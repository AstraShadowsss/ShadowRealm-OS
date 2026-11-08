#!/usr/bin/env python3
"""Build a signed AMD64 APT archive from reviewed ShadowRealm-OS DEBs.

Run on Debian with dpkg-deb and gpg. Output must be a new directory.
Signing keys are supplied explicitly; this tool never generates or uploads one.
"""
import argparse, datetime, email.utils, gzip, hashlib, pathlib, shutil, subprocess

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('packages', type=pathlib.Path)
p.add_argument('output', type=pathlib.Path)
p.add_argument('--signing-key', required=True, help='Full fingerprint of your signing key')
p.add_argument('--gnupg-home', type=pathlib.Path)
p.add_argument('--valid-days', type=int, default=14)
a = p.parse_args()
if not 1 <= a.valid_days <= 90:
    p.error('--valid-days must be between 1 and 90')
files = sorted(a.packages.glob('*.deb'))
if not files:
    p.error('No DEB packages found')
if a.output.exists():
    p.error('Use a new output directory; existing archives are never overwritten')
games = {'shadow-pinball', 'skull-invaders', 'shadow-runner', 'shadow-solitaire',
         'marble-reactor', 'circuit-chase', 'neon-ascent', 'neon-breaker', 'shadow-snake'}
entries = []
seen = set()
for file in files:
    control = subprocess.check_output(['dpkg-deb', '-f', str(file)], text=True).strip()
    fields = dict(line.split(': ', 1) for line in control.splitlines()
                  if ': ' in line and not line.startswith((' ', '\t')))
    name, version, arch = (fields[k] for k in ('Package', 'Version', 'Architecture'))
    if not (name.startswith('shadowrealm-os-') or name in games):
        p.error('Refusing unrelated package: ' + name)
    if arch not in ('all', 'amd64'):
        p.error('Unsupported architecture: ' + arch)
    identity = (name, version, arch)
    if identity in seen:
        p.error('Duplicate package/version/architecture: ' + repr(identity))
    seen.add(identity)
    entries.append((file, control, name))
a.output.mkdir(parents=True)
index = []
for file, control, name in entries:
    relative = pathlib.PurePosixPath('pool/main') / name / file.name
    destination = a.output / str(relative)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(file, destination)
    data = file.read_bytes()
    index.append(control + '\nFilename: ' + str(relative) + '\nSize: ' + str(len(data))
                 + '\nSHA256: ' + hashlib.sha256(data).hexdigest()
                 + '\nSHA512: ' + hashlib.sha512(data).hexdigest() + '\n\n')
suite = a.output / 'dists/trixie'
binary = suite / 'main/binary-amd64'
binary.mkdir(parents=True)
packages = ''.join(index).encode()
(binary / 'Packages').write_bytes(packages)
(binary / 'Packages.gz').write_bytes(gzip.compress(packages, mtime=0))
now = datetime.datetime.now(datetime.timezone.utc)
release = ('Origin: ShadowRealm-OS\nLabel: ShadowRealm-OS\nSuite: trixie\nCodename: trixie\n'
           'Architectures: amd64\nComponents: main\nAcquire-By-Hash: yes\n'
           'Description: ShadowRealm-OS custom Debian 13 packages\n'
           'Date: ' + email.utils.format_datetime(now, usegmt=True) + '\n'
           'Valid-Until: ' + email.utils.format_datetime(now + datetime.timedelta(days=a.valid_days), usegmt=True) + '\n')
for label, algorithm in [('SHA256', 'sha256'), ('SHA512', 'sha512')]:
    release += label + ':\n'
    for file in [binary / 'Packages', binary / 'Packages.gz']:
        data = file.read_bytes()
        digest = hashlib.new(algorithm, data).hexdigest()
        relative = file.relative_to(suite).as_posix()
        release += f' {digest} {len(data)} {relative}\n'
        hashed = binary / 'by-hash' / label / digest
        hashed.parent.mkdir(parents=True, exist_ok=True)
        hashed.write_bytes(data)
(suite / 'Release').write_text(release)
gpg = ['gpg', '--batch']
if a.gnupg_home:
    gpg += ['--homedir', str(a.gnupg_home)]
key = a.signing_key.replace(' ', '')
if len(key) not in (40, 64) or any(c not in '0123456789abcdefABCDEF' for c in key):
    p.error('Use a full signing-key fingerprint')
subprocess.run(gpg + ['--local-user', key, '--digest-algo', 'SHA256', '--output',
                     str(suite / 'InRelease'), '--clearsign', str(suite / 'Release')], check=True)
subprocess.run(gpg + ['--local-user', key, '--digest-algo', 'SHA256', '--armor', '--output',
                     str(suite / 'Release.gpg'), '--detach-sign', str(suite / 'Release')], check=True)
public = subprocess.check_output(gpg + ['--export', key])
if not public:
    raise RuntimeError('Public signing key could not be exported')
(a.output / 'shadowrealm-os-archive-keyring.gpg').write_bytes(public)
print(f'Built signed repository: {len(entries)} packages in {a.output}')

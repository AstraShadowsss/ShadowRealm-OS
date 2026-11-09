#!/usr/bin/env python3
"""Build the public APT setup package. No private signing material is needed."""
import argparse, pathlib, subprocess, tempfile, os
p=argparse.ArgumentParser()
p.add_argument('public_key',type=pathlib.Path)
p.add_argument('output',type=pathlib.Path)
a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
source=pathlib.Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='shadowrealm-archive-keyring-') as td:
 root=pathlib.Path(td)
 def put(name,data,mode=0o644):
  f=root/name;f.parent.mkdir(parents=True,exist_ok=True)
  f.write_bytes(data.encode() if isinstance(data,str) else data);f.chmod(mode)
 put('DEBIAN/control','Package: shadowrealm-os-archive-keyring\nVersion: 2026.11-1\nArchitecture: all\nSection: admin\nPriority: optional\nMaintainer: ShadowRealm-OS Project <packages@shadowrealm-os.invalid>\nDepends: apt (>= 2.6), ca-certificates\nDescription: ShadowRealm-OS signed custom package repository and public key\n')
 put('usr/share/keyrings/shadowrealm-os-archive-keyring.gpg',a.public_key.read_bytes())
 put('etc/apt/sources.list.d/shadowrealm-os.sources','Types: deb\nURIs: https://shadowrealm-os.sourceforge.io/apt\nSuites: trixie\nComponents: main\nArchitectures: amd64\nSigned-By: /usr/share/keyrings/shadowrealm-os-archive-keyring.gpg\n')
 games='shadow-pinball skull-invaders shadow-runner shadow-solitaire marble-reactor circuit-chase neon-ascent neon-breaker shadow-snake'
 put('etc/apt/preferences.d/shadowrealm-os','Package: shadowrealm-os-* '+games+'\nPin: release o=ShadowRealm-OS\nPin-Priority: 700\n\nPackage: *\nPin: release o=ShadowRealm-OS\nPin-Priority: -1\n')
 put('DEBIAN/conffiles','/etc/apt/sources.list.d/shadowrealm-os.sources\n/etc/apt/preferences.d/shadowrealm-os\n')
 put('usr/share/doc/shadowrealm-os-archive-keyring/copyright',(source/'LICENSE').read_bytes())
 env=dict(os.environ);env.setdefault('SOURCE_DATE_EPOCH','1794096000')
 subprocess.run(['dpkg-deb','--root-owner-group','--build',str(root),str(a.output/'shadowrealm-os-archive-keyring_2026.11-1_all.deb')],check=True,env=env)

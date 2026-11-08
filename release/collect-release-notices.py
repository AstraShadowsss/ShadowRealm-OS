#!/usr/bin/python3
"""Collect license files and audit coverage against an exact installed filesystem."""
from pathlib import Path
import argparse,hashlib,json,subprocess,tarfile
p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('output',type=Path);a=p.parse_args();root=a.root.resolve();a.output.mkdir(parents=True,exist_ok=True)
assert (root/'var/lib/dpkg/status').is_file() and root!=Path('/')

def resolved(p):
 q=p.resolve()
 if not q.is_relative_to(root):q=(root/str(q).lstrip('/')).resolve()
 if not q.is_relative_to(root):raise ValueError('License path leaves image: '+str(p))
 return q

raw=subprocess.check_output(['dpkg-query','--admindir='+str(root/'var/lib/dpkg'),'-W','-f=${binary:Package}\t${Version}\t${Architecture}\t${source:Package}\t${source:Version}\t${db:Status-Status}\n'],text=True)
rows=[line.split('\t') for line in raw.splitlines() if line.endswith('\tinstalled')]
supplements={'librewolf':'usr/share/doc/shadowrealm-os-desktop/vendor-notices/LibreWolf-159.0.1-licenses.html','libqt-jami':'usr/share/doc/shadowrealm-os-desktop/vendor-notices/Qt-and-QtWebEngine-license-notices.tar.gz'}
paths={};coverage=[];missing=[]
for name,version,arch,src,sv,state in rows:
 package=name.split(':')[0];rel='usr/share/doc/'+package+'/copyright';kind='Package copyright'
 if not (root/rel).is_file():rel=supplements.get(package,'');kind='Upstream vendor supplement'
 if not rel or not (root/rel).is_file():missing.append(name);continue
 source=resolved(root/rel);paths[rel]=source
 coverage.append([name,version,kind,rel,hashlib.sha256(source.read_bytes()).hexdigest()])
for folder in [root/'usr/share/doc',root/'usr/share/common-licenses']:
 for file in folder.rglob('*'):
  if not file.is_file():continue
  name=file.name.lower();rel=str(file.relative_to(root))
  if folder.name=='common-licenses' or name.startswith(('copyright','license','copying','notice','authors')) or name=='gnome-icon-copyright' or '/vendor-notices/' in rel:
   paths[rel]=resolved(file)
if missing:raise SystemExit('Missing license coverage: '+', '.join(missing))
archive=a.output/'Package-license-notices.tar.gz'
with tarfile.open(archive,'w:gz') as t:
 for rel,source in sorted(paths.items()):
  info=t.gettarinfo(str(source),arcname=rel);info.uid=info.gid=0;info.uname=info.gname='root';info.mode=0o644
  with source.open('rb') as stream:t.addfile(info,stream)
(a.output/'package-license-inventory.tsv').write_text('Package\tVersion\tNotice type\tNotice path\tSHA256\n'+'\n'.join('\t'.join(row) for row in coverage)+'\n')
(a.output/'installed-package-source-versions.tsv').write_text('Package\tVersion\tArchitecture\tSource\tSourceVersion\n'+'\n'.join('\t'.join(row[:5]) for row in rows)+'\n')
(a.output/'license-coverage.json').write_text(json.dumps({'installed_packages':len(rows),'packages_with_notices':len(coverage),'missing_packages':missing,'notice_files':len(paths),'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest()},indent=2)+'\n')
print('PASS',len(coverage),'packages accounted for;',len(paths),'notice files. This verifies file coverage, not legal certification.')

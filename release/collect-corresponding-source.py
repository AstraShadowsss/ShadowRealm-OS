#!/usr/bin/python3
"""Inventory installed packages and matching SHA256-verified Debian source inputs.
Run on Debian with python3-apt and matching trusted deb-src indexes available.
Vendor sources and original ShadowRealm-OS components are supplied separately.
"""
import argparse,json,pathlib,subprocess
import apt_pkg
p=argparse.ArgumentParser();p.add_argument('--root',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args()
apt_pkg.init();root=a.root.resolve();assert (root/'var/lib/dpkg/status').is_file()
custom={'shadowrealm-os-experience','shadowrealm-os-desktop','shadowrealm-os-terminal','shadowrealm-os-panel','shadowrealm-os-security','shadowrealm-os-artwork','shadowrealm-os-release','shadowrealm-os-installer-settings','shadow-pinball','shadow-runner','skull-invaders','circuit-chase','marble-reactor','neon-ascent','neon-breaker','shadow-snake','shadow-solitaire'}
vendors={'librewolf','jami','jami-daemon','libqt-jami'}
fmt='${db:Status-Status}\t${binary:Package}\t${Version}\t${source:Package}\t${source:Version}\n'
raw=subprocess.check_output(['dpkg-query','--admindir='+str(root/'var/lib/dpkg'),'-W','-f='+fmt],text=True)
sources=set();packages=[]
for line in raw.splitlines():
 status,name,version,source,sversion=line.split('\t')
 if status!='installed':continue
 packages.append(dict(package=name,version=version,source=source,source_version=sversion))
 if source not in custom|vendors:sources.add((source,sversion))
files={};missing=[];records=apt_pkg.SourceRecords()
for source,version in sorted(sources):
 records.restart();found=False
 while records.lookup(source):
  if records.version!=version:continue
  if not records.index.is_trusted:raise RuntimeError('Untrusted source index: '+source)
  found=True
  for file in records.files:
   sha=file.hashes.find('SHA256')
   if not sha:raise RuntimeError('Missing SHA256: '+file.path)
   files[file.path]=dict(url=records.index.archive_uri(file.path).replace('http:','https:'),path=file.path,size=file.size,sha256=sha.hashvalue,source=source,version=version)
  break
 if not found:missing.append(dict(source=source,version=version))
data=dict(packages=packages,files=list(files.values()),missing=missing,separate_vendor_sources=sorted(vendors),original_components=sorted(custom))
a.output.write_text(json.dumps(data,indent=2)+'\n')
print('Packages:',len(packages),'Debian sources:',len(sources),'Files:',len(files),'Bytes:',sum(f['size'] for f in files.values()),'Missing:',missing)
if missing:raise SystemExit(1)

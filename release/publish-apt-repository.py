#!/usr/bin/env python3
"""Publish a reviewed, already-signed archive using SFTP (python3-paramiko).

Existing package filenames are immutable. Indexes are replaced atomically,
and InRelease is published last. Retain older by-hash files on the server.
"""
import argparse,pathlib,paramiko,hashlib,urllib.request
p=argparse.ArgumentParser()
p.add_argument('archive',type=pathlib.Path)
p.add_argument('--host',default='web.sourceforge.net')
p.add_argument('--user',required=True)
p.add_argument('--identity',required=True)
p.add_argument('--remote-root',default='/home/project-web/shadowrealm-os/htdocs/apt')
p.add_argument('--public-root',default='https://shadowrealm-os.sourceforge.io/apt')
a=p.parse_args()
assert (a.archive/'dists/trixie/InRelease').is_file()
c=paramiko.SSHClient();c.load_system_host_keys();c.connect(a.host,username=a.user,key_filename=a.identity)
s=c.open_sftp()
def mkdir(path):
 try:s.stat(path)
 except OSError:
  parent=path.rsplit('/',1)[0]
  if parent:mkdir(parent)
  s.mkdir(path)
def digest(stream):
 h=hashlib.sha256()
 for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
 return h.hexdigest()
files=sorted((f for f in a.archive.rglob('*') if f.is_file()),key=lambda f:(f.name=='InRelease',f.name=='Release.gpg',f.name=='Release',not f.relative_to(a.archive).as_posix().startswith('pool/'),str(f)))
for f in files:
 rel=f.relative_to(a.archive).as_posix();remote=a.remote_root+'/'+rel
 mkdir(remote.rsplit('/',1)[0])
 if rel.startswith('pool/'):
  try:existing=s.open(remote,'rb')
  except OSError:existing=None
  if existing:
   existing.close()
   print('Checking immutable package '+rel,flush=True)
   with urllib.request.urlopen(a.public_root+'/'+rel,timeout=30) as published, f.open('rb') as local:
    assert digest(published)==digest(local),'Published package changed under the same filename: '+rel
   continue
 s.put(str(f),remote+'.upload')
 s.posix_rename(remote+'.upload',remote)
 print('Published '+rel,flush=True)
s.close();c.close()

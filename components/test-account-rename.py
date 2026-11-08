#!/usr/bin/python3
"""Destructive disposable-account integration tests. Run ONLY in a build/test VM."""
import importlib.machinery, importlib.util, json, os, pwd, shutil, subprocess, sys
from pathlib import Path
if os.geteuid()!=0 or os.environ.get('SHADOWREALM_OS_DISPOSABLE_TEST')!='1':
 raise SystemExit('Requires root in a disposable VM and SHADOWREALM_OS_DISPOSABLE_TEST=1.')
source=Path(sys.argv[1]).resolve()
loader=importlib.machinery.SourceFileLoader('rename_test_module',str(source))
spec=importlib.util.spec_from_loader(loader.name,loader);m=importlib.util.module_from_spec(spec);loader.exec_module(m)
old,new='shrtestold','shrtestnew'
def command(*args):subprocess.run(args,check=True,stdout=subprocess.DEVNULL)
def cleanup():
 for name in (old,new):
  try:pwd.getpwnam(name)
  except KeyError:continue
  command('userdel','-r',name)
 for name in (old,new):
  subprocess.run(['groupdel',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  home=Path('/home')/name
  if home.exists() and not home.is_symlink():shutil.rmtree(home)
def fixture():
 cleanup();command('useradd','-m','-U','-G','sudo,audio',old)
 u=pwd.getpwnam(old);home=Path(u.pw_dir)
 cfg=home/'.config/shadowrealm-os';cfg.mkdir(parents=True)
 text=cfg/'fixture.json';text.write_text(json.dumps({'home':str(home),'other':str(home)+'-backup'}));text.chmod(0o640)
 link=home/'.local/share/icons';link.mkdir(parents=True)
 (link/'palette').symlink_to(home/'.themes',target_is_directory=True)
 for path in home.rglob('*'):os.lchown(path,u.pw_uid,u.pw_gid)
 req={'uid':u.pw_uid,'gid':u.pw_gid,'old':old,'new':new,'home':str(home),'target':'/home/'+new,'private_group':True,'supplementary_groups':m.local_supplementary_groups(old)}
 return req
try:
 req=fixture();m.apply(req);u=pwd.getpwnam(new)
 assert u.pw_uid==req['uid'] and u.pw_dir=='/home/'+new
 text=Path(u.pw_dir)/'.config/shadowrealm-os/fixture.json'
 data=json.loads(text.read_text());assert data['home']=='/home/'+new and data['other']=='/home/'+old+'-backup'
 assert text.stat().st_mode&0o777==0o640 and text.stat().st_uid==u.pw_uid
 assert os.readlink(Path(u.pw_dir)/'.local/share/icons/palette')=='/home/'+new+'/.themes'
 groups=subprocess.check_output(['id','-nG',new],text=True).split();assert 'sudo' in groups and 'audio' in groups
 command('runuser','-u',new,'--','sh','-c','test "$HOME" = /home/shrtestnew && test -w "$HOME"')
 print('PASS real rename, Home, private group, supplementary groups, permissions, directory symlink and user execution',flush=True)
 req=fixture()
 # Kill immediately after the real usermod transaction, then retry the persisted request.
 script='''import importlib.machinery, importlib.util, os, signal, json, sys
l=importlib.machinery.SourceFileLoader('r',sys.argv[1]);s=importlib.util.spec_from_loader('r',l);m=importlib.util.module_from_spec(s);l.exec_module(m)
original=m.command
def crash(*args):
 original(*args)
 if args[0]=='/usr/sbin/usermod':os.kill(os.getpid(),signal.SIGKILL)
m.command=crash;m.apply(json.loads(sys.argv[2]))
'''
 result=subprocess.run([sys.executable,'-c',script,str(source),json.dumps(req)])
 assert result.returncode==-9;m.apply(req)
 assert pwd.getpwnam(new).pw_dir=='/home/'+new
 print('PASS retry after actual process termination following usermod',flush=True)
 req=fixture();command('usermod','-l',new,'-d','/home/'+new,old);m.apply(req)
 assert Path('/home/'+new).is_dir() and not Path('/home/'+old).exists()
 print('PASS interrupted metadata change before Home move',flush=True)
 req=fixture();Path('/home/'+old).rename('/home/'+new);m.apply(req)
 assert pwd.getpwnam(new).pw_dir=='/home/'+new
 print('PASS interrupted Home move before metadata change',flush=True)
 req=fixture();original=m.command
 def fail_reload(*args):
  if args==('/usr/bin/systemctl','daemon-reload'):raise RuntimeError('injected test failure')
  return original(*args)
 m.command=fail_reload
 try:m.apply(req)
 except RuntimeError:pass
 else:raise AssertionError('Expected rollback')
 m.command=original
 assert pwd.getpwnam(old).pw_dir=='/home/'+old and Path('/home/'+old).is_dir()
 assert json.loads((Path('/home/'+old)/'.config/shadowrealm-os/fixture.json').read_text())['home']=='/home/'+old
 assert {'sudo','audio'} <= set(subprocess.check_output(['id','-nG',old],text=True).split())
 print('PASS real account/configuration/group rollback after injected downstream failure',flush=True)
 req=fixture();command('useradd','-M','-g',old,'shrtestpeer')
 try:
  req['private_group']=m.private_group(pwd.getpwnam(old));assert not req['private_group']
  m.apply(req)
  import grp
  assert grp.getgrnam(old).gr_gid==req['gid'] and pwd.getpwnam(new).pw_gid==req['gid'] and pwd.getpwnam('shrtestpeer').pw_gid==req['gid']
  print('PASS shared primary group retained for both users',flush=True)
 finally:command('userdel','shrtestpeer')
finally:cleanup()

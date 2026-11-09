#!/usr/bin/python3
"""Synchronize shared branding from a fixed palette selected by the active desktop.
Unprivileged files supply only a whitelisted palette name, never an asset path.
"""
import fcntl, hashlib, json, os, pathlib, pwd, stat, subprocess, tempfile
P=pathlib.Path
PALETTES={'neon':('Neon','ShadowRealm-OS-Neon'),'white-silver-gold':('WhiteSilverGold','ShadowRealm-OS-White-Silver-Gold'),'red-black':('RedBlack','ShadowRealm-OS-RedBlack'),'woodland':('Woodland','ShadowRealm-OS-Woodland'),'hacker':('Hacker','ShadowRealm-OS-Hacker'),'black-blue':('BlackBlue','ShadowRealm-OS-BlackBlue'),'black-white':('BlackWhite','ShadowRealm-OS-BlackWhite'),'professional':('Professional','ShadowRealm-OS-Professional')}
def output(*args):return subprocess.check_output(args,text=True,timeout=10).strip()
def active_palette():
 sid=output('loginctl','show-seat','seat0','-p','ActiveSession','--value')
 if not sid:return None
 fields=dict(line.split('=',1) for line in output('loginctl','show-session',sid,'-p','User','-p','Class','-p','Remote').splitlines() if '=' in line)
 if fields.get('Class')!='user' or fields.get('Remote')!='no':return None
 uid=int(fields.get('User','0'))
 if uid<1000:return None
 home=P(pwd.getpwuid(uid).pw_dir)
 if home.parent!=P('/home') or home.is_symlink():return None
 path=home
 for part in ('.config','shadowrealm-os','appearance-mode'):
  path=path/part
  st=path.lstat()
  if stat.S_ISLNK(st.st_mode) or st.st_uid!=uid:return None
 if path.stat().st_size>64:return None
 mode=path.read_text().strip()
 return mode if mode in PALETTES else None

def approved(path):
 st=path.lstat()
 if not stat.S_ISREG(st.st_mode) or st.st_uid!=0 or st.st_mode&0o022:
  raise RuntimeError('Branding input must be an approved root-owned regular file.')
 return path.read_bytes()
def atomic(path,data):
 path.parent.mkdir(parents=True,exist_ok=True)
 fd,name=tempfile.mkstemp(prefix='.shadow-brand-',dir=path.parent)
 try:
  with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
  os.chmod(name,0o644);os.replace(name,path)
 finally:
  if os.path.lexists(name):os.unlink(name)
def main():
 if os.geteuid()!=0:raise SystemExit('Administrator service only.')
 with open('/run/lock/shadowrealm-os-branding.lock','w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  try:mode=active_palette()
  except (OSError,ValueError,subprocess.SubprocessError):return
  if mode is None:return
  name,theme=PALETTES[mode]
  logo=approved(P('/usr/share/shadowrealm-os/branding')/('ShadowRealm-OS-Circular-'+name+'.png'))
  wall=P('/usr/share/backgrounds/shadowrealm-os/logo-focused')/('ShadowRealm-OS-'+name+'.png')
  image=approved(wall)
  state=P('/var/lib/shadowrealm-os/branding.json')
  signature={'palette':mode,'logo':hashlib.sha256(logo).hexdigest(),'background':hashlib.sha256(image).hexdigest()}
  if state.exists() and json.loads(state.read_text())==signature:return
  for target in ('/usr/share/pixmaps/shadowrealm-os-logo.png','/usr/share/plymouth/themes/shadowrealm-os/logo.png'):
   atomic(P(target),logo)
  if P('/boot/grub').is_dir():atomic(P('/boot/grub/shadowrealm-os-background.png'),image)
  text=f'[greeter]\nbackground={wall}\nuser-background=false\ntheme-name={theme}\nicon-theme-name={theme}\n'
  atomic(P('/etc/lightdm/lightdm-gtk-greeter.conf.d/91-shadowrealm-os-artwork.conf'),text.encode())
  # Rebuild once per change so encrypted early boot receives the selected logo.
  if list(P('/boot').glob('initrd.img-*')):subprocess.run(['update-initramfs','-u','-k','all'],check=True,timeout=300)
  atomic(state,(json.dumps(signature)+'\n').encode())
if __name__=='__main__':main()

from pathlib import Path
import os,json,subprocess,time,tempfile,shutil
import gi
gi.require_version('Gtk','3.0');gi.require_version('GdkX11','3.0')
from gi.repository import Gtk,Gdk,GdkX11
Gtk.init([])
factory=Path.home()/'.local/share/shadow-link/appearance-modes.json';records=json.loads(factory.read_text())
root=Path(tempfile.mkdtemp(prefix='sr-messenger-visual-',dir='/var/tmp'));config=root/'.config/shadowrealm-os';config.mkdir(parents=True);base=root/'.local/share/shadow-link';base.mkdir(parents=True);shutil.copy2(factory,base/'appearance-modes.json');(config/'appearance-mode').write_text('neon')
binary=Path.home()/'.local/lib/shadow-messenger-development/shadow-messenger';env=os.environ.copy();env['HOME']=str(root);env['XDG_DATA_HOME']=str(root/'.local/share');env['XDG_CONFIG_HOME']=str(root/'.config')
before={line.split()[0] for line in subprocess.check_output(['wmctrl','-lp'],text=True).splitlines()}
log=(root/'application.log').open('w');process=subprocess.Popen(['dbus-run-session','--',str(binary)],env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True)
window=None
try:
 for _ in range(100):
  for line in subprocess.check_output(['wmctrl','-lp'],text=True).splitlines():
   parts=line.split(None,4)
   if len(parts)==5 and parts[0] not in before and 'Shadow Messenger' in parts[4]:
    status=Path('/proc/'+parts[2]+'/status').read_text();parent=next(line.split()[1] for line in status.splitlines() if line.startswith('PPid:'))
    if parent==str(process.pid):window=parts[0]
  if window:break
  time.sleep(.1)
 assert window,'Palette test window missing'
 subprocess.run(['wmctrl','-ir',window,'-e','0,40,65,900,600'],check=True);time.sleep(.5)
 for key,record in records.items():
  temp=config/'appearance-mode.new';temp.write_text(key);temp.replace(config/'appearance-mode');time.sleep(.5)
  native=GdkX11.X11Window.foreign_new_for_display(Gdk.Display.get_default(),int(window,16));image=Gdk.pixbuf_get_from_window(native,0,0,native.get_width(),native.get_height());assert image
  # Check a free content area, beyond the connection sidebar and action rows.
  x=image.get_width()-80;y=image.get_height()-60;offset=y*image.get_rowstride()+x*image.get_n_channels();actual=tuple(image.get_pixels()[offset:offset+3]);expected=tuple(bytes.fromhex(record['background'][1:]));assert actual==expected,(key,actual,expected)
  image.savev(str(root/(key+'.png')),'png',[],[]);print('PASS live palette',key,flush=True)
finally:
 if window:subprocess.run(['wmctrl','-ic',window])
 try:process.wait(timeout=10)
 except subprocess.TimeoutExpired:process.terminate();process.wait(timeout=5)
 log.close()
print('CAPTURES',root)

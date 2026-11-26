"""Conservative migration of exact old factory icon files to the new assets."""
import hashlib,json,os,tempfile,subprocess,shutil
from pathlib import Path

def sha(data):return hashlib.sha256(data).hexdigest()
def atomic(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent,delete=False) as f:
        tmp=Path(f.name);f.write(data);os.fchmod(f.fileno(),0o644)
    try:os.replace(tmp,path)
    finally:tmp.unlink(missing_ok=True)

def migrate_icons(home,payload,system_share):
    home=Path(home).resolve();state=home/'.local/state/shadowrealm-os/icon-factory-v1';marker=state/'complete.json'
    if marker.is_file():return
    if not state.parent.resolve().is_relative_to(home):raise RuntimeError('Unsafe migration state')
    manifest=json.loads((payload/'icon-factory-migration.json').read_text());updated=0;preserved=[];refresh=set()
    for item in manifest:
        rel=Path(item['path']);parts=rel.parts
        if rel.is_absolute() or '..' in parts:raise RuntimeError('Unsafe migration manifest')
        if parts[:3]==('usr','share','icons'):
            src=system_share/Path(*parts[2:]);dest=home/'.local/share/icons'/Path(*parts[3:])
        elif parts[:6]==('usr','share','shadowrealm-os','desktop','runtime','icons'):
            src=payload/Path(*parts[4:]);dest=home/'.local/share/shadow-link/icons'/Path(*parts[6:])
        else:raise RuntimeError('Unexpected icon path: '+str(rel))
        if not src.is_file() or src.is_symlink():raise RuntimeError('Missing new factory icon: '+str(src))
        data=src.read_bytes()
        if sha(data)!=item['new']:raise RuntimeError('New factory icon hash mismatch: '+str(src))
        if not dest.parent.resolve().is_relative_to(home) or dest.is_symlink():preserved.append(str(dest));continue
        if dest.is_file():
            old=dest.read_bytes();old_hash=sha(old)
            if old_hash==item['new']:continue
            if old_hash!=item['old']:preserved.append(str(dest.relative_to(home)));continue
            backup=state/'original'/dest.relative_to(home)
            if not backup.exists():atomic(backup,old)
        elif os.path.lexists(dest):preserved.append(str(dest));continue
        atomic(dest,data);updated+=1
        if parts[:3]==('usr','share','icons'):refresh.add(home/'.local/share/icons'/parts[3])
    if shutil.which('gtk-update-icon-cache'):
        for root in sorted(refresh):
            if (root/'index.theme').is_file():subprocess.run(['gtk-update-icon-cache','-f','-t',str(root)],check=True,stdout=subprocess.DEVNULL)
    atomic(marker,(json.dumps({'updated':updated,'preserved':preserved},indent=2)+'\n').encode())

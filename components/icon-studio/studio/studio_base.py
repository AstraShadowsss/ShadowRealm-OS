#!/usr/bin/python3
"""Shadow Icon Studio: GTK3 front end for the installed ShadowRealm renderer."""
from pathlib import Path
from datetime import datetime
import fcntl, json, os, re, subprocess, sys, tempfile, threading
import gi
gi.require_version('Gtk','3.0')
from gi.repository import Gtk, Gio, GdkPixbuf, GLib
H=Path.home()
ENGINE=Path(__file__).resolve().parent.parent/'engine'
sys.path.insert(0,str(ENGINE))
import rebuild as r

class Studio(Gtk.Window):
    def __init__(self):
        super().__init__(title='Shadow Icon Studio')
        self.set_default_size(760,580); self.set_border_width(18)
        self.connect('destroy',Gtk.main_quit)
        self.modes=json.loads((r.B/'appearance-modes.json').read_text())
        if len(self.modes)!=12: raise RuntimeError('Expected 12 appearance modes')
        self.logo=None; self.busy=False; self.apps={}
        box=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=12);self.add(box)
        h=Gtk.Label();h.set_markup('<span size="x-large" weight="bold">Shadow Icon Studio</span>');h.set_xalign(0);box.pack_start(h,False,False,0)
        intro=Gtk.Label(label='Create matching icons for every ShadowRealm theme. Original logo colors are preserved.');intro.set_xalign(0);intro.set_line_wrap(True);box.pack_start(intro,False,False,0)
        grid=Gtk.Grid(column_spacing=12,row_spacing=9);box.pack_start(grid,False,False,0)
        self.chooser=Gtk.FileChooserButton(title='Choose original logo',action=Gtk.FileChooserAction.OPEN)
        filt=Gtk.FileFilter();filt.set_name('Images (PNG, JPEG, SVG, WebP)');[filt.add_pattern('*.'+ext) for ext in ('png','PNG','jpg','jpeg','svg','SVG','webp')];self.chooser.add_filter(filt);self.chooser.connect('file-set',self.load_logo)
        self.app=Gtk.ComboBoxText();self.app.set_hexpand(True);self.app.append('', 'Export only — do not change an application');self.app.set_active(0)
        for a in sorted(Gio.AppInfo.get_all(),key=lambda a:(a.get_name() or '').casefold()):
            if not isinstance(a,Gio.DesktopAppInfo) or not a.should_show():continue
            id=a.get_id(); path=a.get_filename()
            if not id or not path or not r.valid(id):continue
            f=r.read_fields(Path(path))
            if r.role_of(f,id) or r.game(f,id) or id=='shadowrealm-icon-studio.desktop':continue
            self.apps[id]=a;self.app.append(id,f'{a.get_name()} — {id}')
        self.app.connect('changed',self.update_controls)
        self.palette=Gtk.ComboBoxText()
        for mid,mode in self.modes.items():self.palette.append(mid,mode['icons'].removeprefix('ShadowRealm-OS-'))
        try:active=(H/'.config/shadowrealm-os/appearance-mode').read_text().strip()
        except OSError:active='neon'
        if not self.palette.set_active_id(active):self.palette.set_active(0)
        self.palette.connect('changed',lambda *_:self.preview())
        for n,(name,w) in enumerate((('Original logo',self.chooser),('Application',self.app),('Preview palette',self.palette))):
            label=Gtk.Label(label=name);label.set_xalign(0);grid.attach(label,0,n,1,1);grid.attach(w,1,n,1,1)
        self.image=Gtk.Image();self.image.set_pixel_size(192);preview=Gtk.Frame(label='Preview');preview.add(self.image);box.pack_start(preview,True,True,0)
        buttons=Gtk.Box(spacing=8);box.pack_start(buttons,False,False,0)
        self.export=Gtk.Button(label='Export all 12 themes');self.export.connect('clicked',self.export_all);buttons.pack_start(self.export,True,True,0)
        self.apply=Gtk.Button(label='Apply to selected app');self.apply.connect('clicked',lambda *_:self.change_custom(False));buttons.pack_start(self.apply,True,True,0)
        self.reset=Gtk.Button(label='Restore original logo');self.reset.connect('clicked',lambda *_:self.change_custom(True));buttons.pack_start(self.reset,True,True,0)
        self.refresh=Gtk.Button(label='Scan for newly installed apps');self.refresh.connect('clicked',lambda *_:self.run_task(None,False));box.pack_start(self.refresh,False,False,0)
        self.status=Gtk.Label(label='Choose a logo to begin. Games and system status icons are protected.');self.status.set_xalign(0);self.status.set_line_wrap(True);self.status.set_selectable(True);box.pack_start(self.status,False,False,0)
        self.update_controls()
    def update_controls(self,*_):
        selected=bool(self.app.get_active_id())
        self.export.set_sensitive(not self.busy and self.logo is not None)
        self.apply.set_sensitive(not self.busy and selected and self.logo is not None)
        self.reset.set_sensitive(not self.busy and selected and (r.STATE/'custom-logos'/(self.app.get_active_id()+'.png')).is_file())
        self.refresh.set_sensitive(not self.busy);self.chooser.set_sensitive(not self.busy);self.app.set_sensitive(not self.busy)
    def load_logo(self,*_):
        try:
            p=Path(self.chooser.get_filename())
            if p.stat().st_size>16*1024*1024:raise ValueError('Choose an image smaller than 16 MB.')
            pb=GdkPixbuf.Pixbuf.new_from_file_at_scale(str(p),256,256,True)
            self.logo=r.art_png(bytes(pb.save_to_bufferv('png',[],[])[1]));self.preview();self.status.set_text('Logo ready. Export or apply to an installed application.')
        except Exception as e:self.logo=None;self.image.clear();self.status.set_text(str(e))
        self.update_controls()
    def preview(self):
        if not self.logo:return
        try:
            data=r.icon(self.modes[self.palette.get_active_id()],logo=self.logo)
            loader=GdkPixbuf.PixbufLoader.new_with_type('svg');loader.set_size(192,192);loader.write(data);loader.close();self.image.set_from_pixbuf(loader.get_pixbuf())
        except Exception as e:self.status.set_text(str(e))
    def export_all(self,*_):
        dialog=Gtk.FileChooserDialog(title='Choose export folder',parent=self,action=Gtk.FileChooserAction.SELECT_FOLDER)
        dialog.add_buttons('Cancel',Gtk.ResponseType.CANCEL,'Export',Gtk.ResponseType.OK)
        try:
            if dialog.run()!=Gtk.ResponseType.OK:return
            root=Path(dialog.get_filename())/('ShadowRealm-Icons-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f'));root.mkdir()
            for mode in self.modes.values():
                d=root/mode['icons'];d.mkdir();svg=r.icon(mode,logo=self.logo);(d/'icon.svg').write_bytes(svg)
                for size in r.SIZES:(d/f'icon-{size}.png').write_bytes(r.raster(svg,size))
            self.status.set_text(f'Exported 12 SVG masters and 96 PNGs to {root}')
        except Exception as e:self.status.set_text(f'Export incomplete: {e}')
        finally:dialog.destroy()
    def change_custom(self,reset):
        id=self.app.get_active_id()
        if not id or id not in self.apps:return
        if reset or self.logo:
            self.run_task(id,reset)
    def run_task(self,id,reset):
        if self.busy:return
        self.busy=True;self.update_controls();self.status.set_text('Updating icons. The existing catalog is not rebuilt.')
        logo=self.logo
        def work():
            backup=None;target=None;previous=None
            try:
                if id:
                    # Same lock as the background service, to avoid concurrent file writes.
                    with (r.STATE/'lock').open('a') as lock:
                        fcntl.flock(lock,fcntl.LOCK_EX)
                        target=r.STATE/'custom-logos'/(id+'.png');target.parent.mkdir(parents=True,exist_ok=True)
                        previous=target.read_bytes() if target.is_file() else None
                        backup=H/'shadowrealm-checkpoints'/('icon-studio-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f'));backup.mkdir(parents=True)
                        (backup/'application-id.txt').write_text(id+'\n')
                        if previous is not None:(backup/'previous-logo.png').write_bytes(previous)
                        if reset:target.unlink(missing_ok=True)
                        else:
                            with tempfile.NamedTemporaryFile(dir=target.parent,delete=False) as f:f.write(logo);tmp=f.name
                            os.replace(tmp,target)
                # Refuse refresh if incremental state is missing.
                previous_state=json.loads((r.STATE/'installed.json').read_text())
                if not previous_state.get('fingerprint') or not isinstance(previous_state.get('per_app'),dict):
                    raise RuntimeError('Incremental engine state missing. No rebuild started.')
                result=subprocess.run([sys.executable,str(ENGINE/'rebuild.py'),'--refresh'],capture_output=True,text=True,timeout=240)
                if result.returncode:raise RuntimeError((result.stderr or result.stdout or 'Icon engine failed').strip()[-1200:])
                if id and not reset:
                    for mode in self.modes.values():
                        expected=r.icon(mode,logo=logo)
                        file=r.U/mode['icons']/'scalable/apps'/(r.key(id)+'.svg')
                        if not file.is_file() or file.read_bytes()!=expected:raise RuntimeError('Icon was not verified in '+mode['icons'])
                if id:r.refresh_panel()
                message=('Custom override removed; original artwork refresh requested.' if reset else 'Custom icon applied across all 12 themes.') if id else 'Application scan finished. '+result.stdout.strip()[-500:]
            except Exception as e:
                # Keep the saved request so the user can retry or restore; report honestly.
                message='Update not verified: '+str(e)+(f'\nSaved request; recovery folder: {backup}' if backup else '')
            GLib.idle_add(self.finish,message)
        threading.Thread(target=work,daemon=True).start()
    def finish(self,message):
        self.busy=False;self.status.set_text(message);self.update_controls();return False

if __name__=='__main__':
    win=Studio();win.show_all();Gtk.main()

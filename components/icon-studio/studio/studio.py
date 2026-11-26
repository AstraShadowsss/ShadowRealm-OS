#!/usr/bin/python3
"""Shadow Icon Studio 2.3 — development front end over the verified v3 engine."""
from studio_base import Studio, r, H, ENGINE, Gtk, Gio, GdkPixbuf, GLib
from gi.repository import Gdk, Pango
from PIL import Image, ImageOps
from io import BytesIO
from pathlib import Path
from datetime import datetime
import base64, fcntl, json, os, re, subprocess, sys, tempfile, threading, uuid, zipfile

GUIDE = """GET STARTED
Choose an image for your new icon, or click Try sample to load Prism. The image goes inside the themed frame. Select an installed application only if you want to change its icon. To reuse that application's own artwork, select it and click Use app’s original artwork. Optional tint changes only the artwork. All 12 previews update automatically.

THREE WAYS TO USE YOUR ICON
Apply: changes the selected app’s icon in all twelve palettes. You do not need to export or manage system files. Confirm the application name before applying. The program does not change the app itself.
Save to My Icons: keeps a named creation in your personal library. You can use it again later, even if no application is installed yet. No app is changed. Open My Icons, choose a creation and click Use selected icon to load it in Create. Rename or remove saved creations there. Removing a saved creation does not undo any already applied icons. Saved artwork includes any tint you applied; turn off tint before saving if you want the original colors.
Export: saves standalone files for sharing or use outside Icon Studio. No app is changed. The destination is shown on Create; by default it is Documents/ShadowRealm Icons (Home fallback). A new timestamped folder contains 12 SVGs and 96 PNGs (16, 24, 32, 48, 64, 96, 128 and 256 px). Open export folder takes you straight there. The last destination and successful export are remembered. The SVG frame is vector; imported raster artwork remains raster.

FIND AND RESTORE APPLICATIONS
Search by name or desktop ID. Select a visible result; the chosen name appears above the Apply button. Clear the selection for library-only or export-only work. New apps are discovered when installed, when Studio opens or when you click Scan for new apps. Protected system utilities and individual games are intentionally omitted. Restore app icon removes a manual override and returns to the default themed artwork. Your applied overrides survive automatic scans. The user timer checks for newly installed apps periodically. Missing original logos are reported. No internet or administrator permissions are required for local creation, scans or export.

ADVANCED TOOLS
Batch export generates all twelve palettes for each chosen image in the same export destination. Custom packs are ZIPs of applied app overrides, not the My Icons library. Import only applies to eligible installed apps and asks before replacing existing overrides. Restore all removes eligible overrides, not saved creations. Only share artwork you have permission to redistribute.

TROUBLESHOOTING
Read the status bar at the bottom of the window. If an app is missing, scan and search again. If a menu icon has not refreshed, reopen the menu. Keep system icon folders intact. A failed operation reports the reason and any recovery backup. My Icons and export settings are personal and are not included in factory release assets."""

# Original, neutral Prism demonstration art; no external files or network needed.
SAMPLE = base64.b64decode('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')

class IconLibrary:
    """Independent named creations, one atomically written record per icon."""
    def __init__(self,root):
        self.root=Path(root)
    @staticmethod
    def name(value):
        value=value.strip()
        if not value or len(value)>80 or any(ord(c)<32 for c in value):
            raise ValueError('Enter a name of 1–80 characters without control characters.')
        return value
    def path(self,ident):
        if not re.fullmatch(r'[0-9a-f]{32}',ident):raise ValueError('Invalid saved icon ID.')
        return self.root/(ident+'.json')
    def read(self,ident):
        p=self.path(ident)
        if p.is_symlink() or not p.is_file() or p.stat().st_size>1024*1024:raise ValueError('Invalid saved icon file.')
        rec=json.loads(p.read_text());name=self.name(rec['name'])
        if rec.get('version')!=1:raise ValueError('Unsupported saved icon version.')
        art=base64.b64decode(rec['png'],validate=True)
        with Image.open(BytesIO(art)) as im:
            if im.format!='PNG' or max(im.size)>256:raise ValueError('Invalid saved artwork.')
            im.verify()
        return name,art
    def entries(self):
        rows=[];bad=0
        for p in self.root.glob('*.json'):
            try:
                name,art=self.read(p.stem);rows.append((p.stem,name,art))
            except Exception:bad+=1
        return sorted(rows,key=lambda x:(x[1].casefold(),x[0])),bad
    def write(self,ident,name,art):
        name=self.name(name)
        with Image.open(BytesIO(art)) as im:
            if im.format!='PNG' or max(im.size)>256:raise ValueError('Invalid saved artwork.')
            im.verify()
        atomic(self.path(ident),json.dumps({'version':1,'name':name,'png':base64.b64encode(art).decode('ascii')},ensure_ascii=False).encode('utf-8'))
    def save(self,name,art):
        ident=uuid.uuid4().hex;self.write(ident,name,art);return ident
    def rename(self,ident,name):
        _,art=self.read(ident);self.write(ident,name,art)
    def remove(self,ident):
        self.read(ident);self.path(ident).unlink()


def png_from_file(p):
    p=Path(p)
    if not p.is_file() or p.stat().st_size>16*1024*1024:raise ValueError('Choose a local image smaller than 16 MB.')
    pb=GdkPixbuf.Pixbuf.new_from_file_at_scale(str(p),256,256,True)
    return r.art_png(bytes(pb.save_to_bufferv('png',[],[])[1]))

def atomic(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent,delete=False) as f:f.write(data);tmp=Path(f.name)
    try:os.replace(tmp,path)
    finally:tmp.unlink(missing_ok=True)

def pix(svg,n):
    loader=GdkPixbuf.PixbufLoader.new_with_type('svg');loader.set_size(n,n);loader.write(svg);loader.close();return loader.get_pixbuf()

class ApplicationList(Gtk.ScrolledWindow):
    """Visible selection list; no selection means export only."""
    def __init__(self):
        super().__init__()
        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.set_shadow_type(Gtk.ShadowType.IN)
        self.set_min_content_height(145)
        self.set_size_request(-1,145)
        self.set_hexpand(True)
        self.model=Gtk.ListStore(str,str)
        self.tree=Gtk.TreeView(model=self.model)
        self.tree.set_headers_visible(False)
        self.tree.set_enable_search(False)
        self.tree.set_activate_on_single_click(False)
        cell=Gtk.CellRendererText(ellipsize=Pango.EllipsizeMode.END)
        column=Gtk.TreeViewColumn('Application',cell,text=1)
        column.set_expand(True)
        self.tree.append_column(column)
        self.selection=self.tree.get_selection()
        self.selection.set_mode(Gtk.SelectionMode.SINGLE)
        self.add(self.tree)
    def get_active_id(self):
        model,it=self.selection.get_selected()
        return model.get_value(it,0) if it is not None else None
    def set_active_id(self,aid):
        for row in self.model:
            if row[0]==aid:
                self.selection.select_iter(row.iter)
                self.tree.scroll_to_cell(row.path,None,False,0,0)
                return True
        return False
    def set_active(self,index):
        self.selection.select_path(Gtk.TreePath.new_from_indices([index]))
    def append(self,aid,label):
        self.model.append([aid,label])
    def remove_all(self):
        self.model.clear()


def matching_apps(apps,query):
    tokens=query.casefold().split()
    return [(aid,a) for aid,a in apps.items()
            if all(t in ((a.get_name() or '')+' '+aid).casefold() for t in tokens)]

class Studio2(Studio):
    def __init__(self):
        # Build a fresh GTK layout; reuse only the verified engine-facing methods.
        Gtk.Window.__init__(self,title='Shadow Icon Studio')
        self.set_default_size(1040,760);self.set_border_width(10)
        self.set_icon_name('orbital-dock-image-viewer');self.connect('destroy',Gtk.main_quit)
        self.modes=json.loads((r.B/'appearance-modes.json').read_text())
        if len(self.modes)!=12:raise RuntimeError('Expected 12 appearance modes')
        self.logo=None;self.raw=None;self.busy=False;self.apps={};self.last_export=None;self.searching=False;self.source_name='icon'
        documents=GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOCUMENTS)
        self.export_dest=(Path(documents) if documents and Path(documents).is_dir() else H)/'ShadowRealm Icons'
        self.library=IconLibrary(Path(GLib.get_user_data_dir())/'shadowrealm-icon-studio'/'library');self.library_thumbs={}
        self.settings=Path(GLib.get_user_config_dir())/'shadowrealm-icon-studio'/'preferences.json'
        try:
            prefs=json.loads(self.settings.read_text())
            dest=Path(prefs.get('destination',''));last=Path(prefs.get('last_export',''))
            if dest.is_absolute():self.export_dest=dest
            if last.is_absolute() and last.is_dir():self.last_export=last
        except (OSError,ValueError,TypeError,AttributeError):pass
        outer=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=6);self.add(outer)
        tabs=Gtk.Notebook();self.tabs=tabs;outer.pack_start(tabs,True,True,0)
        page=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=6);tabs.append_page(page,Gtk.Label(label='Create'))
        scroll=Gtk.ScrolledWindow();scroll.set_policy(Gtk.PolicyType.AUTOMATIC,Gtk.PolicyType.AUTOMATIC);page.pack_start(scroll,True,True,0)
        create=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=12);create.set_border_width(14);scroll.add(create)
        def label(text,sub=False):
            w=Gtk.Label(label=text,xalign=0,wrap=True);w.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR);w.set_max_width_chars(48)
            if sub:w.get_style_context().add_class('dim-label')
            return w
        def heading(text):
            w=Gtk.Label(xalign=0);w.set_markup('<b>'+GLib.markup_escape_text(text)+'</b>');return w
        def button(text,cb):
            w=Gtk.Button(label=text);w.connect('clicked',cb);return w
        create.pack_start(heading('Create a themed icon'),False,False,0)
        create.pack_start(label('Choose artwork, preview all themes, then apply, save for later, or export.',True),False,False,0)
        columns=Gtk.Box(spacing=18);create.pack_start(columns,True,True,0)
        left=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=8);left.set_size_request(300,-1);columns.pack_start(left,True,True,0)
        right=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=8);columns.pack_start(right,True,True,0)
        left.pack_start(heading('1. Choose artwork'),False,False,0)
        left.pack_start(label('Select the image that will appear inside the new icon. You can also drop a file here.',True),False,False,0)
        self.chooser=Gtk.FileChooserButton(title='Choose artwork for your new icon',action=Gtk.FileChooserAction.OPEN)
        filt=Gtk.FileFilter();filt.set_name('Images (PNG, JPEG, SVG, WebP)')
        for ext in ('png','jpg','jpeg','svg','webp'):
            filt.add_pattern('*.'+ext);filt.add_pattern('*.'+ext.upper())
        self.chooser.add_filter(filt);self.chooser.connect('file-set',self.load_logo);left.pack_start(self.chooser,False,False,0)
        self.sample=button('Try sample (Prism)',self.load_sample);left.pack_start(self.sample,False,False,0)
        self.source_status=label('No artwork loaded',True);left.pack_start(self.source_status,False,False,0)
        tintbox=Gtk.Box(spacing=8);self.tint=Gtk.CheckButton(label='Tint artwork (optional)');self.color=Gtk.ColorButton();rgba=Gdk.RGBA();rgba.parse('#00e5ff');self.color.set_rgba(rgba);tintbox.pack_start(self.tint,False,False,0);tintbox.pack_start(self.color,False,False,0);left.pack_start(tintbox,False,False,0);self.tint.connect('toggled',lambda *_:self.recolor());self.color.connect('color-set',lambda *_:self.recolor())
        left.pack_start(Gtk.Separator(),False,False,4)
        left.pack_start(heading('2. Choose an application (optional)'),False,False,0)
        left.pack_start(label('Select an app to replace its icon. Skip this step to save a creation or export files.',True),False,False,0)
        self.search=Gtk.SearchEntry();self.search.set_placeholder_text('Search installed apps');self.search.connect('changed',lambda *_:self.filter_apps());left.pack_start(self.search,False,False,0)
        self.app=ApplicationList();left.pack_start(self.app,True,True,0)
        self.match_count=label('',True);left.pack_start(self.match_count,False,False,0)
        selection=Gtk.Frame(label='Selected application');sel=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=4);sel.set_border_width(8);selection.add(sel);left.pack_start(selection,False,False,0)
        self.selection_name=heading('No application selected');self.selection_name.set_line_wrap(True);sel.pack_start(self.selection_name,False,False,0)
        self.selection_detail=label('No app will be changed when saving or exporting.',True);sel.pack_start(self.selection_detail,False,False,0)
        self.clear_app=button('Clear selection',lambda *_:self.app.selection.unselect_all());sel.pack_start(self.clear_app,False,False,0)
        self.use_original=button('Use selected app’s original artwork',self.original_logo);left.pack_start(self.use_original,False,False,0)
        self.app.selection.connect('changed',self.selection_changed)
        right.pack_start(heading('3. Preview all 12 themes'),False,False,0)
        right.pack_start(label('The border follows your desktop palette. Artwork keeps its colors unless tinting is enabled.',True),False,False,0)
        self.thumbs={};mini=Gtk.Grid(column_spacing=8,row_spacing=8,column_homogeneous=True)
        for j,(mid,mode) in enumerate(self.modes.items()):
            item=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=3);im=Gtk.Image();im.set_size_request(84,84);self.thumbs[mid]=im;item.pack_start(im,False,False,0);caption=Gtk.Label(label=mode.get('label') or mode['icons'].removeprefix('ShadowRealm-OS-'));caption.set_line_wrap(True);caption.set_max_width_chars(14);item.pack_start(caption,False,False,0);mini.attach(item,j%4,j//4,1,1)
        preview=Gtk.Frame();mini.set_border_width(8);preview.add(mini);right.pack_start(preview,False,False,0)
        right.pack_start(heading('4. Use your icon'),False,False,0)
        self.apply=button('Apply to selected app',lambda *_:self.change_custom(False));self.apply.get_style_context().add_class('suggested-action');right.pack_start(self.apply,False,False,0)
        self.reset=button('Restore app’s original icon',lambda *_:self.change_custom(True));right.pack_start(self.reset,False,False,0)
        right.pack_start(Gtk.Separator(),False,False,2)
        self.save_library=button('Save to My Icons',self.save_creation);right.pack_start(self.save_library,False,False,0)
        right.pack_start(label('Keep a named creation for later. No application changes.',True),False,False,0)
        right.pack_start(Gtk.Separator(),False,False,2)
        right.pack_start(label('Export standalone files for use outside Icon Studio.',True),False,False,0)
        right.pack_start(heading('Export location'),False,False,0)
        self.dest_label=label(str(self.export_dest));self.dest_label.set_selectable(True);right.pack_start(self.dest_label,False,False,0)
        self.change_dest=button('Change export folder…',self.select_destination);right.pack_start(self.change_dest,False,False,0)
        self.export=button('Export icon files (12 themes)',self.export_all);right.pack_start(self.export,False,False,0)
        self.open_last=button('Open export folder',self.open_export);right.pack_start(self.open_last,False,False,0)
        self.open_last.set_tooltip_text('Open the last successfully exported folder in Files.')
        self.refresh=button('Scan for new apps',lambda *_:self.run_task(None,False));left.pack_start(self.refresh,False,False,0)
        footer=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=5);footer.set_border_width(8);outer.pack_start(footer,False,False,0)
        footer.pack_start(Gtk.Separator(),False,False,0)
        self.status=label('Choose artwork to begin. Protected system icons and individual games cannot be changed.');self.status.set_selectable(True);footer.pack_start(self.status,False,False,0)
        self.progress=Gtk.ProgressBar();footer.pack_start(self.progress,False,False,0)
        create.drag_dest_set(Gtk.DestDefaults.ALL,[Gtk.TargetEntry.new('text/uri-list',0,0)],Gdk.DragAction.COPY);create.connect('drag-data-received',self.drop)
        library_page=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=10);library_page.set_border_width(14);tabs.append_page(library_page,Gtk.Label(label='My Icons'))
        library_page.pack_start(heading('Your saved creations'),False,False,0)
        library_page.pack_start(label('Save artwork from Create to reuse it later. Loading a creation does not change any application.',True),False,False,0)
        self.library_search=Gtk.SearchEntry();self.library_search.set_placeholder_text('Search saved icons');library_page.pack_start(self.library_search,False,False,0)
        self.library_model=Gtk.ListStore(GdkPixbuf.Pixbuf,str,str)
        self.library_view=Gtk.IconView.new_with_model(self.library_model);self.library_view.set_pixbuf_column(0);self.library_view.set_text_column(1);self.library_view.set_selection_mode(Gtk.SelectionMode.SINGLE);self.library_view.set_item_width(128);self.library_view.set_margin(10);self.library_view.set_spacing(5)
        library_scroll=Gtk.ScrolledWindow();library_scroll.set_policy(Gtk.PolicyType.NEVER,Gtk.PolicyType.AUTOMATIC);library_scroll.set_shadow_type(Gtk.ShadowType.IN);library_scroll.add(self.library_view);library_page.pack_start(library_scroll,True,True,0)
        self.library_count=label('',True);library_page.pack_start(self.library_count,False,False,0)
        self.library_load=button('Use selected icon',self.load_creation);self.library_load.get_style_context().add_class('suggested-action')
        self.library_rename=button('Rename',self.rename_creation);self.library_remove=button('Remove from My Icons',self.remove_creation)
        actions=Gtk.Box(spacing=8);library_page.pack_start(actions,False,False,0)
        for w in (self.library_load,self.library_rename,self.library_remove):actions.pack_start(w,True,True,0)
        self.library_view.connect('selection-changed',lambda *_:self.update_controls() if hasattr(self,'progress') and hasattr(self,'extra') else None)
        self.library_view.connect('item-activated',lambda *_:self.load_creation())
        self.library_search.connect('changed',lambda *_:self.reload_library())
        tools=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=12);tools.set_border_width(16);tabs.append_page(tools,Gtk.Label(label='Advanced'))
        self.extra=[]
        for title,desc,cb in [('Batch export images','Select multiple source images and create all 12 palettes for each in the export location on Create.',self.batch),('Open last export','Open the most recent export folder.',self.open_export),('Export custom pack','Save your custom application logos as a portable ZIP.',self.export_pack),('Import custom pack','Load a ZIP made by Icon Studio and apply eligible overrides.',self.import_pack),('Restore all custom icons','Restore all currently installed eligible customized applications.',self.restore_all)]:
            label=Gtk.Label(label=desc,xalign=0,wrap=True);tools.pack_start(label,False,False,0);b=Gtk.Button(label=title);b.connect('clicked',cb);tools.pack_start(b,False,False,0);self.extra.append(b)
        self.tool_status=Gtk.Label(xalign=0,wrap=True,selectable=True);# status shown in the shared footer
        self.tool_progress=Gtk.ProgressBar();# progress shown in the shared footer
        guide=Gtk.ScrolledWindow();view=Gtk.TextView();view.set_editable(False);view.set_cursor_visible(False);view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR);view.set_left_margin(18);view.set_right_margin(18);view.set_top_margin(14);view.set_bottom_margin(14);view.get_buffer().set_text(GUIDE);guide.add(view);tabs.append_page(guide,Gtk.Label(label='User guide'))
        self.connect('delete-event',lambda *_:self.busy)
        self.reload_apps()
        self.reload_library()
        self.update_controls()
        self.app_reload_pending=False
        self.monitor=Gio.AppInfoMonitor.get();self.monitor.connect('changed',self.apps_changed)
    def apps_changed(self,*_):
        if not self.app_reload_pending:
            self.app_reload_pending=True;GLib.timeout_add(350,self.reload_after_change)
    def reload_after_change(self):
        self.app_reload_pending=False
        if not self.busy:self.reload_apps()
        return False
    def remember_export(self):
        try:atomic(self.settings,json.dumps({'destination':str(self.export_dest),'last_export':str(self.last_export) if self.last_export else ''}).encode())
        except OSError as e:return ' (Could not remember export settings: '+str(e)+')'
        return ''
    def selected_creation(self):
        paths=self.library_view.get_selected_items()
        if not paths:return None
        try:return self.library_model[paths[0]][2]
        except (IndexError,ValueError,TypeError):return None
    def reload_library(self,select=None):
        if self.busy:return
        if not select:select=self.selected_creation()
        query=self.library_search.get_text().casefold().strip();rows,bad=self.library.entries();shown=0
        self.library_model.clear()
        mode=self.modes.get('neon') or next(iter(self.modes.values()))
        for ident,name,art in rows:
            if query and query not in name.casefold():continue
            try:
                cached=self.library_thumbs.get(ident)
                if cached and cached[0]==art:thumb=cached[1]
                else:
                    thumb=pix(r.icon(mode,logo=art),80);self.library_thumbs[ident]=(art,thumb)
            except Exception:bad+=1;continue
            it=self.library_model.append([thumb,name,ident]);shown+=1
            if ident==select:self.library_view.select_path(self.library_model.get_path(it))
        self.library_thumbs={k:v for k,v in self.library_thumbs.items() if k in {row[0] for row in rows}}
        self.library_count.set_text((f'{shown} of {len(rows)} saved icons' if rows else 'No saved icons yet. Use Save to My Icons on the Create tab.')+(f' • {bad} unreadable entries skipped' if bad else ''))
        self.update_controls()
    def ask_name(self,title,initial):
        dialog=Gtk.Dialog(title=title,transient_for=self,modal=True);dialog.add_buttons('Cancel',Gtk.ResponseType.CANCEL,'Save',Gtk.ResponseType.OK)
        box=dialog.get_content_area();box.set_border_width(12);box.set_spacing(8);box.pack_start(Gtk.Label(label='Name your creation:',xalign=0),False,False,0)
        entry=Gtk.Entry();entry.set_max_length(80);entry.set_text(initial[:80]);entry.set_activates_default(True);box.pack_start(entry,False,False,0);dialog.set_default_response(Gtk.ResponseType.OK);dialog.show_all();entry.grab_focus();entry.select_region(0,-1)
        try:return self.library.name(entry.get_text()) if dialog.run()==Gtk.ResponseType.OK else None
        finally:dialog.destroy()
    def save_creation(self,*_):
        if self.busy or not self.logo:return
        try:
            name=self.ask_name('Save to My Icons',self.source_name)
            if name is None:return
            ident=self.library.save(name,self.logo);self.library_search.set_text('');self.reload_library(ident);self.message(f'Saved “{name}” to My Icons. No application changed.')
        except Exception as e:self.message('Could not save icon: '+str(e))
    def load_creation(self,*_):
        if self.busy:return
        ident=self.selected_creation()
        if not ident:return
        try:
            name,art=self.library.read(ident);self.load_artwork(name,art,'Loaded from My Icons: '+name);self.app.selection.unselect_all();self.tabs.set_current_page(0);self.message('Saved creation loaded. Choose an app to apply it, or export the files.')
        except Exception as e:self.message('Could not load icon: '+str(e))
    def rename_creation(self,*_):
        if self.busy:return
        ident=self.selected_creation()
        if not ident:return
        try:
            old,_=self.library.read(ident);name=self.ask_name('Rename saved icon',old)
            if name is None:return
            self.library.rename(ident,name);self.library_search.set_text('');self.reload_library(ident);self.message(f'Renamed saved icon to “{name}”.')
        except Exception as e:self.message('Could not rename icon: '+str(e))
    def remove_creation(self,*_):
        if self.busy:return
        ident=self.selected_creation()
        if not ident:return
        try:
            name,_=self.library.read(ident)
            if self.confirm(f'Remove “{name}” from My Icons?\n\nAlready applied icons and exported files will not be affected.'):
                self.library.remove(ident);self.reload_library();self.message(f'Removed “{name}” from My Icons.')
        except Exception as e:self.message('Could not remove icon: '+str(e))
    def load_artwork(self,name,art,description):
        # Reset tint before replacing the old artwork; saved icons already include their tint.
        self.raw=None;self.tint.set_active(False);self.raw=art;self.source_name=name;self.chooser.unselect_all();self.source_status.set_text(description);self.recolor()
    def load_sample(self,*_):
        if self.busy:return
        try:self.load_artwork('Prism',r.art_png(SAMPLE),'Loaded sample artwork: Prism');self.message('Prism ready. Preview, save, export, or choose an application.')
        except Exception as e:self.message('Could not load sample: '+str(e))
    def reload_apps(self):
        if not hasattr(self,'search') or self.busy:return
        apps={}
        for a in sorted(Gio.AppInfo.get_all(),key=lambda a:(a.get_name() or '').casefold()):
            if not isinstance(a,Gio.DesktopAppInfo) or not a.should_show():continue
            aid=a.get_id();p=a.get_filename()
            if not r.valid(aid) or not p:continue
            f=r.read_fields(Path(p))
            if r.role_of(f,aid) or r.game(f,aid) or aid=='shadowrealm-icon-studio.desktop':continue
            apps[aid]=a
        self.apps=apps
        self.filter_apps()
    def selection_changed(self,*_):
        if not self.searching:self.update_controls()
    def filter_apps(self):
        if not hasattr(self,'match_count') or self.busy:return
        previous=self.app.get_active_id();query=self.search.get_text()
        matches=matching_apps(self.apps,query)
        self.searching=True
        try:
            self.app.remove_all()
            for aid,a in matches:self.app.append(aid,a.get_name() or aid)
            if previous and self.app.set_active_id(previous):pass
            else:self.app.selection.unselect_all()
        finally:self.searching=False
        count=len(matches);total=len(self.apps)
        if not count:
            text=f'No matching apps ({total} eligible installed). Clear or change the search.'
        else:
            text=f'{count} of {total} customizable apps — click a result to select it.'
        if previous and not self.app.get_active_id():text+=' Previous selection cleared.'
        self.match_count.set_text(text);self.update_controls()
    def update_controls(self,*args):
        # Use base sensitivity rules, then update the explicit selection summary.
        super().update_controls(*args)
        if hasattr(self,'use_original'):
            aid=self.app.get_active_id();a=self.apps.get(aid);name=(a.get_name() or aid) if a else None
            self.selection_name.set_markup('<b>'+GLib.markup_escape_text(('Selected: '+name) if name else 'No application selected')+'</b>')
            self.selection_detail.set_text('Ready to apply a new icon to this app.' if name else 'You can still save or export your artwork.');self.selection_detail.set_tooltip_text(aid if name else None)
            self.apply.set_label('Apply to '+name if name else 'Select an app to apply');self.apply.set_tooltip_text('Changes the selected app icon in every theme; no export needed.')
            self.clear_app.set_sensitive(not self.busy and bool(name));self.use_original.set_sensitive(not self.busy and bool(name));self.search.set_sensitive(not self.busy);self.tint.set_sensitive(not self.busy);self.color.set_sensitive(not self.busy and self.tint.get_active())
            self.change_dest.set_sensitive(not self.busy);self.open_last.set_sensitive(not self.busy and self.last_export is not None)
        if hasattr(self,'extra'):
            for b in self.extra:b.set_sensitive(not self.busy)
            self.extra[1].set_sensitive(not self.busy and self.last_export is not None)
        if hasattr(self,'save_library'):self.save_library.set_sensitive(not self.busy and self.logo is not None);self.sample.set_sensitive(not self.busy)
        if hasattr(self,'library_load'):
            chosen=not self.busy and self.selected_creation() is not None
            for w in (self.library_load,self.library_rename,self.library_remove):w.set_sensitive(chosen)
            self.library_view.set_sensitive(not self.busy);self.library_search.set_sensitive(not self.busy)
    def message(self,s):
        self.status.set_text(s)
        if hasattr(self,'tool_status'):self.tool_status.set_text(s)
    def load_logo(self,*_):
        try:
            path=Path(self.chooser.get_filename());art=png_from_file(path);self.raw=None;self.tint.set_active(False);self.raw=art;self.source_name=path.stem;self.source_status.set_text('Loaded: '+path.name);self.recolor();self.message('Artwork ready. Apply to an app, save to My Icons, or export files.')
        except Exception as e:self.raw=None;self.logo=None;[i.clear() for i in self.thumbs.values()];self.source_status.set_text('No artwork loaded');self.message(str(e));self.update_controls()
    def recolor(self):
        if not self.raw:return
        self.logo=self.raw
        if self.tint.get_active():
            c=self.color.get_rgba();rgb=tuple(round(x*255) for x in (c.red,c.green,c.blue));im=Image.open(BytesIO(self.raw)).convert('RGBA');out=ImageOps.colorize(ImageOps.grayscale(im),black=tuple(x//5 for x in rgb),white=rgb).convert('RGBA');out.putalpha(im.getchannel('A'));buf=BytesIO();out.save(buf,format='PNG');self.logo=r.art_png(buf.getvalue())
        self.preview();self.update_controls()
    def preview(self):
        if not self.logo:return
        if hasattr(self,'thumbs'):
            try:
                for mid,im in self.thumbs.items():im.set_from_pixbuf(pix(r.icon(self.modes[mid],logo=self.logo),84))
            except Exception as e:self.message(str(e))
    def drop(self,w,ctx,x,y,data,info,t):
        ok=False
        try:
            if self.busy:raise ValueError('Wait for the current operation.')
            uris=data.get_uris() or []
            if len(uris)!=1:raise ValueError('Drop one local logo; use Batch export for multiple logos.')
            path=Gio.File.new_for_uri(uris[0]).get_path()
            if not path:raise ValueError('Local files only.')
            self.chooser.set_filename(path);self.load_logo();ok=self.logo is not None
        except Exception as e:self.message(str(e))
        Gtk.drag_finish(ctx,ok,False,t)
    def original_logo(self,*_):
        try:
            aid=self.app.get_active_id();state=json.loads((r.STATE/'installed.json').read_text());name=state.get('original_icons',{}).get(aid) or r.read_fields(Path(self.apps[aid].get_filename())).get('Icon','');art=r.source_art(name,r.native_setup())
            if art is None:raise ValueError('Original artwork unavailable; choose a logo file instead.')
            name=self.apps[aid].get_name() or aid;self.load_artwork(name,r.art_png(art),'Loaded original artwork: '+name);self.message('Original application artwork loaded.')
        except Exception as e:self.message(str(e))
    def choose(self,title,action,multiple=False,name=None):
        d=Gtk.FileChooserDialog(title=title,parent=self,action=action);d.add_buttons('Cancel',Gtk.ResponseType.CANCEL,'Select',Gtk.ResponseType.OK);d.set_select_multiple(multiple)
        if name:d.set_current_name(name);d.set_do_overwrite_confirmation(True)
        try:return d.get_filenames() if d.run()==Gtk.ResponseType.OK else []
        finally:d.destroy()
    def confirm(self,s):
        d=Gtk.MessageDialog(transient_for=self,modal=True,message_type=Gtk.MessageType.QUESTION,buttons=Gtk.ButtonsType.YES_NO,text=s)
        try:return d.run()==Gtk.ResponseType.YES
        finally:d.destroy()
    def start(self,fn):
        if self.busy:return
        self.busy=True;self.progress.set_fraction(0);self.tool_progress.set_fraction(0);self.message('Working…');self.update_controls();GLib.timeout_add(150,self.pulse)
        def worker():
            try:msg=fn()
            except Exception as e:msg='Operation not completed: '+str(e)
            GLib.idle_add(self.finish2,msg)
        threading.Thread(target=worker,daemon=False).start()
    def pulse(self):
        if not self.busy:return False
        self.progress.pulse();self.tool_progress.pulse();return True
    def finish2(self,msg):
        self.busy=False;self.progress.set_fraction(1 if not msg.startswith('Operation not completed') else 0);self.tool_progress.set_fraction(self.progress.get_fraction());self.message(msg);self.reload_apps();self.reload_library();self.update_controls();return False
    def export_sets(self,items,dest):
        dest=Path(dest);dest.mkdir(parents=True,exist_ok=True)
        name=(re.sub(r'[^A-Za-z0-9_.-]','_',items[0][0])[:60].strip('.') or 'icon') if len(items)==1 else 'batch'
        root=dest/(name+'-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f'));root.mkdir();total=0
        for j,(name,art) in enumerate(items):
            base=root if len(items)==1 else root/(f'{j+1:03d}-'+re.sub(r'[^A-Za-z0-9_.-]','_',name)[:80]);base.mkdir(exist_ok=True)
            for mode in self.modes.values():
                d=base/mode['icons'];d.mkdir();svg=r.icon(mode,logo=art);(d/'icon.svg').write_bytes(svg)
                for size in r.SIZES:(d/f'icon-{size}.png').write_bytes(r.raster(svg,size))
                total+=1
        self.last_export=root;return f'Exported {total} SVG masters and {total*len(r.SIZES)} PNGs to {root}'+self.remember_export()
    def select_destination(self,*_):
        d=Gtk.FileChooserDialog(title='Choose where to save exported icon files',parent=self,action=Gtk.FileChooserAction.SELECT_FOLDER)
        d.add_buttons('Cancel',Gtk.ResponseType.CANCEL,'Use this folder',Gtk.ResponseType.OK)
        d.set_current_folder(str(self.export_dest if self.export_dest.is_dir() else self.export_dest.parent if self.export_dest.parent.is_dir() else H))
        try:
            if d.run()==Gtk.ResponseType.OK:
                self.export_dest=Path(d.get_filename());self.dest_label.set_text(str(self.export_dest));self.message('Export location updated. No files saved yet.'+self.remember_export())
        finally:d.destroy()
    def export_all(self,*_):
        if not self.logo or self.busy:return
        dest=self.export_dest;art=self.logo;name=self.source_name
        if self.confirm(f'Save 108 icon files in a new folder inside:\n{dest}\n\nNo application icons will be changed.'):
            self.start(lambda:self.export_sets([(name,art)],dest))
    def batch(self,*_):
        paths=self.choose('Choose source images',Gtk.FileChooserAction.OPEN,True)
        if not paths:return
        if len(paths)>100:self.message('Select at most 100 images per batch.');return
        dest=self.export_dest
        if not self.confirm(f'Export {len(paths)} images to a new folder inside:\n{dest}\n\nNo application icons will be changed.'):return
        def work():return self.export_sets([(Path(p).stem,png_from_file(p)) for p in paths],dest)
        self.start(work)
    def open_export(self,*_):
        if self.last_export:
            try:Gio.AppInfo.launch_default_for_uri(self.last_export.as_uri(),None)
            except Exception as e:self.message('Cannot open export folder: '+str(e))
    def eligible(self):return set(self.apps)
    def override_files(self):return {p.stem:p for p in (r.STATE/'custom-logos').glob('*.png') if r.valid(p.stem) and p.is_file() and not p.is_symlink()}
    def export_pack(self,*_):
        dest=self.choose('Save custom icon pack',Gtk.FileChooserAction.SAVE,name='ShadowRealm-Custom-Icons.zip')
        if not dest:return
        path=Path(dest[0])
        if path.suffix.lower()!='.zip':self.message('Use a .zip filename.');return
        def work():
            with (r.STATE/'lock').open('a') as lock:
                fcntl.flock(lock,fcntl.LOCK_EX);files=self.override_files()
                if not files:raise ValueError('No custom overrides to export.')
                with tempfile.NamedTemporaryFile(dir=path.parent,delete=False) as t:tmp=Path(t.name)
                try:
                    with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as z:
                        z.writestr('manifest.json',json.dumps({'format':'shadowrealm-custom-logos-v1','ids':sorted(files)}))
                        for aid,p in files.items():z.writestr('logos/'+aid+'.png',r.art_png(p.read_bytes()))
                    os.replace(tmp,path)
                finally:tmp.unlink(missing_ok=True)
            return f'Exported {len(files)} custom overrides to {path}'
        self.start(work)
    def import_pack(self,*_):
        paths=self.choose('Open custom icon pack',Gtk.FileChooserAction.OPEN)
        if not paths:return
        try:
            path=Path(paths[0]);eligible=self.eligible();changes={}
            if path.stat().st_size>128*1024*1024:raise ValueError('Pack exceeds 128 MB.')
            with zipfile.ZipFile(path) as z:
                infos=z.infolist()
                if len(infos)>1001 or len({x.filename for x in infos})!=len(infos) or sum(x.file_size for x in infos)>128*1024*1024:raise ValueError('Invalid or oversized pack.')
                manifest=json.loads(z.read('manifest.json'));ids=manifest['ids']
                if manifest.get('format')!='shadowrealm-custom-logos-v1' or not isinstance(ids,list) or not all(r.valid(x) and x.endswith('.desktop') for x in ids) or len(ids)!=len(set(ids)):raise ValueError('Invalid pack manifest.')
                if set(z.namelist())!={'manifest.json'}|{'logos/'+aid+'.png' for aid in ids}:raise ValueError('Unexpected pack content.')
                for aid in ids:
                    if aid in eligible:
                        with Image.open(BytesIO(z.read('logos/'+aid+'.png'))) as im:
                            if im.format!='PNG' or max(im.size)>256:raise ValueError('Invalid pack logo.')
                        changes[aid]=r.art_png(z.read('logos/'+aid+'.png'))
            if not changes:raise ValueError('No eligible installed applications match this pack.')
            if self.confirm(f'Apply {len(changes)} overrides? Existing custom logos for these apps will be replaced. {len(ids)-len(changes)} unavailable or protected apps will be skipped.'):self.run_changes(changes)
        except Exception as e:self.message(str(e))
    def restore_all(self,*_):
        ids=self.eligible()&self.override_files().keys()
        if not ids:self.message('No eligible custom overrides to restore.');return
        if self.confirm(f'Restore original artwork for {len(ids)} installed apps?'):self.run_changes(dict.fromkeys(ids))
    def change_custom(self,reset):
        aid=self.app.get_active_id();a=self.apps.get(aid)
        if self.busy or not a or (not reset and not self.logo):return
        name=a.get_name() or aid
        prompt=(f'Restore the original icon for {name}?\n{aid}' if reset else f'Apply the loaded artwork to {name}?\n{aid}\n\nThis updates the icon in all 12 themes. The application itself is unchanged.')
        if self.confirm(prompt):self.run_task(aid,reset)
    def run_task(self,aid,reset):
        self.run_changes({aid:None if reset else self.logo} if aid else {})
    def run_changes(self,changes):
        if not set(changes)<=self.eligible():self.message('Protected or unavailable application.');return
        # Gtk.IconTheme lookup belongs on the GUI thread; only the child engine
        # process and GdkPixbuf/Pillow file rendering run in the worker.
        expected=dict(changes)
        try:
            resets=[aid for aid,data in changes.items() if data is None]
            if resets:
                state=json.loads((r.STATE/'installed.json').read_text());fallback=r.native_setup()
                for aid in resets:
                    src=state.get('original_icons',{}).get(aid,'');art=r.source_art(src,fallback)
                    if not art:raise RuntimeError('Cannot restore original artwork for '+aid+'; no overrides changed.')
                    expected[aid]=art
        except Exception as e:self.message(str(e));return
        def work():
            state=json.loads((r.STATE/'installed.json').read_text())
            if not state.get('fingerprint') or not isinstance(state.get('per_app'),dict):raise RuntimeError('Incremental state missing; no rebuild started.')
            backup=H/'shadowrealm-checkpoints'/('icon-studio-v2-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f'));backup.mkdir(parents=True)
            originals={}
            with (r.STATE/'lock').open('a') as lock:
                fcntl.flock(lock,fcntl.LOCK_EX)
                for aid,data in changes.items():
                    p=r.STATE/'custom-logos'/(aid+'.png');originals[aid]=p.read_bytes() if p.is_file() else None
                    if originals[aid] is not None:(backup/(aid+'.png')).write_bytes(originals[aid])
                (backup/'changes.json').write_text(json.dumps({aid:originals[aid] is not None for aid in changes}))
                try:
                    for aid,data in changes.items():
                        p=r.STATE/'custom-logos'/(aid+'.png')
                        if data is None:p.unlink(missing_ok=True)
                        else:atomic(p,data)
                except BaseException:
                    for aid,data in originals.items():
                        p=r.STATE/'custom-logos'/(aid+'.png')
                        if data is None:p.unlink(missing_ok=True)
                        else:atomic(p,data)
                    raise
            def refresh():
                result=subprocess.run([sys.executable,str(ENGINE/'rebuild.py'),'--refresh'],capture_output=True,text=True,timeout=600)
                if result.returncode:raise RuntimeError((result.stderr or result.stdout or 'Icon engine failed')[-1000:])
                return result.stdout
            try:
                output=refresh()
                for aid,data in expected.items():
                    for m in self.modes.values():
                        p=r.U/m['icons']/'scalable/apps'/(r.key(aid)+'.svg')
                        if not p.is_file() or p.read_bytes()!=r.icon(m,logo=data):raise RuntimeError('Artwork verification failed: '+aid+' / '+m['icons'])
            except Exception as exc:
                with (r.STATE/'lock').open('a') as lock:
                    fcntl.flock(lock,fcntl.LOCK_EX)
                    for aid,data in originals.items():
                        p=r.STATE/'custom-logos'/(aid+'.png')
                        if data is None:p.unlink(missing_ok=True)
                        else:atomic(p,data)
                try:refresh()
                except Exception as rollback:raise RuntimeError(f'{exc}; rollback refresh failed: {rollback}; backup {backup}')
                raise RuntimeError(f'{exc}; prior override requests restored; backup {backup}')
            if changes:r.refresh_panel()
            return ('Updated and verified '+(self.apps[next(iter(changes))].get_name() or next(iter(changes)) if len(changes)==1 else str(len(changes))+' apps')+' across all 12 palettes.') if changes else 'Application scan finished. '+output[-500:]
        self.start(work)

if __name__=='__main__':
    win=Studio2();win.show_all();Gtk.main()

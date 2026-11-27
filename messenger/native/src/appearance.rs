use std::{cell::RefCell,path::{Path,PathBuf}};
use gtk::prelude::*;

thread_local! {
    static PROVIDER:RefCell<Option<gtk::CssProvider>>=const{RefCell::new(None)};
    static MONITORS:RefCell<Vec<gtk::gio::FileMonitor>>=const{RefCell::new(Vec::new())};
    static LOGOS:RefCell<Vec<gtk::glib::WeakRef<gtk::Picture>>>=const{RefCell::new(Vec::new())};
}

const SHEET:&str=r#"
@define-color messenger_bg {bg};
@define-color messenger_fg {fg};
@define-color messenger_accent {accent};
.messenger-window { background-color:@messenger_bg; color:@messenger_fg; }
.messenger-window headerbar { background-image:none; background-color:mix(@messenger_bg,@messenger_fg,0.055); color:@messenger_fg; border-bottom:1px solid alpha(@messenger_accent,0.28); box-shadow:none; }
.messenger-window .messenger-menubar, .messenger-menubar, .messenger-window menubar, menubar.messenger-menubar { background-image:none; background-color:mix(@messenger_bg,@messenger_fg,0.055); color:@messenger_fg; border-bottom:1px solid alpha(@messenger_accent,0.28); box-shadow:none; padding:2px 6px; }
.messenger-window .messenger-menubar > item, .messenger-menubar > item, .messenger-window menubar > item, menubar.messenger-menubar > item { color:@messenger_fg; border-radius:6px; padding:4px 9px; }
.messenger-window .messenger-menubar > item:hover, .messenger-menubar > item:hover, .messenger-window menubar > item:hover, menubar.messenger-menubar > item:hover, .messenger-window .messenger-menubar > item:selected, .messenger-menubar > item:selected, .messenger-window menubar > item:selected, menubar.messenger-menubar > item:selected { background-color:alpha(@messenger_accent,0.22); color:@messenger_fg; }
.messenger-window .messenger-menubar > item > label, .messenger-menubar > item > label, .messenger-window menubar > item > label, menubar.messenger-menubar > item > label { color:@messenger_fg; }
.messenger-window .messenger-menubar menubutton, .messenger-window .messenger-menubar button { background-image:none; background-color:transparent; color:@messenger_fg; border:none; box-shadow:none; padding:4px 9px; min-height:0; }
.messenger-window .messenger-menubar menubutton:hover, .messenger-window .messenger-menubar button:hover, .messenger-window .messenger-menubar menubutton:checked, .messenger-window .messenger-menubar button:checked { background-color:alpha(@messenger_accent,0.22); color:@messenger_fg; }
.messenger-window .messenger-menubar menubutton label, .messenger-window .messenger-menubar button label { color:@messenger_fg; }
popover.menu, popover.menu > contents, popover.background > contents { background-image:none; background-color:mix(@messenger_bg,@messenger_fg,0.055); color:@messenger_fg; }
popover.menu modelbutton, popover.menu label { color:@messenger_fg; }
popover.menu modelbutton:hover { background-color:alpha(@messenger_accent,0.22); }
.messenger-window decoration { border-radius:12px; box-shadow:0 5px 20px alpha(black,0.4); }
.messenger-window label { color:@messenger_fg; }
.messenger-window entry, .messenger-window passwordentry,
.messenger-window textview, .messenger-window textview text,
.messenger-window list, .messenger-window listview { background-color:mix(@messenger_bg,@messenger_fg,0.04); color:@messenger_fg; caret-color:@messenger_accent; }
.messenger-window button { background-image:none; background-color:mix(@messenger_bg,@messenger_fg,0.07); color:@messenger_fg; border:1px solid alpha(@messenger_accent,0.45); border-radius:8px; }
.messenger-window button:hover, .messenger-window button:checked { background-color:mix(@messenger_bg,@messenger_accent,0.18); }
.messenger-window button:disabled { opacity:0.58; }
.messenger-window button.suggested-action { background-color:@messenger_accent; color:{ink}; }
.messenger-window button.suggested-action label { color:{ink}; }
.messenger-window switch { background-color:mix(@messenger_bg,@messenger_fg,0.18); border-radius:999px; }
.messenger-window switch:checked { background-color:@messenger_accent; }
.messenger-window switch > slider { background-color:{ink}; }
.messenger-window checkbutton check { background-color:mix(@messenger_bg,@messenger_fg,0.05); border:1px solid alpha(@messenger_fg,0.55); border-radius:4px; }
.messenger-window checkbutton check:checked { background-color:@messenger_accent; color:{ink}; border-color:@messenger_accent; }
.messenger-window row:selected { background-color:mix(@messenger_bg,@messenger_accent,0.22); }
.messenger-window .messenger-sidebar { background-color:mix(@messenger_bg,@messenger_fg,0.055); }
.messenger-window .messenger-sidebar list { background-color:transparent; }
.messenger-window .messenger-history, .messenger-window .messenger-composer { border-color:alpha(@messenger_accent,0.5); background-color:mix(@messenger_bg,@messenger_fg,0.025); }
.messenger-window .messenger-history text, .messenger-window .messenger-composer text { background-color:transparent; }
.messenger-window .messenger-notice { background-color:mix(@messenger_bg,@messenger_accent,0.08); border-color:alpha(@messenger_accent,0.4); }
.messenger-window .messenger-card { background-color:mix(@messenger_bg,@messenger_fg,0.035); border:1px solid alpha(@messenger_accent,0.32); border-radius:16px; padding:26px; }
.messenger-window .messenger-nav { background-color:mix(@messenger_bg,@messenger_fg,0.045); border:1px solid alpha(@messenger_fg,0.06); border-radius:14px; padding:10px; }
.messenger-window .messenger-nav button.messenger-nav-item { background-color:transparent; border:none; border-radius:9px; padding:9px 12px; }
.messenger-window .messenger-nav button.messenger-nav-item:hover { background-color:alpha(@messenger_fg,0.07); }
.messenger-window .messenger-nav button.messenger-nav-item.active { background-color:alpha(@messenger_accent,0.22); border:1px solid alpha(@messenger_accent,0.5); }
.messenger-window .messenger-nav button.messenger-nav-item.active label { color:@messenger_fg; }
.messenger-window .messenger-profile { background-color:mix(@messenger_bg,@messenger_fg,0.045); border:1px solid alpha(@messenger_fg,0.06); border-radius:14px; padding:16px; }
.messenger-window .messenger-avatar { background-color:@messenger_accent; color:{ink}; border-radius:40px; min-width:80px; min-height:80px; font-size:26pt; font-weight:700; }
.messenger-window .messenger-avatar-small { background-color:alpha(@messenger_accent,0.32); color:@messenger_fg; border-radius:16px; min-width:32px; min-height:32px; font-weight:700; }
.messenger-window .messenger-avatar-chat { background-color:@messenger_accent; color:{ink}; border-radius:18px; min-width:36px; min-height:36px; font-weight:700; }
.messenger-window .messenger-avatar-picture { border-radius:38px; min-width:76px; min-height:76px; }
.messenger-window .messenger-brand-logo { background:transparent; }
.messenger-window .messenger-bubble { border-radius:14px; padding:8px 12px; }
.messenger-window .messenger-bubble-in { background-color:mix(@messenger_bg,@messenger_fg,0.075); border:1px solid alpha(@messenger_fg,0.10); }
.messenger-window .messenger-bubble-out { background-color:alpha(@messenger_accent,0.22); border:1px solid alpha(@messenger_accent,0.42); }
.messenger-window .messenger-sender { font-weight:700; font-size:10pt; color:mix(@messenger_fg,@messenger_accent,0.35); }
.messenger-window .messenger-body { font-size:11pt; }
.messenger-window .messenger-action { font-style:italic; }
.messenger-window .messenger-time { font-size:8pt; color:alpha(@messenger_fg,0.55); }
.messenger-window .messenger-error { font-size:8pt; color:{error}; }
.messenger-window .messenger-day { font-size:9pt; color:alpha(@messenger_fg,0.62); padding:10px 0 6px; }
.messenger-window .messenger-day-row { background-color:transparent; }
.messenger-window .messenger-message-row { background-color:transparent; padding:2px 12px; }
.messenger-window .messenger-transcript { background-color:transparent; }
.messenger-window .messenger-transcript row { background-color:transparent; }
.messenger-window .messenger-typing { font-size:9pt; color:alpha(@messenger_fg,0.65); }
.messenger-window .messenger-empty { color:alpha(@messenger_fg,0.55); }
.messenger-window .messenger-security { font-size:9pt; color:alpha(@messenger_fg,0.62); }
.messenger-window .messenger-status-line { font-size:9pt; color:alpha(@messenger_fg,0.62); }
.messenger-window .messenger-composer-frame { border:1px solid alpha(@messenger_accent,0.5); border-radius:12px; background-color:mix(@messenger_bg,@messenger_fg,0.025); }
.messenger-window .messenger-composer-frame textview, .messenger-window .messenger-composer-frame textview text { background-color:transparent; }
.messenger-window .messenger-small-button { padding:4px 8px; font-size:9pt; }
.messenger-window .messenger-header-button { background-color:transparent; border:1px solid alpha(@messenger_fg,0.22); border-radius:8px; padding:4px 10px; }
.messenger-window .messenger-chat-heading { font-weight:700; font-size:12pt; }
.messenger-window .messenger-chat-subtitle { font-size:9pt; color:alpha(@messenger_fg,0.62); }
.messenger-window .messenger-connection-row { background-color:transparent; padding:6px 4px; border-radius:10px; }
.messenger-window .messenger-connection-row:hover { background-color:alpha(@messenger_fg,0.045); }
.messenger-window .messenger-connection-name { font-weight:600; }
.messenger-window .messenger-connection-subtitle { font-size:9pt; color:alpha(@messenger_fg,0.62); }
.messenger-window .messenger-page-title { font-weight:700; font-size:15pt; }
.messenger-window .messenger-section { font-weight:700; font-size:9pt; color:alpha(@messenger_fg,0.62); }
.messenger-window .messenger-muted { font-size:9pt; color:alpha(@messenger_fg,0.62); }
.messenger-window .messenger-badge { background-color:@messenger_accent; color:{ink}; border-radius:9px; min-width:18px; min-height:18px; font-size:8pt; font-weight:700; }
.messenger-window .messenger-dot-online { color:{dot_online}; }
.messenger-window .messenger-dot-away { color:{dot_away}; }
.messenger-window .messenger-dot-dnd { color:{dot_dnd}; }
.messenger-window .messenger-dot-invisible { color:{dot_neutral}; }
.messenger-window .messenger-dot-offline { color:{dot_neutral}; }
.messenger-window .messenger-dot-unknown { color:{dot_neutral}; }
.messenger-window .messenger-activity-row { background-color:transparent; padding:8px 6px; border-radius:10px; }
.messenger-window .messenger-activity-row:hover { background-color:alpha(@messenger_fg,0.045); }
.messenger-window .messenger-activity-title { font-weight:600; }
.messenger-window .messenger-activity-body { font-size:9pt; color:alpha(@messenger_fg,0.70); }
.messenger-window .messenger-activity-time { font-size:8pt; color:alpha(@messenger_fg,0.52); }
"#;

fn color(value:&serde_json::Value,key:&str)->Option<String>{
    let value=value.get(key)?.as_str()?;
    (value.len()==7&&value.starts_with('#')&&value[1..].bytes().all(|c|c.is_ascii_hexdigit())).then(||value.to_owned())
}
fn sheet(record:&serde_json::Value)->Option<String>{
    let bg=color(record,"background")?;let fg=color(record,"foreground")?;let accent=color(record,"accent")?;
    let channels=(1..6).step_by(2).map(|i|u8::from_str_radix(&accent[i..i+2],16).unwrap() as f64/255.).map(|c|if c<=0.04045{c/12.92}else{((c+0.055)/1.055).powf(2.4)}).collect::<Vec<_>>();
    let luminance=channels[0]*0.2126+channels[1]*0.7152+channels[2]*0.0722;let ink=if luminance>0.179{"#101114"}else{"#ffffff"};
    let light=record.get("light").and_then(|value|value.as_bool()).unwrap_or(false);
    let (dot_online,dot_away,dot_dnd,dot_neutral,error)=if light{
        ("#1f7a36","#8a5200","#b42318","#5f5f6a","#b42318")
    }else{
        ("#35c759","#ffb020","#ff7b7b","#9a9aa8","#ff9b9b")
    };
    Some(SHEET.replace("{bg}",&bg).replace("{fg}",&fg).replace("{accent}",&accent).replace("{ink}",ink)
        .replace("{dot_online}",dot_online).replace("{dot_away}",dot_away).replace("{dot_dnd}",dot_dnd)
        .replace("{dot_neutral}",dot_neutral).replace("{error}",error))
}
fn home()->Option<PathBuf>{std::env::var_os("HOME").map(PathBuf::from).filter(|path|path.is_absolute())}
fn directories()->Option<(PathBuf,PathBuf)>{
    let home=home()?;Some((home.join(".config/shadowrealm-os"),home.join(".local/share/shadow-link")))
}
fn palette()->Option<serde_json::Value>{
    let (_,base)=directories()?;let data=std::fs::read(base.join("appearance-modes.json")).ok()?;
    if data.len()>256*1024{return None;}serde_json::from_slice(&data).ok()
}
fn logo_path()->Option<PathBuf>{
    let (config,base)=directories()?;
    let mode=std::fs::read_to_string(config.join("appearance-mode")).unwrap_or_default();
    if let Some(path)=palette().and_then(|modes|modes.get(mode.trim()).and_then(|record|record.get("logo")).and_then(|value|value.as_str()).map(PathBuf::from)){
        if path.is_absolute()&&path.is_file(){return Some(path);}
    }
    let fallback=base.join("logo.png");fallback.is_file().then_some(fallback)
}
fn refresh_logos(){
    let path=logo_path();
    LOGOS.with(|logos|{
        let mut logos=logos.borrow_mut();logos.retain(|picture|picture.upgrade().is_some());
        for picture in logos.iter(){if let Some(picture)=picture.upgrade(){picture.set_filename(path.as_deref());}}
    });
}
/// The current theme's SR logo, shared by brand marks and kept in sync with Appearance.
pub fn brand_logo(size:i32)->gtk::Picture{
    let picture=gtk::Picture::new();picture.set_can_shrink(true);picture.set_content_fit(gtk::ContentFit::Contain);
    picture.set_size_request(size,size);picture.add_css_class("messenger-brand-logo");
    init();picture.set_filename(logo_path().as_deref());
    LOGOS.with(|logos|logos.borrow_mut().push(picture.downgrade()));
    picture
}
fn refresh(provider:&gtk::CssProvider){
    refresh_logos();
    let Some((config,_))=directories() else{return};
    let Ok(mode)=std::fs::read_to_string(config.join("appearance-mode")) else{return};
    let Some(modes)=palette() else{return};
    let Some(record)=modes.get(mode.trim()) else{return};let Some(css)=sheet(record) else{return};
    if let Some(settings)=gtk::Settings::default(){settings.set_gtk_application_prefer_dark_theme(!record.get("light").and_then(|value|value.as_bool()).unwrap_or(false));}
    provider.load_from_data(&css);
}
fn watch(provider:&gtk::CssProvider){
    let Some((config,base))=directories() else{return};
    for directory in [&config,&base]{
        if let Ok(monitor)=gtk::gio::File::for_path(directory).monitor_directory(gtk::gio::FileMonitorFlags::NONE,None::<&gtk::gio::Cancellable>){
            let provider=provider.clone();monitor.connect_changed(move|_,file,other,_|{
                let relevant=[Some(file),other].into_iter().flatten().filter_map(|file|file.basename())
                    .any(|name|name==Path::new("appearance-mode")||name==Path::new("appearance-modes.json"));
                if relevant{refresh(&provider);}
            });MONITORS.with(|monitors|monitors.borrow_mut().push(monitor));
        }
    }
}
fn init(){
    PROVIDER.with(|slot|{
        if slot.borrow().is_some(){return;}
        let provider=gtk::CssProvider::new();
        if let Some(display)=gtk::gdk::Display::default(){gtk::style_context_add_provider_for_display(&display,&provider,gtk::STYLE_PROVIDER_PRIORITY_APPLICATION+1);}
        watch(&provider);refresh(&provider);*slot.borrow_mut()=Some(provider);
    });
}
pub fn attach<W:IsA<gtk::Widget>>(window:&W){
    window.add_css_class("messenger-window");init();
}
/// Forces a re-read after the desktop appearance changes or from Preferences.
pub fn refresh_now(){PROVIDER.with(|slot|if let Some(provider)=slot.borrow().as_ref(){refresh(provider);});}
/// The palette currently inherited from ShadowRealm-OS, for the Preferences note.
pub fn current_label()->String{
    let Some((config,_))=directories() else{return "System theme".into()};
    let Ok(mode)=std::fs::read_to_string(config.join("appearance-mode")) else{return "System theme".into()};
    palette().and_then(|modes|modes.get(mode.trim()).and_then(|record|record.get("label")).and_then(|label|label.as_str()).map(str::to_owned))
        .unwrap_or_else(||"System theme".into())
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn palette_values_cannot_inject_css(){
        assert!(sheet(&serde_json::json!({"background":"#000000","foreground":"#ffffff","accent":"#55aaff"})).is_some());
        assert!(sheet(&serde_json::json!({"background":"red; color:white","foreground":"#ffffff","accent":"#55aaff"})).is_none());
    }
    #[test]
    #[ignore = "requires GTK display and factory appearance modes"]
    fn factory_palette_sheets_parse(){
        gtk::init().unwrap();
        let path=std::env::var("SHADOW_MESSENGER_TEST_PALETTES").unwrap();
        let records:serde_json::Value=serde_json::from_slice(&std::fs::read(path).unwrap()).unwrap();
        assert!(records.as_object().unwrap().len()>=12);
        for (name,record) in records.as_object().unwrap(){
            let provider=gtk::CssProvider::new();
            let failures=std::rc::Rc::new(std::cell::RefCell::new(Vec::new()));let captured=failures.clone();
            provider.connect_parsing_error(move|_,_,error|captured.borrow_mut().push(error.to_string()));
            provider.load_from_data(&sheet(record).expect("valid factory palette"));
            assert!(failures.borrow().is_empty(),"{name}: {:?}",failures.borrow());
        }
    }
}

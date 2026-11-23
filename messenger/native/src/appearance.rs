use std::path::{Path,PathBuf};
use gtk::prelude::*;

fn color(value:&serde_json::Value,key:&str)->Option<String>{
    let value=value.get(key)?.as_str()?;
    (value.len()==7&&value.starts_with('#')&&value[1..].bytes().all(|c|c.is_ascii_hexdigit())).then(||value.to_owned())
}
fn sheet(record:&serde_json::Value)->Option<String>{
    let bg=color(record,"background")?;let fg=color(record,"foreground")?;let accent=color(record,"accent")?;
    let channels=(1..6).step_by(2).map(|i|u8::from_str_radix(&accent[i..i+2],16).unwrap() as f64/255.).map(|c|if c<=0.04045{c/12.92}else{((c+0.055)/1.055).powf(2.4)}).collect::<Vec<_>>();
    let luminance=channels[0]*0.2126+channels[1]*0.7152+channels[2]*0.0722;let ink=if luminance>0.179{"#101114"}else{"#ffffff"};
    Some(format!(r#"
@define-color messenger_bg {bg};
@define-color messenger_fg {fg};
@define-color messenger_accent {accent};
.messenger-window {{ background-color:@messenger_bg; color:@messenger_fg; }}
.messenger-window headerbar {{ background-image:none; background-color:mix(@messenger_bg,@messenger_fg,0.055); color:@messenger_fg; border-bottom:1px solid alpha(@messenger_accent,0.28); box-shadow:none; }}
.messenger-window decoration {{ border-radius:12px; box-shadow:0 5px 20px alpha(black,0.4); }}
.messenger-window label {{ color:@messenger_fg; }}
.messenger-window entry, .messenger-window passwordentry,
.messenger-window textview, .messenger-window textview text,
.messenger-window list {{ background-color:mix(@messenger_bg,@messenger_fg,0.04); color:@messenger_fg; caret-color:@messenger_accent; }}
.messenger-window button {{ background-image:none; background-color:mix(@messenger_bg,@messenger_fg,0.07); color:@messenger_fg; border:1px solid alpha(@messenger_accent,0.45); border-radius:8px; }}
.messenger-window button:hover, .messenger-window button:checked {{ background-color:mix(@messenger_bg,@messenger_accent,0.18); }}
.messenger-window button:disabled {{ opacity:0.58; }}
.messenger-window button.suggested-action {{ background-color:@messenger_accent; color:{ink}; }}
.messenger-window button.suggested-action label {{ color:{ink}; }}
.messenger-window checkbutton check {{ background-color:mix(@messenger_bg,@messenger_fg,0.05); border:1px solid alpha(@messenger_fg,0.55); border-radius:4px; }}
.messenger-window checkbutton check:checked {{ background-color:@messenger_accent; color:{ink}; border-color:@messenger_accent; }}
.messenger-window row:selected {{ background-color:mix(@messenger_bg,@messenger_accent,0.22); }}
.messenger-window .messenger-sidebar {{ background-color:mix(@messenger_bg,@messenger_fg,0.055); }}
.messenger-window .messenger-sidebar list {{ background-color:transparent; }}
.messenger-window .messenger-history, .messenger-window .messenger-composer {{ border-color:alpha(@messenger_accent,0.5); background-color:mix(@messenger_bg,@messenger_fg,0.025); }}
.messenger-window .messenger-history text, .messenger-window .messenger-composer text {{ background-color:transparent; }}
.messenger-window .messenger-notice {{ background-color:mix(@messenger_bg,@messenger_accent,0.08); border-color:alpha(@messenger_accent,0.4); }}
"#))
}
fn refresh(provider:&gtk::CssProvider,config:&Path,base:&Path){
    let Ok(mode)=std::fs::read_to_string(config.join("appearance-mode")) else{return};
    let Ok(data)=std::fs::read(base.join("appearance-modes.json")) else{return};
    if data.len()>256*1024{return;}
    let Ok(modes)=serde_json::from_slice::<serde_json::Value>(&data) else{return};
    let Some(record)=modes.get(mode.trim()) else{return};let Some(css)=sheet(record) else{return};
    if let Some(settings)=gtk::Settings::default(){settings.set_gtk_application_prefer_dark_theme(!record.get("light").and_then(|v|v.as_bool()).unwrap_or(false));}
    provider.load_from_data(&css);
}
pub fn attach(window:&gtk::ApplicationWindow){
    window.add_css_class("messenger-window");
    let Some(home)=std::env::var_os("HOME").map(PathBuf::from) else{return};
    let config=home.join(".config/shadowrealm-os");let base=home.join(".local/share/shadow-link");let provider=gtk::CssProvider::new();
    if let Some(display)=gtk::gdk::Display::default(){gtk::style_context_add_provider_for_display(&display,&provider,gtk::STYLE_PROVIDER_PRIORITY_APPLICATION+1);}
    refresh(&provider,&config,&base);let mut monitors=Vec::new();
    for directory in [&config,&base]{
        if let Ok(monitor)=gtk::gio::File::for_path(directory).monitor_directory(gtk::gio::FileMonitorFlags::NONE,None::<&gtk::gio::Cancellable>){
            let weak=window.downgrade();let provider=provider.clone();let config=config.clone();let base=base.clone();
            monitor.connect_changed(move|_,file,other,_|{
                let relevant=[Some(file),other].into_iter().flatten().filter_map(|file|file.basename()).any(|name|name==Path::new("appearance-mode")||name==Path::new("appearance-modes.json"));
                if relevant&&weak.upgrade().is_some(){refresh(&provider,&config,&base);}
            });monitors.push(monitor);
        }
    }
    window.connect_destroy(move |_|{for monitor in &monitors{monitor.cancel();}});
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

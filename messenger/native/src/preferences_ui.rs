//! Preferences. Appearance is deliberately read-only: Messenger follows ShadowRealm-OS.
use std::rc::Rc;
use gtk::prelude::*;
use crate::{appearance,settings};

#[derive(Clone)]
pub struct Actions {
    pub security:Rc<dyn Fn()>,
    pub recovery:Rc<dyn Fn()>,
    pub logout:Rc<dyn Fn()>,
    pub test_notification:Rc<dyn Fn()>,
    pub test_sound:Rc<dyn Fn(String)>,
}

pub struct Preferences {
    window:gtk::Window,
    main:gtk::Window,
    nav:gtk::ListBox,
    stack:gtk::Stack,
    account:gtk::Label,
    theme:gtk::Label,
    status:gtk::Label,
}

fn page(title:&str)->(gtk::Box,gtk::Box){
    let outer=gtk::Box::new(gtk::Orientation::Vertical,12);outer.set_margin_top(22);outer.set_margin_bottom(22);outer.set_margin_start(24);outer.set_margin_end(24);
    let heading=gtk::Label::new(Some(title));heading.add_css_class("messenger-page-title");heading.set_xalign(0.0);outer.append(&heading);
    let content=gtk::Box::new(gtk::Orientation::Vertical,14);outer.append(&content);
    (outer,content)
}
fn add_page(stack:&gtk::Stack,page:&gtk::Box,name:&str){
    let scroll=gtk::ScrolledWindow::builder().child(page)
        .hscrollbar_policy(gtk::PolicyType::Never).vexpand(true).build();
    scroll.set_vexpand(true);
    stack.add_named(&scroll,Some(name));
}
fn toggle(key:&str,default:bool,title:&str,note:&str,status:&gtk::Label)->gtk::Box{
    let row=gtk::Box::new(gtk::Orientation::Horizontal,12);
    let labels=gtk::Box::new(gtk::Orientation::Vertical,2);labels.set_hexpand(true);
    let title_label=gtk::Label::new(Some(title));title_label.set_xalign(0.0);labels.append(&title_label);
    let note_label=gtk::Label::new(Some(note));note_label.set_wrap(true);note_label.set_xalign(0.0);note_label.add_css_class("messenger-muted");labels.append(&note_label);
    let switch=gtk::Switch::new();switch.set_active(settings::get(key,default));switch.set_valign(gtk::Align::Center);
    let owned_key=key.to_owned();let status=status.clone();
    switch.connect_state_set(move|_,value|{if let Err(message)=settings::set(&owned_key,value){status.set_text(&message);}gtk::glib::Propagation::Proceed});
    row.append(&labels);row.append(&switch);row
}

fn sound_row(event:&str,title:&str,note:&str,parent:&gtk::Window,status:&gtk::Label,
             test:&Rc<dyn Fn(String)>)->gtk::Box{
    let key=format!("sound_{event}");
    let row=gtk::Box::new(gtk::Orientation::Vertical,6);
    let labels=gtk::Box::new(gtk::Orientation::Vertical,2);
    let title_label=gtk::Label::new(Some(title));title_label.set_xalign(0.0);
    let note_label=gtk::Label::new(Some(note));note_label.set_wrap(true);note_label.set_xalign(0.0);note_label.add_css_class("messenger-muted");
    labels.append(&title_label);labels.append(&note_label);row.append(&labels);
    let current=gtk::Label::new(Some("Default chime"));current.set_xalign(0.0);current.add_css_class("messenger-muted");
    if let Some(path)=settings::get_string(&key){
        current.set_text(&format!("Custom: {}",std::path::Path::new(&path).file_name().and_then(|name|name.to_str()).unwrap_or(&path)));
    }
    row.append(&current);
    let buttons=gtk::Box::new(gtk::Orientation::Horizontal,8);
    let preview=gtk::Button::with_label("Test sound");
    let preview_event=event.to_owned();let preview_action=test.clone();
    preview.connect_clicked(move|_|preview_action(preview_event.clone()));
    let choose=gtk::Button::with_label("Choose sound…");
    let choose_key=key.clone();let choose_event=event.to_owned();let choose_current=current.clone();
    let choose_status=status.clone();let choose_action=test.clone();let choose_parent=parent.clone();
    choose.connect_clicked(move|_|{
        let chooser=gtk::FileChooserDialog::new(Some("Choose a sound"),Some(&choose_parent),gtk::FileChooserAction::Open,
            &[("Cancel",gtk::ResponseType::Cancel),("Use sound",gtk::ResponseType::Accept)]);
        let filter=gtk::FileFilter::new();filter.set_name(Some("Audio files"));
        for pattern in ["*.wav","*.ogg","*.oga","*.mp3","*.flac"]{filter.add_pattern(pattern);}
        chooser.add_filter(&filter);
        let key=choose_key.clone();let event=choose_event.clone();let current=choose_current.clone();
        let status=choose_status.clone();let action=choose_action.clone();
        chooser.connect_response(move|chooser,response|{
            if response==gtk::ResponseType::Accept{
                if let Some(path)=chooser.file().and_then(|file|file.path()){
                    match settings::set_string(&key,path.to_string_lossy().as_ref()){
                        Ok(())=>{current.set_text(&format!("Custom: {}",path.file_name().and_then(|name|name.to_str()).unwrap_or("selected file")));
                            status.set_text("Sound saved. Use Test sound to preview it.");action(event.clone());},
                        Err(message)=>status.set_text(&message),
                    }
                }
            }
            chooser.close();
        });
        chooser.show();
    });
    let reset=gtk::Button::with_label("Reset");
    let reset_key=key.clone();let reset_current=current.clone();let reset_status=status.clone();let reset_action=test.clone();let reset_event=event.to_owned();
    reset.connect_clicked(move|_|{
        match settings::set_string(&reset_key,""){
            Ok(())=>{reset_current.set_text("Default chime");reset_status.set_text("Default sound restored.");reset_action(reset_event.clone());},
            Err(message)=>reset_status.set_text(&message),
        }
    });
    for button in [&preview,&choose,&reset]{buttons.append(button);}
    row.append(&buttons);row
}

impl Preferences {
    pub fn new(parent:&gtk::ApplicationWindow,actions:Actions)->Self{
        let main:gtk::Window=parent.clone().upcast();
        let window=gtk::Window::builder().title("Shadow Messenger – Preferences").transient_for(parent).destroy_with_parent(true)
            .default_width(780).default_height(560).build();
        window.add_css_class("messenger-window");window.set_size_request(620,440);
        let root=gtk::Box::new(gtk::Orientation::Horizontal,0);
        let nav=gtk::ListBox::new();nav.set_selection_mode(gtk::SelectionMode::Single);nav.set_size_request(196,-1);nav.add_css_class("messenger-preferences-nav");
        let stack=gtk::Stack::new();stack.set_hexpand(true);stack.set_transition_type(gtk::StackTransitionType::Crossfade);
        let status=gtk::Label::new(None);status.set_xalign(0.0);status.set_wrap(true);status.set_margin_start(24);status.set_margin_end(24);status.set_margin_bottom(10);status.add_css_class("messenger-muted");
        let names=["General","Appearance","Notifications","Privacy & Security","Accounts","Advanced"];
        let keys=["general","appearance","notifications","privacy-security","accounts","advanced"];
        for (index,name) in names.iter().enumerate(){
            let label=gtk::Label::new(Some(name));label.set_xalign(0.0);label.set_margin_top(9);label.set_margin_bottom(9);label.set_margin_start(12);label.set_margin_end(12);
            let row=gtk::ListBoxRow::new();row.set_child(Some(&label));nav.append(&row);
            let _=index;
        }
        let nav_scroll=gtk::ScrolledWindow::builder().child(&nav).hscrollbar_policy(gtk::PolicyType::Never).build();nav_scroll.set_size_request(196,-1);
        root.append(&nav_scroll);root.append(&gtk::Separator::new(gtk::Orientation::Vertical));
        let body=gtk::Box::new(gtk::Orientation::Vertical,0);body.set_hexpand(true);body.append(&stack);
        body.append(&status);root.append(&body);window.set_child(Some(&root));
        let nav_stack=stack.clone();
        nav.connect_row_selected(move|_,row|{if let Some(row)=row{if let Some(name)=keys.get(row.index() as usize){nav_stack.set_visible_child_name(name);}}});

        let (general,general_content)=page("General");
        general_content.append(&toggle("auto_restore",false,"Restore my saved account at startup","The session is read from the desktop keyring and never stored in plain text.",&status));
        let hint=gtk::Label::new(Some("Shadow Messenger keeps one account per profile. Sign out to remove the saved session from this device."));hint.set_wrap(true);hint.set_xalign(0.0);hint.add_css_class("messenger-muted");general_content.append(&hint);
        add_page(&stack,&general,"general");

        let (appearance_page,appearance_content)=page("Appearance");
        let theme=gtk::Label::new(Some(&format!("Following ShadowRealm-OS: {}",appearance::current_label())));theme.set_xalign(0.0);theme.set_wrap(true);appearance_content.append(&theme);
        let note=gtk::Label::new(Some("Shadow Messenger uses the active desktop palette for windows, navigation, message bubbles and dialogs. Change the theme in Settings → Appearance; the messenger updates without a restart."));note.set_wrap(true);note.set_xalign(0.0);note.add_css_class("messenger-muted");appearance_content.append(&note);
        let reload=gtk::Button::with_label("Reload theme");let theme_copy=theme.clone();reload.connect_clicked(move|_|{appearance::refresh_now();theme_copy.set_text(&format!("Following ShadowRealm-OS: {}",appearance::current_label()));});
        reload.set_halign(gtk::Align::Start);appearance_content.append(&reload);
        add_page(&stack,&appearance_page,"appearance");

        let (notifications,notifications_content)=page("Notifications");
        notifications_content.append(&toggle("notifications",true,"Show desktop notifications","Messages from other people appear through the desktop notification service.",&status));
        notifications_content.append(&toggle("notification_previews",true,"Show message text in notifications","Turn this off to see only “New message”. Mention names stay private either way.",&status));
        notifications_content.append(&toggle("notification_sounds",true,"Play notification sounds","A short tone for messages and a brighter tone when you are mentioned.",&status));
        notifications_content.append(&toggle("presence_sounds",true,"Play sign-on and sign-off sounds","A quiet chime when an account connects or signs out.",&status));
        let test_row=gtk::Box::new(gtk::Orientation::Horizontal,8);
        let test_notification=gtk::Button::with_label("Send test notification");let action=actions.test_notification.clone();test_notification.connect_clicked(move|_|action());
        test_row.append(&test_notification);notifications_content.append(&test_row);
        let sound_note=gtk::Label::new(Some("Each event uses its own original chime. Choose a WAV, OGG, MP3 or FLAC file to replace it; Reset returns to the bundled sound. Volume follows the system output and mute."));
        sound_note.set_wrap(true);sound_note.set_xalign(0.0);sound_note.add_css_class("messenger-muted");notifications_content.append(&sound_note);
        for (event,title,note) in [
            ("message","New message","Played for a message in another conversation."),
            ("mention","Mention","Played when a message mentions you or your name."),
            ("sign-on","Sign-on","Played when an account connects."),
            ("sign-off","Sign-off","Played when an account signs out."),
        ]{
            notifications_content.append(&sound_row(event,title,note,&window,&status,&actions.test_sound));
        }
        let dnd=gtk::Label::new(Some("Do Not Disturb and Invisible suppress every alert and sound, including mentions. Activity still records what arrived."));dnd.set_wrap(true);dnd.set_xalign(0.0);dnd.add_css_class("messenger-muted");notifications_content.append(&dnd);
        add_page(&stack,&notifications,"notifications");

        let (privacy,privacy_content)=page("Privacy & Security");
        let privacy_note=gtk::Label::new(Some("Encrypted rooms use Matrix end-to-end encryption. Your password is used once for sign-in and is never saved. Session tokens and the local store key live in the desktop keyring."));privacy_note.set_wrap(true);privacy_note.set_xalign(0.0);privacy_note.add_css_class("messenger-muted");privacy_content.append(&privacy_note);
        let privacy_buttons=gtk::Box::new(gtk::Orientation::Horizontal,8);
        let security=gtk::Button::with_label("Devices & security");let action=actions.security.clone();security.connect_clicked(move|_|action());
        let recovery=gtk::Button::with_label("Account recovery");let action=actions.recovery.clone();recovery.connect_clicked(move|_|action());
        privacy_buttons.append(&security);privacy_buttons.append(&recovery);privacy_content.append(&privacy_buttons);
        add_page(&stack,&privacy,"privacy-security");

        let (accounts,accounts_content)=page("Accounts");
        let account=gtk::Label::new(Some("Not signed in"));account.set_xalign(0.0);account.set_wrap(true);accounts_content.append(&account);
        let account_note=gtk::Label::new(Some("Signing out removes the saved session and its local encryption key from the desktop keyring. Encrypted history remains on your homeserver."));account_note.set_wrap(true);account_note.set_xalign(0.0);account_note.add_css_class("messenger-muted");accounts_content.append(&account_note);
        let sign_out=gtk::Button::with_label("Sign out");sign_out.set_halign(gtk::Align::Start);let action=actions.logout.clone();sign_out.connect_clicked(move|_|action());accounts_content.append(&sign_out);
        add_page(&stack,&accounts,"accounts");

        let (advanced,advanced_content)=page("Advanced");
        let version=gtk::Label::new(Some(&format!("Development build {}",env!("CARGO_PKG_VERSION"))));version.set_xalign(0.0);advanced_content.append(&version);
        let development=gtk::Label::new(Some("This development build has working verification and recovery against the private fixture, but independent-client interoperability and the rest of the release checklist are still in progress. Do not use it for personal conversations."));development.set_wrap(true);development.set_xalign(0.0);development.add_css_class("messenger-muted");advanced_content.append(&development);
        let storage=gtk::Label::new(Some("Account data: ~/.local/share/shadow-messenger/accounts (private directory, SDK-encrypted store)."));storage.set_wrap(true);storage.set_xalign(0.0);storage.add_css_class("messenger-muted");advanced_content.append(&storage);
        add_page(&stack,&advanced,"advanced");

        if let Some(row)=nav.row_at_index(0){nav.select_row(Some(&row));}
        window.connect_close_request(|window|{window.hide();gtk::glib::Propagation::Stop});
        Self{window,main,nav,stack,account,theme,status}
    }
    /// Shows Preferences above `parent` (the active conversation when there is one).
    /// Attaching to that window keeps the settings reachable instead of letting a
    /// sibling chat window cover the controls.
    pub fn present_above(&self,parent:Option<&gtk::Window>,page:&str){
        if parent.is_some_and(|parent|parent==&self.window){self.window.present();}else{
            self.window.set_transient_for(Some(parent.unwrap_or(&self.main)));
            self.window.present();
        }
        self.select(page);
    }
    /// Returns the window to the main window when the chat it was attached to
    /// is hidden. The window stays open and usable.
    pub fn release_to_main(&self){
        if self.window.transient_for().as_ref()!=Some(&self.main){
            self.window.set_transient_for(Some(&self.main));
            if self.window.is_visible(){self.window.present();}
        }
    }
    pub fn window(&self)->&gtk::Window{&self.window}
    pub fn is_visible(&self)->bool{self.window.is_visible()}
    fn select(&self,page:&str){
        let names=["general","appearance","notifications","privacy-security","accounts","advanced"];
        if let Some(index)=names.iter().position(|name|*name==page){
            if let Some(row)=self.nav.row_at_index(index as i32){self.nav.select_row(Some(&row));}
        }
        if page=="appearance"{self.theme.set_text(&format!("Following ShadowRealm-OS: {}",appearance::current_label()));}
    }
    pub fn set_account(&self,account:&str){self.account.set_text(account);}
    #[allow(dead_code)]
    pub fn status(&self,message:&str){self.status.set_text(message);}
    #[allow(dead_code)]
    pub fn stack(&self)->&gtk::Stack{&self.stack}
}

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
    pub test_sound:Rc<dyn Fn()>,
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
        stack.add_named(&general,Some("general"));

        let (appearance_page,appearance_content)=page("Appearance");
        let theme=gtk::Label::new(Some(&format!("Following ShadowRealm-OS: {}",appearance::current_label())));theme.set_xalign(0.0);theme.set_wrap(true);appearance_content.append(&theme);
        let note=gtk::Label::new(Some("Shadow Messenger uses the active desktop palette for windows, navigation, message bubbles and dialogs. Change the theme in Settings → Appearance; the messenger updates without a restart."));note.set_wrap(true);note.set_xalign(0.0);note.add_css_class("messenger-muted");appearance_content.append(&note);
        let reload=gtk::Button::with_label("Reload theme");let theme_copy=theme.clone();reload.connect_clicked(move|_|{appearance::refresh_now();theme_copy.set_text(&format!("Following ShadowRealm-OS: {}",appearance::current_label()));});
        reload.set_halign(gtk::Align::Start);appearance_content.append(&reload);
        stack.add_named(&appearance_page,Some("appearance"));

        let (notifications,notifications_content)=page("Notifications");
        notifications_content.append(&toggle("notifications",true,"Show desktop notifications","Messages from other people appear through the desktop notification service.",&status));
        notifications_content.append(&toggle("notification_previews",true,"Show message text in notifications","Turn this off to see only “New message”. Mention names stay private either way.",&status));
        notifications_content.append(&toggle("notification_sounds",true,"Play notification sounds","A short tone for messages and a brighter tone when you are mentioned.",&status));
        notifications_content.append(&toggle("presence_sounds",true,"Play sign-on and sign-off sounds","A quiet chime when an account connects or signs out.",&status));
        let test_row=gtk::Box::new(gtk::Orientation::Horizontal,8);
        let test_notification=gtk::Button::with_label("Send test notification");let action=actions.test_notification.clone();test_notification.connect_clicked(move|_|action());
        let test_sound=gtk::Button::with_label("Play message sound");let action=actions.test_sound.clone();test_sound.connect_clicked(move|_|action());
        test_row.append(&test_notification);test_row.append(&test_sound);notifications_content.append(&test_row);
        let dnd=gtk::Label::new(Some("Do Not Disturb and Invisible suppress every alert and sound, including mentions. Activity still records what arrived."));dnd.set_wrap(true);dnd.set_xalign(0.0);dnd.add_css_class("messenger-muted");notifications_content.append(&dnd);
        stack.add_named(&notifications,Some("notifications"));

        let (privacy,privacy_content)=page("Privacy & Security");
        let privacy_note=gtk::Label::new(Some("Encrypted rooms use Matrix end-to-end encryption. Your password is used once for sign-in and is never saved. Session tokens and the local store key live in the desktop keyring."));privacy_note.set_wrap(true);privacy_note.set_xalign(0.0);privacy_note.add_css_class("messenger-muted");privacy_content.append(&privacy_note);
        let privacy_buttons=gtk::Box::new(gtk::Orientation::Horizontal,8);
        let security=gtk::Button::with_label("Devices & security");let action=actions.security.clone();security.connect_clicked(move|_|action());
        let recovery=gtk::Button::with_label("Account recovery");let action=actions.recovery.clone();recovery.connect_clicked(move|_|action());
        privacy_buttons.append(&security);privacy_buttons.append(&recovery);privacy_content.append(&privacy_buttons);
        stack.add_named(&privacy,Some("privacy-security"));

        let (accounts,accounts_content)=page("Accounts");
        let account=gtk::Label::new(Some("Not signed in"));account.set_xalign(0.0);account.set_wrap(true);accounts_content.append(&account);
        let account_note=gtk::Label::new(Some("Signing out removes the saved session and its local encryption key from the desktop keyring. Encrypted history remains on your homeserver."));account_note.set_wrap(true);account_note.set_xalign(0.0);account_note.add_css_class("messenger-muted");accounts_content.append(&account_note);
        let sign_out=gtk::Button::with_label("Sign out");sign_out.set_halign(gtk::Align::Start);let action=actions.logout.clone();sign_out.connect_clicked(move|_|action());accounts_content.append(&sign_out);
        stack.add_named(&accounts,Some("accounts"));

        let (advanced,advanced_content)=page("Advanced");
        let version=gtk::Label::new(Some(&format!("Development build {}",env!("CARGO_PKG_VERSION"))));version.set_xalign(0.0);advanced_content.append(&version);
        let development=gtk::Label::new(Some("This build is for testing. Verification, recovery and independent-client interoperability checks are still in progress; do not use it for personal conversations."));development.set_wrap(true);development.set_xalign(0.0);development.add_css_class("messenger-muted");advanced_content.append(&development);
        let storage=gtk::Label::new(Some("Account data: ~/.local/share/shadow-messenger/accounts (private directory, SDK-encrypted store)."));storage.set_wrap(true);storage.set_xalign(0.0);storage.add_css_class("messenger-muted");advanced_content.append(&storage);
        stack.add_named(&advanced,Some("advanced"));

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
    pub fn present(&self,page:&str){
        self.select(page);
        self.window.present();
    }
    pub fn set_account(&self,account:&str){self.account.set_text(account);}
    #[allow(dead_code)]
    pub fn status(&self,message:&str){self.status.set_text(message);}
    #[allow(dead_code)]
    pub fn stack(&self)->&gtk::Stack{&self.stack}
}

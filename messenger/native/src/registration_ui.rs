//! Account creation. Registration is a separate window so the sign-in card
//! stays usable on small displays, and so it follows the same transient-parent
//! rules as the other tool windows.
use async_channel::Sender;
use gtk::prelude::*;
use crate::worker::Command;

pub struct RegistrationView {
    window:gtk::Window,
    main:gtk::Window,
    server:gtk::Entry,
    user:gtk::Entry,
    password:gtk::PasswordEntry,
    confirm:gtk::PasswordEntry,
    token:gtk::Entry,
    create:gtk::Button,
    status:gtk::Label,
}

impl RegistrationView {
    pub fn new(parent:&gtk::ApplicationWindow,commands:Sender<Command>,homeserver:&str)->Self{
        let main:gtk::Window=parent.clone().upcast();
        let window=gtk::Window::builder().title("Create a Matrix account").transient_for(parent).destroy_with_parent(true).default_width(560).default_height(560).build();
        window.add_css_class("messenger-window");window.set_size_request(440,460);
        let outer=gtk::Box::new(gtk::Orientation::Vertical,10);outer.set_margin_top(20);outer.set_margin_bottom(20);outer.set_margin_start(22);outer.set_margin_end(22);
        let heading=gtk::Label::new(Some("Create a Matrix account"));heading.add_css_class("messenger-page-title");heading.set_xalign(0.0);outer.append(&heading);
        let note=gtk::Label::new(Some("Your provider must allow new accounts. If registration is disabled, or its form needs a captcha or terms page, create the account on the provider's website and sign in here."));note.set_wrap(true);note.set_xalign(0.0);note.add_css_class("messenger-muted");outer.append(&note);
        let server=gtk::Entry::builder().placeholder_text("HTTPS homeserver").text(homeserver).build();
        let user=gtk::Entry::builder().placeholder_text("Account name (without @ or the server)").build();
        let password=gtk::PasswordEntry::new();password.set_show_peek_icon(true);password.set_placeholder_text(Some("Choose a password (at least 8 characters)"));
        let confirm=gtk::PasswordEntry::new();confirm.set_show_peek_icon(true);confirm.set_placeholder_text(Some("Repeat the password"));
        let token=gtk::Entry::builder().placeholder_text("Registration token (only if your provider requires one)").build();
        for widget in [server.upcast_ref::<gtk::Widget>(),user.upcast_ref(),password.upcast_ref(),confirm.upcast_ref(),token.upcast_ref()]{outer.append(widget);}
        let create=gtk::Button::with_label("Create account");create.add_css_class("suggested-action");
        let status=gtk::Label::new(Some("The new session is stored in the desktop keyring."));status.set_wrap(true);status.set_xalign(0.0);status.add_css_class("messenger-muted");
        outer.append(&create);outer.append(&status);
        let scroll=gtk::ScrolledWindow::builder().child(&outer).hscrollbar_policy(gtk::PolicyType::Never).vscrollbar_policy(gtk::PolicyType::Automatic).build();
        window.set_child(Some(&scroll));
        let tx=commands.clone();let status_copy=status.clone();let server_copy=server.clone();let user_copy=user.clone();let password_copy=password.clone();let confirm_copy=confirm.clone();let token_copy=token.clone();
        create.connect_clicked(move|button|{
            if user_copy.text().trim().is_empty(){status_copy.set_text("Choose an account name for this homeserver.");return;}
            if password_copy.text().chars().count()<8{status_copy.set_text("Choose a password with at least 8 characters.");return;}
            if password_copy.text()!=confirm_copy.text(){status_copy.set_text("The passwords do not match.");return;}
            let token=token_copy.text().to_string();
            let command=Command::Register{server:server_copy.text().to_string(),username:user_copy.text().to_string(),password:zeroize::Zeroizing::new(password_copy.text().to_string()),token:(!token.trim().is_empty()).then(||zeroize::Zeroizing::new(token))};
            if tx.try_send(command).is_ok(){button.set_sensitive(false);status_copy.set_text("Creating the account and protecting the session with the desktop keyring...");}
            else{status_copy.set_text("An account request is already pending.");}
        });
        let password_copy=password.clone();let confirm_copy=confirm.clone();let status_copy=status.clone();
        window.connect_close_request(move|window|{password_copy.set_text("");confirm_copy.set_text("");status_copy.set_text("The new session is stored in the desktop keyring.");window.hide();gtk::glib::Propagation::Stop});
        Self{window,main,server,user,password,confirm,token,create,status}
    }
    pub fn present_above(&self,parent:Option<&gtk::Window>){
        if parent.is_some_and(|parent|parent==&self.window){self.window.present();}
        else{self.window.set_transient_for(Some(parent.unwrap_or(&self.main)));self.window.present();}
    }
    pub fn release_to_main(&self){
        if self.window.transient_for().as_ref()!=Some(&self.main){self.window.set_transient_for(Some(&self.main));if self.window.is_visible(){self.window.present();}}
    }
    pub fn set_homeserver(&self,homeserver:&str){if self.server.text().is_empty(){self.server.set_text(homeserver);}}
    pub fn succeeded(&self){
        self.password.set_text("");self.confirm.set_text("");self.token.set_text("");self.create.set_sensitive(true);
        self.status.set_text("Account created. Choose a conversation or start one.");self.window.hide();
    }
    pub fn failed(&self,message:&str){self.status.set_text(message);self.create.set_sensitive(true);if self.window.is_visible(){self.window.present();}}
    pub fn signed_out(&self){
        self.password.set_text("");self.confirm.set_text("");self.token.set_text("");self.user.set_text("");self.create.set_sensitive(true);
        self.status.set_text("The new session is stored in the desktop keyring.");self.window.hide();
    }
}

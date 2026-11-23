use std::{cell::Cell,rc::Rc};
use async_channel::Sender;
use gtk::prelude::*;
use zeroize::Zeroizing;
use crate::worker::Command;

pub struct RecoveryView {
    window:gtk::Window,
    status:gtk::Label,
    key:gtk::PasswordEntry,
    generated:gtk::PasswordEntry,
    saved:gtk::CheckButton,
    consent:gtk::CheckButton,
    create:gtk::Button,
    restore:gtk::Button,
    finish:gtk::Button,
    password:gtk::PasswordEntry,
    can_create:Rc<Cell<bool>>,
}
impl RecoveryView {
    pub fn new(parent:&gtk::ApplicationWindow,commands:Sender<Command>)->Self{
        let window=gtk::Window::builder().title("Account recovery").transient_for(parent).destroy_with_parent(true).default_width(630).default_height(560).build();
        window.add_css_class("messenger-window");
        let outer=gtk::Box::new(gtk::Orientation::Vertical,12);outer.set_margin_top(20);outer.set_margin_bottom(20);outer.set_margin_start(20);outer.set_margin_end(20);
        let intro=gtk::Label::new(Some("Your Matrix provider stores an encrypted backup of message keys. Your recovery key unlocks it. Keep the key outside this device; do not send it to anyone."));intro.set_wrap(true);intro.set_xalign(0.0);outer.append(&intro);
        let status=gtk::Label::new(Some("Checking account recovery..."));status.set_wrap(true);status.set_xalign(0.0);outer.append(&status);
        let label=gtk::Label::new(Some("Restore an existing recovery key"));label.set_xalign(0.0);outer.append(&label);
        let key=gtk::PasswordEntry::new();key.set_show_peek_icon(true);key.set_widget_name("recovery-existing-key");outer.append(&key);
        let restore=gtk::Button::with_label("Restore encrypted history");restore.set_sensitive(false);outer.append(&restore);
        let consent=gtk::CheckButton::with_label("Set up encrypted key backup for this account");outer.append(&consent);
        let label=gtk::Label::new(Some("Account password, only if your provider requires it for setup"));label.set_wrap(true);label.set_xalign(0.0);outer.append(&label);
        let password=gtk::PasswordEntry::new();password.set_show_peek_icon(true);password.set_widget_name("recovery-setup-password");outer.append(&password);
        let create=gtk::Button::with_label("Create recovery key");create.set_sensitive(false);outer.append(&create);
        let generated=gtk::PasswordEntry::new();generated.set_editable(false);generated.set_show_peek_icon(true);generated.set_widget_name("recovery-created-key");generated.set_visible(false);outer.append(&generated);
        let saved=gtk::CheckButton::with_label("I saved my recovery key somewhere safe");saved.set_visible(false);outer.append(&saved);
        let finish=gtk::Button::with_label("Clear displayed key");finish.set_visible(false);finish.set_sensitive(false);outer.append(&finish);
        let refresh=gtk::Button::with_label("Refresh recovery status");outer.append(&refresh);window.set_child(Some(&outer));
        let can_create=Rc::new(Cell::new(false));let allowed=can_create.clone();let button=create.clone();consent.connect_toggled(move|consent|button.set_sensitive(allowed.get()&&consent.is_active()));
        let button=restore.clone();key.connect_changed(move|key|button.set_sensitive(!key.text().trim().is_empty()));
        let tx=commands.clone();let entry=key.clone();let label=status.clone();restore.connect_clicked(move|button|{
            let value=Zeroizing::new(entry.text().to_string());entry.set_text("");
            if tx.try_send(Command::RestoreRecovery(value)).is_ok(){button.set_sensitive(false);label.set_text("Restoring account keys. Older encrypted messages will fetch their keys when opened.");}
            else{label.set_text("An account request is already pending. Enter the key again when it finishes.");}
        });
        let tx=commands.clone();let entry=password.clone();let label=status.clone();let allowed=can_create.clone();create.connect_clicked(move|button|{
            if !allowed.get(){return;}let value=Zeroizing::new(entry.text().to_string());entry.set_text("");let value=if value.is_empty(){None}else{Some(value)};
            if tx.try_send(Command::EnableRecovery(value)).is_ok(){button.set_sensitive(false);allowed.set(false);label.set_text("Creating encrypted recovery. Keep this window open until you save the key.");}
            else{label.set_text("An account request is already pending. Retry when it finishes.");}
        });
        let button=finish.clone();saved.connect_toggled(move|saved|button.set_sensitive(saved.is_active()));
        let entry=generated.clone();let saved_copy=saved.clone();finish.connect_clicked(move|button|{entry.set_text("");entry.set_visible(false);saved_copy.set_visible(false);button.set_visible(false);});
        let tx=commands;refresh.connect_clicked(move |_|{let _=tx.try_send(Command::RecoveryStatus);});
        let entry=generated.clone();let saved_copy=saved.clone();let label=status.clone();let private_key=key.clone();let private_password=password.clone();window.connect_close_request(move|window|{
            private_key.set_text("");private_password.set_text("");
            if !entry.text().is_empty()&&!saved_copy.is_active(){label.set_text("Save your recovery key and confirm it before closing. This key cannot be displayed again here.");return gtk::glib::Propagation::Stop;}
            entry.set_text("");entry.set_visible(false);saved_copy.set_visible(false);window.hide();gtk::glib::Propagation::Stop
        });
        let entries=[key.clone(),generated.clone(),password.clone()];window.connect_destroy(move |_|{for entry in &entries{entry.set_text("");}});
        Self{window,status,key,generated,saved,consent,create,restore,finish,password,can_create}
    }
    pub fn has_unsaved_key(&self)->bool{!self.generated.text().is_empty()&&!self.saved.is_active()}
    pub fn present(&self){self.window.present();}
    pub fn status(&self,message:&str,can_create:bool){self.status.set_text(message);self.can_create.set(can_create);self.create.set_sensitive(can_create&&self.consent.is_active());}
    pub fn error(&self,message:&str){if self.window.is_visible(){self.status.set_text(message);}}
    pub fn created(&self,key:Zeroizing<String>){
        self.generated.set_text(key.as_str());self.generated.set_visible(true);self.saved.set_active(false);self.saved.set_visible(true);
        self.finish.set_visible(true);self.finish.set_sensitive(false);
        self.status("Save this new recovery key now. Use the eye button to reveal it. Encrypted backup upload is being checked.",false);self.window.present();
    }
    pub fn restored(&self){self.status("Account recovery keys restored. Open a conversation to download the keys needed for its encrypted history.",false);}
    pub fn signed_out(&self){self.key.set_text("");self.generated.set_text("");self.generated.set_visible(false);self.password.set_text("");self.saved.set_active(false);self.saved.set_visible(false);self.finish.set_visible(false);self.finish.set_sensitive(false);self.consent.set_active(false);self.create.set_sensitive(false);self.restore.set_sensitive(false);self.can_create.set(false);self.window.hide();}
}

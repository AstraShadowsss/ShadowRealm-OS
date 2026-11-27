use async_channel::Sender;
use gtk::prelude::*;
use crate::{worker::Command,conversations::Invitation};

pub struct ConversationsView {
    window:gtk::Window,main:gtk::Window,list:gtk::Box,status:gtk::Label,name:gtk::Entry,people:gtk::Entry,create:gtk::Button,commands:Sender<Command>,
}
impl ConversationsView {
    pub fn new(parent:&gtk::ApplicationWindow,commands:Sender<Command>)->Self{
        let main:gtk::Window=parent.clone().upcast();
        let window=gtk::Window::builder().title("Conversations & invitations").transient_for(parent).destroy_with_parent(true).default_width(650).default_height(560).build();
        window.add_css_class("messenger-window");
        let outer=gtk::Box::new(gtk::Orientation::Vertical,12);outer.set_margin_top(20);outer.set_margin_bottom(20);outer.set_margin_start(20);outer.set_margin_end(20);
        let heading=gtk::Label::new(Some("Invitations"));heading.set_xalign(0.0);heading.add_css_class("heading");outer.append(&heading);
        let list=gtk::Box::new(gtk::Orientation::Vertical,10);let scroll=gtk::ScrolledWindow::builder().child(&list).min_content_height(130).vexpand(true).build();outer.append(&scroll);
        let refresh=gtk::Button::with_label("Refresh invitations");outer.append(&refresh);
        outer.append(&gtk::Separator::new(gtk::Orientation::Horizontal));
        let heading=gtk::Label::new(Some("Start an encrypted conversation"));heading.set_xalign(0.0);heading.add_css_class("heading");outer.append(&heading);
        let name=gtk::Entry::builder().placeholder_text("Conversation name (optional)").max_length(80).build();outer.append(&name);
        let people=gtk::Entry::builder().placeholder_text("Matrix addresses, separated by commas").build();outer.append(&people);
        let note=gtk::Label::new(Some("Use full addresses, such as @name:provider.example. One person starts a direct conversation; several people start a private group. Encryption is confirmed before invitations are sent."));note.set_xalign(0.0);note.set_wrap(true);outer.append(&note);
        let create=gtk::Button::with_label("Create encrypted conversation");outer.append(&create);
        let status=gtk::Label::new(Some("Only accept invitations you expect. Joining shares your membership with the room."));status.set_xalign(0.0);status.set_wrap(true);outer.append(&status);window.set_child(Some(&outer));
        let tx=commands.clone();let name_copy=name.clone();let people_copy=people.clone();let label=status.clone();create.connect_clicked(move|button|{
            if tx.try_send(Command::CreateConversation{name:name_copy.text().to_string(),people:people_copy.text().to_string()}).is_ok(){button.set_sensitive(false);label.set_text("Creating a private conversation and confirming encryption...");}else{label.set_text("An account request is already pending. Your entries were kept.");}
        });
        let tx=commands.clone();refresh.connect_clicked(move |_|{let _=tx.try_send(Command::Invitations);});
        window.connect_close_request(|window|{window.hide();gtk::glib::Propagation::Stop});
        Self{window,main,list,status,name,people,create,commands}
    }
    pub fn present_above(&self,parent:Option<&gtk::Window>){
        if parent.is_some_and(|parent|parent==&self.window){self.window.present();}
        else{self.window.set_transient_for(Some(parent.unwrap_or(&self.main)));self.window.present();}
    }
    pub fn release_to_main(&self){
        if self.window.transient_for().as_ref()!=Some(&self.main){self.window.set_transient_for(Some(&self.main));if self.window.is_visible(){self.window.present();}}
    }
    pub fn invitations(&self,invites:Vec<Invitation>){
        while let Some(child)=self.list.first_child(){self.list.remove(&child);}
        if invites.is_empty(){let label=gtk::Label::new(Some("No pending invitations"));label.set_xalign(0.0);self.list.append(&label);}
        for invitation in invites{
            let row=gtk::Box::new(gtk::Orientation::Vertical,6);let label=gtk::Label::new(Some(&format!("{}\nFrom {}",invitation.name,invitation.inviter)));label.set_xalign(0.0);label.set_wrap(true);label.set_tooltip_text(Some(&invitation.room_id));row.append(&label);
            let buttons=gtk::Box::new(gtk::Orientation::Horizontal,8);
            for (text,accept) in [("Accept invitation",true),("Decline invitation",false)]{
                let button=gtk::Button::with_label(text);let id=invitation.room_id.clone();let tx=self.commands.clone();let status=self.status.clone();button.connect_clicked(move|button|{if tx.try_send(Command::RespondInvitation{room_id:id.clone(),accept}).is_ok(){button.set_sensitive(false);status.set_text("Updating invitation...");}else{status.set_text("An account request is already pending. Retry when it finishes.");}});buttons.append(&button);
            }row.append(&buttons);self.list.append(&row);
        }
    }
    pub fn action(&self,message:&str){self.status.set_text(message);self.create.set_sensitive(true);}
    pub fn created(&self,message:&str){self.action(message);self.name.set_text("");self.people.set_text("");}
    pub fn error(&self,message:&str){if self.window.is_visible(){self.action(message);}}
    pub fn signed_out(&self){self.name.set_text("");self.people.set_text("");self.create.set_sensitive(true);while let Some(child)=self.list.first_child(){self.list.remove(&child);}self.window.hide();}
}

use std::{cell::{RefCell,Cell},rc::Rc};
use gtk::prelude::*;
use async_channel::Sender;
use crate::{worker::Command,verification::{DeviceInfo,State}};

pub struct SecurityView {
    window:gtk::Window,
    list:gtk::Box,
    account:gtk::Label,
    status:gtk::Label,
    numbers:gtk::Label,
    confirm:gtk::Button,
    accept:gtk::Button,
    cancel:gtk::Button,
    flow:Rc<RefCell<Option<String>>>,
    confirmed:Rc<Cell<bool>>,
    commands:Sender<Command>,
}
impl SecurityView {
    pub fn new(parent:&gtk::ApplicationWindow,commands:Sender<Command>)->Self{
        let window=gtk::Window::builder().title("Devices & security").transient_for(parent).destroy_with_parent(true).default_width(620).default_height(520).build();
        let outer=gtk::Box::new(gtk::Orientation::Vertical,12);for setter in [gtk::Widget::set_margin_top,gtk::Widget::set_margin_bottom,gtk::Widget::set_margin_start,gtk::Widget::set_margin_end]{setter(outer.upcast_ref(),20);}
        let account=gtk::Label::new(Some("Loading account devices..."));account.set_xalign(0.0);account.set_wrap(true);outer.append(&account);
        let list=gtk::Box::new(gtk::Orientation::Vertical,8);let scroll=gtk::ScrolledWindow::builder().vexpand(true).child(&list).build();outer.append(&scroll);
        let status=gtk::Label::new(Some("Choose another device. Compare all three numbers on both devices before confirming."));status.set_wrap(true);status.set_xalign(0.0);outer.append(&status);
        let numbers=gtk::Label::new(None);numbers.add_css_class("title-1");numbers.set_selectable(true);outer.append(&numbers);
        let accept=gtk::Button::with_label("Accept verification");accept.set_visible(false);
        let buttons=gtk::Box::new(gtk::Orientation::Horizontal,8);let confirm=gtk::Button::with_label("Numbers match");confirm.set_sensitive(false);let cancel=gtk::Button::with_label("Cancel verification");cancel.set_sensitive(false);let refresh=gtk::Button::with_label("Refresh devices");for button in [&accept,&confirm,&cancel,&refresh]{buttons.append(button);}outer.append(&buttons);
        let note=gtk::Label::new(Some("Accept only a request you expect. Compare the numbers on both devices; never confirm a mismatch. Recovery controls are still in development."));note.set_wrap(true);note.set_xalign(0.0);outer.append(&note);window.set_child(Some(&outer));
        let flow=Rc::new(RefCell::new(None::<String>));let confirmed=Rc::new(Cell::new(false));
        let id=flow.clone();let tx=commands.clone();accept.connect_clicked(move|button|{if let Some(id)=id.borrow().clone(){if tx.try_send(Command::AcceptVerification(id)).is_ok(){button.set_sensitive(false);}}});
        let id=flow.clone();let tx=commands.clone();let done=confirmed.clone();let label=status.clone();confirm.connect_clicked(move|button|{if let Some(id)=id.borrow().clone(){if tx.try_send(Command::ConfirmVerification(id)).is_ok(){done.set(true);button.set_sensitive(false);label.set_text("Match confirmed here. Confirm on the other device to finish.");}}});
        let id=flow.clone();let tx=commands.clone();cancel.connect_clicked(move |_|{if let Some(id)=id.borrow().clone(){let _=tx.try_send(Command::CancelVerification(id));}});
        let tx=commands.clone();refresh.connect_clicked(move |_|{let _=tx.try_send(Command::Devices);});
        let id=flow.clone();let tx=commands.clone();window.connect_close_request(move|window|{if let Some(id)=id.borrow().clone(){let _=tx.try_send(Command::CancelVerification(id));}window.hide();gtk::glib::Propagation::Stop});
        Self{window,list,account,status,numbers,confirm,accept,cancel,flow,confirmed,commands}
    }
    pub fn signed_out(&self){self.window.hide();self.numbers.set_text("");self.accept.set_visible(false);self.confirm.set_sensitive(false);self.cancel.set_sensitive(false);self.list.set_sensitive(true);*self.flow.borrow_mut()=None;self.confirmed.set(false);while let Some(child)=self.list.first_child(){self.list.remove(&child);}}
    pub fn present(&self){self.window.present();}
    pub fn error(&self,message:&str){if self.window.is_visible(){self.status.set_text(message);}}
    pub fn devices(&self,user:&str,devices:Vec<DeviceInfo>){
        self.account.set_text(user);while let Some(child)=self.list.first_child(){self.list.remove(&child);}
        for device in devices{
            let row=gtk::Box::new(gtk::Orientation::Horizontal,10);let state=if device.current{"This device"}else if device.verified{"Verified"}else{"Not verified"};
            let label=gtk::Label::new(Some(&format!("{}\n{} · {}",device.name,device.id,state)));label.set_wrap(true);label.set_xalign(0.0);label.set_hexpand(true);row.append(&label);
            let verify=gtk::Button::with_label("Verify");verify.set_sensitive(!device.current);let tx=self.commands.clone();let user=user.to_owned();verify.connect_clicked(move |_|{let _=tx.try_send(Command::VerifyDevice{user_id:user.clone(),device_id:device.id.clone()});});row.append(&verify);self.list.append(&row);
        }
    }
    pub fn verification(&self,id:String,state:State){
        if self.flow.borrow().as_deref()!=Some(id.as_str()){self.confirmed.set(false);}*self.flow.borrow_mut()=Some(id);
        self.confirm.set_sensitive(false);self.cancel.set_sensitive(true);self.list.set_sensitive(false);
        self.accept.set_visible(false);
        match state{
            State::Requested{user,device}=>{self.numbers.set_text("");self.status.set_text(&format!("Verification requested by {user}, device {device}. Accept only if you started this on your other device."));self.accept.set_visible(true);self.accept.set_sensitive(true);self.window.present();}
            State::Waiting=>{self.numbers.set_text("");self.status.set_text("Waiting for the other device to accept...");}
            State::Ready=>{self.status.set_text("Preparing the comparison numbers...");}
            State::Compare((a,b,c))=>{self.numbers.set_text(&format!("{a}   {b}   {c}"));self.confirm.set_sensitive(!self.confirmed.get());self.status.set_text(if self.confirmed.get(){"Match confirmed here. Confirm on the other device to finish."}else{"Compare all three numbers on both devices. Cancel if any number differs."});}
            State::Verified=>{self.status.set_text("Device verified.");self.numbers.set_text("");self.cancel.set_sensitive(false);self.list.set_sensitive(true);*self.flow.borrow_mut()=None;}
            State::Cancelled=>{self.status.set_text("Verification cancelled. This action did not establish trust.");self.numbers.set_text("");self.cancel.set_sensitive(false);self.list.set_sensitive(true);*self.flow.borrow_mut()=None;}
        }
    }
}

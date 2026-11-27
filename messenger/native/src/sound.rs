//! Original short notification tones, played through GTK's media backend.
//! Audio is best-effort: a missing GStreamer plugin must never interrupt messaging.
use std::{cell::RefCell,fs,path::PathBuf};
use gtk::prelude::*;

thread_local! {
    static PLAYERS:RefCell<Vec<gtk::MediaFile>>=const{RefCell::new(Vec::new())};
}

const MESSAGE:&[u8]=include_bytes!("../assets/message.wav");
const MENTION:&[u8]=include_bytes!("../assets/mention.wav");
const SIGN_ON:&[u8]=include_bytes!("../assets/sign-on.wav");
const SIGN_OFF:&[u8]=include_bytes!("../assets/sign-off.wav");

fn bytes(name:&str)->Option<&'static [u8]>{
    match name{"message"=>Some(MESSAGE),"mention"=>Some(MENTION),"sign-on"=>Some(SIGN_ON),"sign-off"=>Some(SIGN_OFF),_=>None}
}
fn cache_path(name:&str)->Option<PathBuf>{
    let home=std::env::var_os("XDG_CACHE_HOME").map(PathBuf::from).filter(|path|path.is_absolute())
        .or_else(||std::env::var_os("HOME").map(PathBuf::from).filter(|path|path.is_absolute()).map(|path|path.join(".cache")))?;
    Some(home.join("shadow-messenger/sounds").join(format!("{name}.wav")))
}
fn prepare(name:&str)->Option<PathBuf>{
    let data=bytes(name)?;let path=cache_path(name)?;
    if fs::read(&path).ok().as_deref()==Some(data){return Some(path);}
    let directory=path.parent()?;
    fs::create_dir_all(directory).ok()?;
    let temporary=directory.join(format!("{name}.wav.new"));
    fs::write(&temporary,data).ok()?;
    fs::rename(temporary,&path).ok()?;
    Some(path)
}

/// Plays one named tone on the GTK main thread. Unknown names are ignored.
pub fn play(name:&str){
    let Some(path)=prepare(name) else{return};
    let media=gtk::MediaFile::for_filename(&path);
    media.set_volume(0.55);
    media.play();
    PLAYERS.with(|players|{
        let mut players=players.borrow_mut();
        players.retain(|media|media.is_playing());
        players.push(media);
    });
}

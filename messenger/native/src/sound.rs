//! Original short notification tones. Playback is best-effort: a missing
//! audio server or file must never interrupt messaging.
use std::{cell::RefCell,fs,path::{Path,PathBuf},process::{Command,Stdio}};
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
fn custom(name:&str)->Option<PathBuf>{
    let path=PathBuf::from(crate::settings::get_string(&format!("sound_{name}"))?);
    (path.is_file()&&path.metadata().ok()?.len()>0).then_some(path)
}
fn fallback_media(path:&Path){
    let media=gtk::MediaFile::for_filename(path);
    media.set_volume(0.55);
    media.play();
    PLAYERS.with(|players|{
        let mut players=players.borrow_mut();
        players.retain(|media|media.is_playing());
        players.push(media);
    });
}
fn play_path(path:&Path){
    // GTK's media backend is optional on minimal installs. paplay is present
    // with the desktop's PulseAudio/PipeWire stack and reports asynchronous
    // playback reliably; pw-play is the fallback for PipeWire-only systems.
    let volume=((0.90*65536.0) as u32).to_string();
    for (program,args) in [
        ("/usr/bin/paplay",vec![format!("--volume={volume}")]),
        ("/usr/bin/pw-play",vec!["--volume=0.55".to_owned()]),
    ]{
        if !Path::new(program).is_file(){continue;}
        let spawned=Command::new(program).args(args).arg(path)
            .stdin(Stdio::null()).stdout(Stdio::null()).stderr(Stdio::null()).spawn();
        if let Ok(mut child)=spawned{
            // Reap the short-lived player so repeated alerts cannot accumulate
            // zombie processes behind the long-running messenger.
            std::thread::spawn(move||{let _=child.wait();});
            return;
        }
    }
    fallback_media(path);
}

/// Plays one named event, preferring a user-selected file over the bundled
/// chime. Unknown names are ignored.
pub fn play(name:&str){
    let Some(path)=custom(name).or_else(||prepare(name)) else{return};
    play_path(&path);
}

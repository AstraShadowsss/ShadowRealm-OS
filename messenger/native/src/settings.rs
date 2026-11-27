//! Small non-secret preferences. Never stores credentials or message content.
use std::{fs,path::PathBuf};

fn config_dir()->Option<PathBuf>{
    std::env::var_os("XDG_CONFIG_HOME").map(PathBuf::from).filter(|path|path.is_absolute())
        .or_else(||std::env::var_os("HOME").map(PathBuf::from).filter(|path|path.is_absolute()).map(|path|path.join(".config")))
        .map(|path|path.join("shadow-messenger"))
}
fn path()->Option<PathBuf>{config_dir().map(|directory|directory.join("preferences.json"))}
fn read()->serde_json::Map<String,serde_json::Value>{
    let Some(path)=path() else{return Default::default()};
    let Ok(data)=fs::read(&path) else{return Default::default()};
    if data.len()>16_384{return Default::default();}
    serde_json::from_slice::<serde_json::Value>(&data).ok()
        .and_then(|value|value.as_object().cloned()).unwrap_or_default()
}

pub fn get(key:&str,default:bool)->bool{
    read().get(key).and_then(serde_json::Value::as_bool).unwrap_or(default)
}

pub fn set(key:&str,value:bool)->Result<(),String>{
    let Some(directory)=config_dir() else{return Err("The preferences directory is unavailable.".into())};
    fs::create_dir_all(&directory).map_err(|_|"The preferences directory could not be created.")?;
    let Some(path)=path() else{return Err("The preferences directory is unavailable.".into())};
    let mut values=read();values.insert(key.into(),serde_json::Value::Bool(value));
    let json=serde_json::to_vec_pretty(&serde_json::Value::Object(values)).map_err(|_|"Preferences could not be saved.")?;
    let temporary=directory.join("preferences.json.new");
    fs::write(&temporary,json).map_err(|_|"Preferences could not be saved.")?;
    fs::rename(temporary,&path).map_err(|_|"Preferences could not be saved.")?;
    Ok(())
}

pub fn get_string(key:&str)->Option<String>{
    read().get(key).and_then(serde_json::Value::as_str)
        .filter(|value|!value.trim().is_empty()).map(str::to_owned)
}

/// Stores a user preference string. An empty value removes the entry so the
/// bundled default is used again.
pub fn set_string(key:&str,value:&str)->Result<(),String>{
    let Some(directory)=config_dir() else{return Err("The preferences directory is unavailable.".into())};
    fs::create_dir_all(&directory).map_err(|_|"The preferences directory could not be created.")?;
    let Some(path)=path() else{return Err("The preferences directory is unavailable.".into())};
    let mut values=read();
    if value.trim().is_empty(){values.remove(key);}
    else{
        if value.len()>4096{return Err("That sound path is too long.".into());}
        values.insert(key.into(),serde_json::Value::String(value.to_owned()));
    }
    let json=serde_json::to_vec_pretty(&serde_json::Value::Object(values)).map_err(|_|"Preferences could not be saved.")?;
    let temporary=directory.join("preferences.json.new");
    fs::write(&temporary,json).map_err(|_|"Preferences could not be saved.")?;
    fs::rename(temporary,&path).map_err(|_|"Preferences could not be saved.")?;
    Ok(())
}

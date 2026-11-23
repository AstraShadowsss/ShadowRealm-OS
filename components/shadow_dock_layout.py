"""Full-width dock shelf using native, expanding Xfce separators."""
from pathlib import Path
import configparser,json,os,subprocess

STATE=Path.home()/'.config/shadowrealm-os/dock-layout.json'
PANEL='/panels/panel-2/'

def query(prop):
    result=subprocess.run(['xfconf-query','-c','xfce4-panel','-p',prop],capture_output=True,text=True,timeout=5)
    return result.stdout.strip() if result.returncode==0 else None

def put(prop,kind,value):
    values=value if isinstance(value,list) else [value]
    args=['xfconf-query','-c','xfce4-panel','-p',prop,'--create']
    if isinstance(value,list):args+=['--force-array']
    for item in values:args+=['--type',kind,'--set',str(item).lower() if isinstance(item,bool) else str(item)]
    subprocess.run(args,capture_output=True,text=True,timeout=5,check=True)

def state():
    try:return json.loads(STATE.read_text())
    except (OSError,ValueError):return {}

def save(record):
    STATE.parent.mkdir(parents=True,exist_ok=True)
    temp=STATE.with_suffix('.new');temp.write_text(json.dumps(record,indent=2)+'\n');os.replace(temp,STATE)

def raw_items():return [int(x) for x in (query(PANEL+'plugin-ids') or '').splitlines() if x.isdigit()]
def shelf_enabled():return state().get('shelf',False)
def user_items():
    spacers=state().get('spacers',[])
    return [item for item in raw_items() if item not in spacers]

def set_items(items):
    record=state();spacers=record.get('spacers',[])
    put(PANEL+'plugin-ids','int',[spacers[0],*items,spacers[1]] if record.get('shelf') and len(spacers)==2 else items)

def opacity(value):
    from shadow_effects import panel_opacity
    panel_opacity(2,value)
    path=STATE.parent/'transparency.ini';config=configparser.ConfigParser();config.read(path)
    if not config.has_section('Appearance'):config.add_section('Appearance')
    config.set('Appearance','dock-opacity',str(value))
    temp=path.with_suffix('.new')
    with temp.open('w') as stream:config.write(stream)
    os.replace(temp,path)

def current_opacity():
    config=configparser.ConfigParser();config.read(STATE.parent/'transparency.ini')
    return config.getint('Appearance','dock-opacity',fallback=100)

def apply_shelf(enabled):
    record=state();items=user_items()
    if not items:raise RuntimeError('The dock has no items in this session.')
    if enabled:
        if not record.get('shelf'):
            record={'shelf':True,'compact':{'length':float(query(PANEL+'length') or 1),'adjust':query(PANEL+'length-adjust')!='false','opacity':current_opacity()}}
            # Allocate unused plugin IDs; never repurpose a user's separator.
            ids=[]
            for line in subprocess.check_output(['xfconf-query','-c','xfce4-panel','-l'],text=True,timeout=5).splitlines():
                token=line.removeprefix('/plugins/plugin-').split('/')[0]
                if token.isdigit():ids.append(int(token))
            first=max(ids+[0])+1;record['spacers']=[first,first+1];save(record)
        for ident in record['spacers']:
            put(f'/plugins/plugin-{ident}','string','separator')
            put(f'/plugins/plugin-{ident}/expand','bool',True)
            put(f'/plugins/plugin-{ident}/style','uint',0)
        put(PANEL+'length','double',100);put(PANEL+'length-adjust','bool',False)
        set_items(items)
        if current_opacity()==0:opacity(88)
    elif record.get('shelf'):
        previous=record.get('compact',{});record['shelf']=False;save(record)
        set_items(items)
        put(PANEL+'length','double',previous.get('length',1));put(PANEL+'length-adjust','bool',previous.get('adjust',True))
        if current_opacity()==88:opacity(previous.get('opacity',0))
    # Recreate providers after their initial expansion properties are configured.
    subprocess.run(['xfce4-panel','--restart'],capture_output=True,timeout=15,check=True)
    return enabled

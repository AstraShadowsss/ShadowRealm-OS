"""Generate the fresh-profile XFCE panel defaults."""
import xml.etree.ElementTree as ET

LAUNCHERS = {
    1: ("Menu \u25be", "shadowrealm-os-desktop menu", "shadow-menu"),
    13: ("Terminal", "shadowrealm-os-desktop terminal", "orbital-dock-terminal"),
    14: ("Files", "shadowrealm-os-desktop files", "orbital-dock-files"),
    15: ("Browser", "shadowrealm-os-desktop browser", "orbital-dock-browser"),
    16: ("Shadow Control Center", "shadowrealm-os-desktop control-center", "orbital-dock-control-center"),
    19: ("Task Manager", "xfce4-taskmanager", "orbital-dock-task-manager"),
    20: ("Shadow Shield", "shadowrealm-os-desktop shield", "orbital-dock-shield"),
    23: ("Bluetooth", "shadowrealm-os-desktop bluetooth", "shadow-panel-bluetooth"),
}


def property_node(parent, name, kind, value=None):
    args = {"name": name, "type": kind}
    if value is not None:
        args["value"] = str(value)
    return ET.SubElement(parent, "property", args)


def array(parent, name, kind, values):
    prop = property_node(parent, name, "array")
    for value in values:
        ET.SubElement(prop, "value", type=kind, value=str(value))


def seed_panel(root):
    config = root / "etc/skel/.config/xfce4"
    panels = ET.Element("channel", name="xfce4-panel", version="1.0")
    property_node(panels, "configver", "int", 2)
    group = property_node(panels, "panels", "array")
    for ident in (1, 2):
        ET.SubElement(group, "value", type="int", value=str(ident))
    for ident, size, position, plugins in (
        (1, 30, "p=6;x=0;y=0", (1,4,5,2,3,8,25,6,24,23,9,10)),
        (2, 54, "p=10;x=0;y=0", (12,13,14,15,16,20,19,18,11)),
    ):
        panel = property_node(group, f"panel-{ident}", "empty")
        property_node(panel,"position","string",position)
        property_node(panel,"position-locked","bool","true")
        property_node(panel,"length","double",100 if ident == 1 else 1)
        property_node(panel,"length-adjust","bool","true")
        property_node(panel,"size","uint",size)
        property_node(panel,"background-style","int",1)
        array(panel,"background-rgba","double",(0.031372549,0.02745098,0.062745098,0.5 if ident == 1 else 0))
        array(panel,"plugin-ids","int",plugins)
    plugins = property_node(panels,"plugins","empty")
    for ident, (name, command, icon) in LAUNCHERS.items():
        launcher = property_node(plugins,f"plugin-{ident}","string","launcher")
        array(launcher,"items","string",["shadow.desktop"])
        if ident == 1:
            property_node(launcher,"show-label","bool","true")
        path = config/f"panel/launcher-{ident}/shadow.desktop"
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(f"[Desktop Entry]\nType=Application\nName={name}\nExec={command}\nIcon=shadowrealm-os-release-{icon}\nTerminal=false\n")
    for ident,kind in ((2,"tasklist"),(3,"separator"),(4,"pager"),(5,"separator"),(6,"systray"),(9,"separator"),(11,"separator"),(12,"separator"),(18,"applicationsmenu"),
                       (8,"clock"),(10,"actions"),(24,"pulseaudio"),(25,"separator")):
        prop = property_node(plugins,f"plugin-{ident}","string",kind)
        if kind == "separator" and ident in (3,25):
            property_node(prop,"expand","bool","true")
            property_node(prop,"style","uint",0)
        if kind == "applicationsmenu":
            property_node(prop,"button-icon","string","shadow-dock-launcher")
            property_node(prop,"button-title","string","")
            property_node(prop,"small","bool","false")
        if kind == "actions":
            property_node(prop,"appearance","uint",0)
            array(prop,"items","string",("+lock-screen","+switch-user","+separator","-suspend","-hibernate","-hybrid-sleep","-separator","+shutdown","+restart","+separator","+logout","-logout-dialog"))
        if kind == "clock":
            property_node(prop,"command","string","gnome-clocks")
            property_node(prop,"mode","uint",2)
            property_node(prop,"digital-time-format","string","%-I:%M %p")
            property_node(prop,"digital-date-format","string","%B %d, %Y")
            property_node(prop,"digital-date-font","string","DejaVu Sans Bold Italic 8")
            property_node(prop,"digital-time-font","string","Serif Bold 12")
            property_node(prop,"digital-layout","uint",3)
        if kind == "pager":
            property_node(prop,"miniature-view","bool","false")
        if kind == "pulseaudio":
            property_node(prop,"mixer-command","string","shadowrealm-os-desktop audio")
    path = config/"xfconf/xfce-perchannel-xml/xfce4-panel.xml"
    path.parent.mkdir(parents=True,exist_ok=True)
    ET.indent(panels)
    ET.ElementTree(panels).write(path,encoding="utf-8",xml_declaration=True)

    window_manager = ET.Element("channel", name="xfwm4", version="1.0")
    general = property_node(window_manager, "general", "empty")
    property_node(general, "workspace_count", "int", 4)
    array(general, "workspace_names", "string", ("1", "2", "3", "4"))
    ET.indent(window_manager)
    ET.ElementTree(window_manager).write(path.with_name("xfwm4.xml"), encoding="utf-8", xml_declaration=True)

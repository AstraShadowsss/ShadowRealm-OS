"""DNS and VPN controls for the ShadowRealm-OS network panels."""
import ipaddress
import os
import re
import secrets
import socket
import struct
import subprocess

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gio, Gtk

LOCAL_PROXY = "127.0.2.1"
DNS_FIELDS = ("ipv4.ignore-auto-dns", "ipv4.dns", "ipv6.ignore-auto-dns", "ipv6.dns")
VPN_TYPES = {"vpn", "wireguard"}


def nm(*args, timeout=45):
    result = subprocess.run(
        ["/usr/bin/nmcli", "--colors", "no", *args],
        capture_output=True, text=True, timeout=timeout,
        env=os.environ | {"LC_ALL": "C"})
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "NetworkManager rejected the change.")
    return result.stdout.rstrip("\n")


def split_fields(line):
    return [re.sub(r"\\(.)", r"\1", item)
            for item in re.split(r"(?<!\\):", line)]


def profiles(active=False):
    args = ("--active",) if active else ()
    return [split_fields(line) for line in
            nm("-t", "-f", "UUID,NAME,TYPE,DEVICE", "connection", "show", *args).splitlines()]


def active_profile(device):
    uuid = nm("-g", "GENERAL.CON-UUID", "device", "show", device)
    if not re.fullmatch(r"[0-9a-fA-F-]{36}", uuid):
        raise RuntimeError("Select an active wired or Wi-Fi connection.")
    return uuid


def read_dns(uuid):
    result = subprocess.run(["/usr/bin/nmcli", "--escape", "no", "-g", ",".join(DNS_FIELDS), "connection",
                             "show", "uuid", uuid], capture_output=True, text=True, timeout=8)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "Could not read the connection.")
    values = result.stdout.splitlines()
    if len(values) != len(DNS_FIELDS):
        raise RuntimeError("Unexpected response from NetworkManager.")
    return tuple(values)


def addresses(value, family):
    result = []
    for token in re.split(r"[,\s]+", value.strip()):
        if not token:
            continue
        try:
            address = ipaddress.ip_address(token)
            if address.version != family or address.is_unspecified or address.is_multicast or "%" in token:
                raise ValueError
        except ValueError:
            raise ValueError(f"'{token}' is not a usable IPv{family} DNS address.") from None
        if str(address) not in result:
            result.append(str(address))
    if len(result) > 3:
        raise ValueError("Enter up to three addresses per family.")
    return result


def dns_query(server, timeout=2.5):
    family = socket.AF_INET6 if ":" in server else socket.AF_INET
    tx = secrets.randbelow(65536)
    data = struct.pack("!6H", tx, 0x100, 1, 0, 0, 0)
    data += b"\x07example\x03com\x00\x00\x01\x00\x01"
    with socket.socket(family, socket.SOCK_DGRAM) as sock:
        sock.settimeout(timeout)
        sock.connect((server, 53))
        sock.send(data)
        reply = sock.recv(4096)
    if len(reply) < 12:
        raise RuntimeError(f"{server} returned an incomplete DNS response.")
    response_tx, flags, _, answers, _, _ = struct.unpack("!6H", reply[:12])
    if response_tx != tx or not flags & 0x8000 or flags & 0x000F or not answers:
        raise RuntimeError(f"{server} did not resolve the test name.")


def change_dns(device, mode, v4, v6):
    uuid = active_profile(device)
    previous = read_dns(uuid)
    if mode == "auto":
        target = ("no", "", "no", "")
    else:
        if mode == "encrypted":
            v4, v6 = [LOCAL_PROXY], []
        if not v4 and not v6:
            raise RuntimeError("Enter at least one DNS address.")
        # Verify the encrypted loopback resolver before changing the live connection.
        if mode == "encrypted":
            dns_query(LOCAL_PROXY)
        target = ("yes", ",".join(v4), "yes", ",".join(v6))
    def modify(values):
        nm("connection", "modify", "uuid", uuid,
           *(token for pair in zip(DNS_FIELDS, values) for token in pair))
    if target == previous:
        return "This DNS setting is already saved."
    if active_profile(device) != uuid:
        raise RuntimeError("The active connection changed. Reload the DNS page and try again.")
    modify(target)
    try:
        if active_profile(device) != uuid:
            raise RuntimeError("The active connection changed before DNS could be applied.")
        nm("device", "reapply", device)
    except (RuntimeError, subprocess.TimeoutExpired) as error:
        try:
            modify(previous)
            if active_profile(device) == uuid:
                nm("device", "reapply", device)
        except (RuntimeError, subprocess.TimeoutExpired) as restore:
            raise RuntimeError(f"{error} Restore failed: {restore}") from error
        raise RuntimeError(f"{error} The original DNS settings were restored.") from error
    return "DNS applied to the active connection."


def label(box, message):
    widget = Gtk.Label(label=message, xalign=0, wrap=True)
    box.pack_start(widget, False, False, 0)
    return widget


class DNSPage:
    def __init__(self, panel, box):
        self.panel = panel
        label(box, "Set DNS for the device selected on the Connection tab. VPN apps and browser DNS settings can use their own resolvers.")
        self.current = label(box, "Select Load Current Settings to inspect this connection.")
        self.mode = Gtk.ComboBoxText()
        for identity, name in (("auto", "Automatic (from the network)"),
                               ("custom", "Custom DNS addresses"),
                               ("encrypted", "Encrypted DNS (local DNSCrypt)")):
            self.mode.append(identity, name)
        self.mode.set_active_id("auto")
        box.pack_start(self.mode, False, False, 0)
        self.v4 = self.entry(box, "IPv4 DNS addresses", "Enter IPv4 addresses separated by commas")
        self.v6 = self.entry(box, "IPv6 DNS addresses", "Enter IPv6 addresses separated by commas")
        label(box, "Custom DNS uses the addresses you provide. Encrypted DNS uses the local DNSCrypt service.")
        row = Gtk.Box(spacing=10)
        box.pack_start(row, False, False, 0)
        panel.button(row, "Load Current Settings", self.load)
        panel.button(row, "Test DNSCrypt", self.test)
        self.apply_button = panel.button(row, "Apply DNS", self.apply)
        self.mode.connect("changed", self.update)
        self.update()
        self.loaded_device = None
        panel.device.connect("changed", lambda *_: self.load())
        self.apply_button.set_sensitive(False)

    @staticmethod
    def entry(box, name, hint):
        caption = label(box, name)
        entry = Gtk.Entry(placeholder_text=hint)
        entry.get_accessible().set_name(name)
        caption.set_mnemonic_widget(entry)
        box.pack_start(entry, False, False, 0)
        return entry

    def update(self, *_):
        for entry in (self.v4, self.v6):
            entry.set_sensitive(self.mode.get_active_id() == "custom")

    def load(self, *_):
        device = self.panel.device.get_active_id()
        if not device:
            return
        self.loaded_device = None
        self.apply_button.set_sensitive(False)
        self.current.set_text("Reading DNS settings…")
        def work():
            return (read_dns(active_profile(device)),
                    nm("--escape", "no", "-g", "IP4.DNS,IP6.DNS", "device", "show", device))
        def done(value, error):
            if self.panel.device.get_active_id() != device:
                return False
            if error:
                self.current.set_text(error)
            else:
                (auto4, v4, auto6, v6), effective = value
                mode = "encrypted" if (auto4, v4, auto6, v6) == ("yes", LOCAL_PROXY, "yes", "") else (
                    "custom" if v4 or v6 or auto4 == "yes" or auto6 == "yes" else "auto")
                self.mode.set_active_id(mode)
                self.v4.set_text(v4)
                self.v6.set_text(v6)
                self.current.set_text(f"{device} DNS: " + (", ".join(effective.splitlines()) or "None reported"))
                self.loaded_device = device
                self.apply_button.set_sensitive(True)
            return False
        self.panel.async_run(work, done)

    def test(self, *_):
        self.panel.status.set_text("Testing the local DNSCrypt resolver…")
        def done(_, error):
            self.panel.status.set_text(error or "DNSCrypt resolved the test name at " + LOCAL_PROXY + ".")
            return False
        self.panel.async_run(lambda: dns_query(LOCAL_PROXY), done)

    def apply(self, *_):
        device = self.panel.device.get_active_id()
        if not device or device != self.loaded_device:
            return
        mode = self.mode.get_active_id()
        try:
            v4, v6 = (addresses(self.v4.get_text(),4), addresses(self.v6.get_text(),6)) if mode == "custom" else ([],[])
        except ValueError as error:
            self.panel.status.set_text(str(error))
            return
        self.apply_button.set_sensitive(False)
        self.panel.status.set_text("Applying DNS. NetworkManager may ask for authentication…")
        def done(message, error):
            self.panel.status.set_text(error or message)
            self.load()
            return False
        self.panel.async_run(lambda: change_dns(device, mode, v4, v6), done)


class VPNPage:
    def __init__(self, panel, box):
        self.panel = panel
        self.status = label(box, "Refresh to see saved WireGuard and OpenVPN profiles.")
        self.combo = Gtk.ComboBoxText()
        box.pack_start(self.combo, False, False, 0)
        row = Gtk.Box(spacing=8)
        box.pack_start(row, False, False, 0)
        panel.button(row, "Refresh Profiles", self.refresh)
        self.connect = panel.button(row, "Connect", lambda *_: self.toggle(True))
        self.disconnect = panel.button(row, "Disconnect", lambda *_: self.toggle(False))
        panel.button(box, "Import or Edit VPN Profiles…", lambda *_: panel.launch("nm-connection-editor"))
        if any(a.get_id() == "proton.vpn.app.gtk.desktop" for a in Gio.AppInfo.get_all()):
            panel.button(box, "Open Proton VPN", lambda *_: panel.launch("gtk-launch","proton.vpn.app.gtk"))
        label(box, "Import a WireGuard or OpenVPN configuration from your provider. VPN credentials and routing are managed by your VPN app or NetworkManager.")
        self.active = set()
        self.busy = False
        self.combo.connect("changed", lambda *_: self.buttons())
        self.buttons()
        self.refresh()

    def buttons(self):
        identity = self.combo.get_active_id()
        self.connect.set_sensitive(bool(identity) and identity not in self.active and not self.busy)
        self.disconnect.set_sensitive(bool(identity) and identity in self.active and not self.busy)

    def refresh(self, *_):
        def done(value, error):
            if error:
                self.status.set_text(error)
                return False
            entries, active = value
            self.active = {row[0] for row in active if row[2] in VPN_TYPES}
            selected = self.combo.get_active_id()
            self.combo.remove_all()
            for identity,name,kind,_ in entries:
                suffix = "Connected" if identity in self.active else "Disconnected"
                self.combo.append(identity, f"{name}  ({'WireGuard' if kind == 'wireguard' else 'VPN'}, {suffix})")
            if entries:
                self.combo.set_active_id(selected) if selected and any(row[0]==selected for row in entries) else self.combo.set_active(0)
            self.status.set_text(f"{len(self.active)} active NetworkManager VPN profile(s)." if entries else
                                 "No VPN profiles saved. Import a configuration from your VPN provider.")
            self.buttons()
            return False
        self.panel.async_run(lambda: ([r for r in profiles() if r[2] in VPN_TYPES], profiles(True)), done)

    def toggle(self, enabled):
        identity = self.combo.get_active_id()
        if not identity or self.busy:
            return
        self.busy = True
        self.buttons()
        self.status.set_text("Connecting…" if enabled else "Disconnecting…")
        def done(_, error):
            self.busy = False
            self.panel.status.set_text(error or ("VPN profile activated." if enabled else "VPN profile disconnected."))
            self.refresh()
            return False
        self.panel.async_run(lambda: nm("--wait","30","connection","up" if enabled else "down","uuid",identity), done)

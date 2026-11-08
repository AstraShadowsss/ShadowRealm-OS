#!/usr/bin/python3
"""Build reviewed root-owned helpers without reading a developer account or host."""
from pathlib import Path
import argparse, shutil, subprocess, tempfile
p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
version=(a.source/'VERSION').read_text().strip()
def write(root,name,text,mode=0o644):
 f=root/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(text);f.chmod(mode)
with tempfile.TemporaryDirectory() as tmp:
 root=Path(tmp)
 for name in ('shadowrealm-os-firewall','shadowrealm-os-security-control','shadowrealm-os-security-status','shadow-account-rename'):
  text=(a.source/'security'/name).read_text()
  if text.startswith('#!/usr/bin/python3'):compile(text,name,'exec')
  write(root,'usr/local/libexec/'+name,text,0o755)
 for f in (a.source/'security/units').iterdir():write(root,'usr/lib/systemd/system/'+f.name,f.read_text())
 for f in (a.source/'security/policies').iterdir():write(root,'usr/share/polkit-1/actions/'+f.name,f.read_text())
 write(root,'etc/nftables/shadowrealm-os.nft','''table inet shadowrealm-os {
 chain input {
  type filter hook input priority 0; policy drop;
  iifname "lo" accept
  ct state established,related accept
  ct state invalid drop
  meta l4proto { icmp, ipv6-icmp } accept
  udp sport 67 udp dport 68 accept
  udp sport 547 udp dport 546 accept
  # Shadow Shield managed ports begin
  limit rate 5/minute log prefix "ShadowRealm-OS blocked: "
  # Shadow Shield managed ports end
 }
 chain forward { type filter hook forward priority 0; policy drop; }
 chain output { type filter hook output priority 0; policy accept; }
}
''')
 write(root,'etc/shadowrealm-os/firewall-ports.json','{"tcp": [], "udp": []}\n')
 write(root,'etc/shadowrealm-os/internet-pause.nft','''table inet shadowrealm_os_internet_pause {
 chain output {
  type filter hook output priority 10; policy drop;
  oifname "lo" accept
  udp sport 68 udp dport 67 accept
  udp sport 546 udp dport 547 accept
  ip6 nexthdr ipv6-icmp icmpv6 type { nd-router-solicit, nd-neighbor-solicit, nd-neighbor-advert } accept
 }
}
''')
 write(root,'usr/share/doc/shadowrealm-os-security/copyright',(a.source/'LICENSE').read_text())
 write(root,'DEBIAN/control',f'''Package: shadowrealm-os-security
Version: {version}
Section: admin
Priority: optional
Architecture: all
Maintainer: ShadowRealm-OS Project <packages@shadowrealm-os.invalid>
Depends: python3, nftables, apparmor, apparmor-utils, pkexec, systemd, init-system-helpers, iproute2, procps, tor, passwd
Description: ShadowRealm-OS firewall, privacy status and local account controls
''')
 write(root,'DEBIAN/postinst','''#!/bin/sh
set -e
if [ "$1" = configure ]; then
 for unit in shadowrealm-os-firewall.service shadowrealm-os-security-status.timer shadow-account-rename.service; do
  deb-systemd-helper enable "$unit" >/dev/null
 done
fi
''',0o755)
 write(root,'DEBIAN/conffiles','/etc/nftables/shadowrealm-os.nft\n/etc/shadowrealm-os/firewall-ports.json\n/etc/shadowrealm-os/internet-pause.nft\n')
 subprocess.run(['dpkg-deb','--root-owner-group','--build',str(root),str(a.output/f'shadowrealm-os-security_{version}_all.deb')],check=True)

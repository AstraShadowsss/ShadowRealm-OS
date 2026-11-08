#!/usr/bin/python3
"""Upgrade Debian's obsolete v2 resolver URL without changing its trust key."""
from pathlib import Path
import sys

root = Path(sys.argv[1])
config = root / 'etc/dnscrypt-proxy/dnscrypt-proxy.toml'
old = "url = 'https://download.dnscrypt.info/resolvers-list/v2/public-resolvers.md'"
new = "urls = ['https://raw.githubusercontent.com/DNSCrypt/dnscrypt-resolvers/master/v3/public-resolvers.md', 'https://download.dnscrypt.info/resolvers-list/v3/public-resolvers.md']"
text = config.read_text()
if old in text:
    config.write_text(text.replace(old, new))
    for name in ('public-resolvers.md', 'public-resolvers.md.minisig'):
        (root / 'var/cache/dnscrypt-proxy' / name).unlink(missing_ok=True)
    print('Updated resolver sources; upstream signature verification remains enabled.')

#!/usr/bin/env python3
"""Reassemble the six release source parts and verify their original archive hash."""
from pathlib import Path
import hashlib
BASE=Path(__file__).resolve().parent
NAME='Third-party-corresponding-source.tar'
EXPECTED='c3656b4b5cfac6caf1d90e41d7f08bceeec5e8424f965d2bf85e670cf128be46'
parts=[BASE/(NAME+'.part'+str(n).zfill(2)) for n in range(1,7)]
for part in parts:
 if not part.is_file():raise SystemExit('Missing source part: '+part.name)
pending=BASE/(NAME+'.reassembling');target=BASE/NAME
if target.exists():raise SystemExit('Archive already exists; move it aside before reassembling.')
hash_value=hashlib.sha256()
try:
 with pending.open('xb') as out:
  for part in parts:
   print('Reading',part.name,flush=True)
   with part.open('rb') as source:
    for block in iter(lambda:source.read(8*1024*1024),b''):
     out.write(block);hash_value.update(block)
 if hash_value.hexdigest()!=EXPECTED:raise SystemExit('Checksum mismatch. The incomplete output has been retained for inspection.')
 pending.rename(target)
 print('Verified archive:',target)
 print('Extract with: tar -xf '+NAME)
except BaseException:
 print('Source parts were kept unchanged.')
 raise

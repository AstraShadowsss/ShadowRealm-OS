#!/bin/bash
set -euo pipefail
builder="${1:?Pass build-apt-repository.py and a custom DEB}"
fixture="${2:?Custom DEB required}"
package=$(dpkg-deb -f "$fixture" Package)
testdir=$(mktemp -d /tmp/sr-apt-rejection.XXXXXXXX)
trap 'rm -rf -- "$testdir"' EXIT
chmod 755 "$testdir"
mkdir -m700 "$testdir/key"; mkdir "$testdir/packages"
cp "$fixture" "$testdir/packages/"
gpg --homedir "$testdir/key" --batch --pinentry-mode loopback --passphrase '' --quick-generate-key 'Disposable negative test <test@invalid>' ed25519 sign 1d >/dev/null 2>&1
fingerprint=$(gpg --homedir "$testdir/key" --with-colons --list-keys 2>/dev/null | awk -F: '$1=="fpr" {print $10;exit}')
python3 "$builder" "$testdir/packages" "$testdir/original" --gnupg-home "$testdir/key" --signing-key "$fingerprint"
key="$testdir/original/shadowrealm-os-archive-keyring.gpg"
for name in unsigned altered expired corrupt; do
 cp -a "$testdir/original" "$testdir/$name"
 mkdir -p "$testdir/lists-$name/partial" "$testdir/cache-$name/archives/partial"
 printf 'Types: deb\nURIs: file:%s\nSuites: trixie\nComponents: main\nSigned-By: %s\n' "$testdir/$name" "$key" > "$testdir/$name.sources"
done
rm "$testdir/unsigned/dists/trixie/InRelease" "$testdir/unsigned/dists/trixie/Release.gpg"
sed -i 's/Label: ShadowRealm-OS/Label: altered/' "$testdir/altered/dists/trixie/InRelease"
python3 - "$testdir/expired/dists/trixie/Release" <<'PY'
import sys,datetime,email.utils,pathlib
p=pathlib.Path(sys.argv[1]);s=p.read_text();now=datetime.datetime.now(datetime.timezone.utc)
lines=[]
for line in s.splitlines():
 if line.startswith('Date:'):line='Date: '+email.utils.format_datetime(now-datetime.timedelta(days=3),usegmt=True)
 if line.startswith('Valid-Until:'):line='Valid-Until: '+email.utils.format_datetime(now-datetime.timedelta(days=1),usegmt=True)
 lines.append(line)
p.write_text('\n'.join(lines)+'\n')
PY
gpg --homedir "$testdir/key" --batch --yes --local-user "$fingerprint" --output "$testdir/expired/dists/trixie/InRelease" --clearsign "$testdir/expired/dists/trixie/Release"
aptcase() {
 name=$1;shift
 apt-get -o Dir::Etc::sourcelist="$testdir/$name.sources" -o Dir::Etc::sourceparts=- -o Dir::State::lists="$testdir/lists-$name" -o Dir::Cache="$testdir/cache-$name" -o APT::Update::Error-Mode=any "$@"
}
for name in unsigned altered expired; do
 if aptcase "$name" update >"$testdir/$name.log" 2>&1; then cat "$testdir/$name.log";echo "FAIL: accepted $name metadata";exit 1;fi
 grep -Eiq 'not signed|signature|expired' "$testdir/$name.log"
 echo "PASS: APT rejected $name metadata"
done
aptcase corrupt update >/dev/null
printf 'tampered' >> "$testdir/corrupt/pool/main/$package/"*.deb
cd "$testdir"
if aptcase corrupt download "$package" >"$testdir/corrupt.log" 2>&1; then echo 'FAIL: corrupt package accepted';exit 1;fi
grep -Eiq 'Hash Sum mismatch|unexpected size|File has unexpected size' "$testdir/corrupt.log"
echo 'PASS: APT rejected modified package bytes'

"""Keep executable scripts portable when package sources come from Windows."""
import os
from pathlib import Path
import stat
import tempfile


def normalize_scripts(roots):
    changed = []
    for root in map(Path, roots):
        paths = [root] if root.is_file() else root.rglob('*')
        for path in paths:
            if path.is_symlink() or not path.is_file():
                continue
            with path.open('rb') as stream:
                if stream.read(2) != b'#!':
                    continue
            original = path.read_bytes()
            normalized = original.replace(b'\r\n', b'\n')
            if normalized == original:
                continue
            details = path.stat()
            fd, temporary = tempfile.mkstemp(prefix='.script-new-', dir=path.parent)
            try:
                with os.fdopen(fd, 'wb') as stream:
                    stream.write(normalized)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.chmod(temporary, stat.S_IMODE(details.st_mode))
                if hasattr(os, 'geteuid') and os.geteuid() == 0:
                    os.chown(temporary, details.st_uid, details.st_gid)
                os.replace(temporary, path)
            finally:
                Path(temporary).unlink(missing_ok=True)
            changed.append(str(path))
    return changed


def prepare_package(root):
    """Make shared package data readable even under a private build umask."""
    root = Path(root)
    changed = normalize_scripts([root])
    root.chmod(0o755)
    for directory in (root/'usr', root/'etc/xdg', root/'DEBIAN'):
        if not directory.is_dir() or directory.is_symlink():
            continue
        directory.chmod(0o755)
        for path in directory.rglob('*'):
            if path.is_symlink():
                continue
            if path.is_dir():
                path.chmod(0o755)
            elif path.is_file():
                executable = bool(stat.S_IMODE(path.stat().st_mode) & 0o111)
                path.chmod(0o755 if executable else 0o644)
    return changed


if __name__ == '__main__':
    import sys
    print('Normalized executable scripts:', len(normalize_scripts(sys.argv[1:])))

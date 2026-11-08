"""Single-source read-only Account Manager preflight for queued renames."""
import json
import subprocess
from pathlib import Path

HELPER = Path('/usr/local/libexec/shadow-account-rename')


def preflight(username, uid=None):
    # The GTK app checks its own logged-in user. An explicit uid is used by
    # tests; rejecting arbitrary impersonation keeps real UI behavior clear.
    import os
    if uid is not None and uid != os.getuid():
        raise ValueError('Cannot preflight a different user.')
    try:
        process = subprocess.run(
            ['/usr/bin/python3', str(HELPER), 'preflight', username],
            capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ValueError(f'Account preflight unavailable: {error}') from error
    if process.returncode:
        raise ValueError(process.stderr.strip() or 'Account preflight failed.')
    try:
        data = json.loads(process.stdout)
        return (data['old'], Path(data['home']), Path(data['target']),
                [Path(p) for p in data['references']], data['unreadable'])
    except (ValueError, KeyError) as error:
        raise ValueError('Account preflight returned invalid data.') from error

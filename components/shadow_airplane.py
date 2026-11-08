"""Airplane mode for managed wireless radios. Wired interfaces are left alone."""

from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import re
import subprocess


STATE = Path.home() / ".config/shadowrealm-os/airplane-mode.json"


def run(*args):
    try:
        result = subprocess.run(args, stdin=subprocess.DEVNULL, capture_output=True, text=True,
                                timeout=8, env=os.environ | {"LC_ALL": "C"})
    except (OSError, subprocess.TimeoutExpired) as error:
        raise RuntimeError(str(error)) from error
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "Radio command failed.")
    return result.stdout.strip()


def has_bluetooth_controller():
    return any(Path("/sys/class/bluetooth").glob("hci[0-9]*"))


def inventory():
    fields = run("nmcli", "-t", "-f", "WIFI-HW,WIFI,WWAN-HW,WWAN", "radio", "all").split(":")
    if len(fields) != 4:
        raise RuntimeError("NetworkManager did not report its radio state.")
    states = {}
    blocked = []
    for radio, hardware, setting in zip(("wifi", "wwan"), fields[::2], fields[1::2], strict=True):
        if hardware == "disabled":
            blocked.append(radio)
        if hardware != "missing" and setting in ("enabled", "disabled"):
            states[radio] = setting == "enabled"
    if has_bluetooth_controller():
        paths = run("busctl", "--system", "tree", "--list", "org.bluez").splitlines()
        for path in paths:
            if re.fullmatch(r"/org/bluez/hci\d+", path):
                address = json.loads(run("busctl", "--system", "get-property", "org.bluez", path,
                                         "org.bluez.Adapter1", "Address").removeprefix("s "))
                value = run("busctl", "--system", "get-property", "org.bluez", path,
                            "org.bluez.Adapter1", "Powered")
                states[f"bluetooth:{address}"] = value == "b true"
    return states, blocked


def set_radio(radio, enabled):
    if radio in ("wifi", "wwan"):
        run("nmcli", "radio", radio, "on" if enabled else "off")
        return
    address = radio.removeprefix("bluetooth:")
    if not re.fullmatch(r"(?:[0-9A-F]{2}:){5}[0-9A-F]{2}", address, re.I):
        raise RuntimeError("Invalid Bluetooth controller address.")
    for path in run("busctl", "--system", "tree", "--list", "org.bluez").splitlines():
        if re.fullmatch(r"/org/bluez/hci\d+", path):
            identity = json.loads(run("busctl", "--system", "get-property", "org.bluez", path,
                                      "org.bluez.Adapter1", "Address").removeprefix("s "))
            if identity == address:
                run("busctl", "--system", "set-property", "org.bluez", path,
                    "org.bluez.Adapter1", "Powered", "b", "true" if enabled else "false")
                return
    raise RuntimeError(f"Bluetooth controller {address} is unavailable.")


@contextmanager
def locked():
    STATE.parent.mkdir(parents=True, exist_ok=True)
    with STATE.with_suffix(".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield


def saved():
    if not STATE.exists():
        return {}
    states = json.loads(STATE.read_text())
    if not isinstance(states, dict) or any(not isinstance(value, bool) for value in states.values()):
        raise RuntimeError("The saved radio settings could not be read.")
    return states


def save(states):
    if not states:
        STATE.unlink(missing_ok=True)
        return
    temp = STATE.with_suffix(".new")
    temp.write_text(json.dumps(states) + "\n")
    temp.chmod(0o600)
    temp.replace(STATE)


def status():
    with locked():
        current, blocked = inventory()
        return bool(saved()), bool(current), blocked


def set_mode(enabled):
    with locked():
        previous = saved()
        if enabled == bool(previous):
            return
        current, _ = inventory()
        if enabled:
            if not current:
                raise RuntimeError("No wireless radio is available.")
            save(current)
            changed = {}
            try:
                for radio, state in current.items():
                    if state:
                        changed[radio] = state
                        set_radio(radio, False)
            except RuntimeError as error:
                try:
                    for radio, state in reversed(tuple(changed.items())):
                        set_radio(radio, state)
                except RuntimeError as rollback:
                    raise RuntimeError(f"{error} Automatic restore needs attention: {rollback}") from error
                save({})
                raise
        else:
            remaining = previous.copy()
            errors = []
            for radio, state in previous.items():
                try:
                    if radio not in current:
                        raise RuntimeError(f"{radio} is unavailable.")
                    if current[radio] != state:
                        set_radio(radio, state)
                    remaining.pop(radio)
                except RuntimeError as error:
                    errors.append(str(error))
            save(remaining)
            if errors:
                raise RuntimeError("Some saved radio settings need attention. " + " ".join(errors))

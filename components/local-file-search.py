#!/usr/bin/env python3
"""Find local files by name inside a directory selected by the user."""

import argparse
import os
from pathlib import Path
import stat
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from itertools import islice
from threading import Event


def find_files(folder, query, cancelled=lambda: False):
    terms = query.casefold().split()
    if not terms:
        return

    folder = Path(folder).resolve(strict=True)
    root_stat = folder.stat()
    if not stat.S_ISDIR(root_stat.st_mode):
        raise NotADirectoryError(folder)

    pending = [folder]
    while pending and not cancelled():
        directory = pending.pop()
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    if cancelled():
                        return
                    if entry.name.startswith(".") or entry.is_symlink():
                        continue
                    try:
                        path = Path(entry.path)
                        entry_stat = path.stat(follow_symlinks=False)
                    except OSError:
                        continue
                    if stat.S_ISDIR(entry_stat.st_mode):
                        if entry_stat.st_dev == root_stat.st_dev:
                            pending.append(path)
                    elif stat.S_ISREG(entry_stat.st_mode):
                        if all(term in entry.name.casefold() for term in terms):
                            yield path
        except OSError:
            if directory == folder:
                raise


def desktop_search():
    import gi
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gdk, Gio, GLib, Gtk

    window = Gtk.Window(title="Local Search", default_width=560, default_height=420)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8, margin=12)
    window.add(box)
    query = Gtk.SearchEntry(placeholder_text="Search file names or settings")
    query.get_accessible().set_name("Search query")
    box.pack_start(query, False, False, 0)
    folder = Gtk.FileChooserButton(title="Choose a folder", action=Gtk.FileChooserAction.SELECT_FOLDER)
    folder.set_local_only(True)
    default = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOCUMENTS)
    folder.set_filename(default if default and Path(default).is_dir() else str(Path.home()))
    folder.get_accessible().set_name("Folder to search")
    box.pack_start(folder, False, False, 0)
    buttons = Gtk.Box(spacing=8)
    box.pack_start(buttons, False, False, 0)
    search = Gtk.Button(label="Find Files")
    stop = Gtk.Button(label="Cancel Search", sensitive=False)
    settings = Gtk.Button(label="Find Settings")
    for button, accessible in ((search, "Find files"), (stop, "Cancel search"),
                               (settings, "Find settings")):
        button.get_accessible().set_name(accessible)
        buttons.pack_start(button, False, False, 0)
    results = Gtk.ListStore(str, str)
    view = Gtk.TreeView(model=results)
    view.get_accessible().set_name("Search results")
    for index, title in enumerate(("File", "Folder")):
        column = Gtk.TreeViewColumn(title, Gtk.CellRendererText(), text=index)
        column.set_resizable(True)
        view.append_column(column)
    scroll = Gtk.ScrolledWindow()
    scroll.add(view)
    box.pack_start(scroll, True, True, 0)
    status = Gtk.Label(label="Search file names in the selected folder. "
                             "Ctrl+F focuses search, Down opens results, Enter opens, Esc cancels.", xalign=0)
    status.get_accessible().set_name("Search status")
    box.pack_start(status, False, False, 0)
    worker = ThreadPoolExecutor(max_workers=1)
    active = None

    def finish(future, token):
        if token is not active:
            return GLib.SOURCE_REMOVE
        stop.set_sensitive(False)
        try:
            paths = future.result()
            for path in paths[:100]:
                results.append((path.name, str(path.parent)))
            status.set_text("Showing the first 100 matches." if len(paths) > 100
                            else f"{len(paths)} matching files.")
        except OSError as error:
            status.set_text(f"Could not search the folder: {error.strerror or error}")
        return GLib.SOURCE_REMOVE

    def cancel(*_):
        nonlocal active
        if active:
            active.set()
            active = None
            stop.set_sensitive(False)
            status.set_text("Search canceled.")

    def start(*_):
        nonlocal active
        cancel()
        text, directory = query.get_text().strip(), folder.get_filename()
        results.clear()
        if not text or not directory:
            status.set_text("Enter a file name and choose a folder.")
            return
        token = active = Event()
        stop.set_sensitive(True)
        status.set_text("Searching…")
        future = worker.submit(lambda: list(islice(find_files(directory, text, token.is_set), 101)))
        future.add_done_callback(lambda result: GLib.idle_add(finish, result, token))

    def open_settings(*_):
        env = dict(os.environ, SHADOWREALM_SETTINGS_QUERY=query.get_text().strip())
        try:
            subprocess.Popen(["shadowrealm-os-desktop", "control-center"], env=env)
        except OSError as error:
            status.set_text(str(error))

    def open_result(_, row, column):
        model, treeiter = results.get_iter(row)
        if treeiter is None:
            return
        name, directory = model[treeiter][0], model[treeiter][1]
        path = Path(directory) / name
        if not path.is_file() or path.is_symlink():
            status.set_text("This file is no longer available.")
            return
        try:
            Gio.AppInfo.launch_default_for_uri(path.as_uri(), None)
        except GLib.Error as error:
            status.set_text(error.message)

    def close(*_):
        cancel()
        worker.shutdown(wait=False, cancel_futures=True)
        Gtk.main_quit()

    def key_press(_, event):
        key = event.keyval
        control = bool(event.state & Gdk.ModifierType.CONTROL_MASK)
        if key == Gdk.KEY_Escape:
            if active:
                cancel()
            elif query.get_text():
                query.set_text("")
            else:
                window.destroy()
            return True
        if control and key in (Gdk.KEY_f, Gdk.KEY_F):
            query.grab_focus()
            query.select_region(0, -1)
            return True
        if control and key in (Gdk.KEY_l, Gdk.KEY_L):
            folder.grab_focus()
            return True
        if control and key in (Gdk.KEY_q, Gdk.KEY_Q):
            window.destroy()
            return True
        if key == Gdk.KEY_F5:
            start()
            return True
        if key == Gdk.KEY_Down and query.has_focus():
            if len(results):
                view.get_selection().select_path(Gtk.TreePath.new_first())
            view.grab_focus()
            return True
        return False

    window.connect("key-press-event", key_press)
    query.connect("activate", start)
    search.connect("clicked", start)
    stop.connect("clicked", cancel)
    settings.connect("clicked", open_settings)
    view.connect("row-activated", open_result)
    window.connect("destroy", close)
    window.show_all()
    query.grab_focus()
    Gtk.main()


def main():
    if sys.argv[1:] == ["--gui"]:
        desktop_search()
        return

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("query")
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()
    if args.limit < 1:
        parser.error("--limit must be positive")

    for count, match in enumerate(find_files(args.folder, args.query), 1):
        print(match)
        if count == args.limit:
            break


if __name__ == "__main__":
    main()

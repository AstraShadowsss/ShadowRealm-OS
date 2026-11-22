"""Share the selected appearance palette with native desktop widgets."""
import configparser
import io
import os
from pathlib import Path
import re
import tempfile


def write_active_palette(directory, mode, record):
    def color(role):
        value = record.get('widget_' + role, record[role])
        if not re.fullmatch(r'#[0-9a-fA-F]{6}', value):
            raise ValueError('Invalid theme color: ' + role)
        return value
    background, foreground = color('background'), color('foreground')
    rgb = lambda value: [int(value[i:i+2], 16) for i in (1, 3, 5)]
    surface = '#' + ''.join(f'{round(a*.86+b*.14):02x}'
                            for a, b in zip(rgb(background), rgb(foreground)))
    config = configparser.ConfigParser(interpolation=None)
    config.optionxform = str
    config['Palette'] = dict(Mode=mode, Accent=color('accent'), Secondary=color('secondary'),
                             Background=background, Foreground=foreground, Surface=surface)
    data = io.StringIO()
    config.write(data)
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.active-palette-', dir=directory)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            stream.write(data.getvalue())
        os.replace(temporary, directory / 'active-palette.ini')
    finally:
        Path(temporary).unlink(missing_ok=True)

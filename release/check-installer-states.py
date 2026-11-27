#!/usr/bin/env python3
"""Render the Calamares stylesheet's checkbox, radio, focus and disabled states.

Run on a desktop with PyQt5 to inspect the installer controls without booting an
ISO. The stylesheet ships in the installer settings package at
usr/share/shadowrealm-os/installer.qss; pass an extracted copy if the package is
not installed.
"""
import argparse
import pathlib
import sys

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QGroupBox,
                             QLabel, QLineEdit, QProgressBar, QPushButton,
                             QRadioButton, QVBoxLayout, QWidget)

DEFAULT_QSS = '/usr/share/shadowrealm-os/installer.qss'

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--stylesheet', type=pathlib.Path, default=pathlib.Path(DEFAULT_QSS))
p.add_argument('--output', type=pathlib.Path, default=pathlib.Path('installer-states.png'))
a = p.parse_args()
if not a.stylesheet.is_file():
    p.error('Stylesheet not found: ' + str(a.stylesheet))

app = QApplication(sys.argv)
window = QWidget()
window.setWindowTitle('ShadowRealm-OS installer states')
window.setStyleSheet(a.stylesheet.read_text())
outer = QVBoxLayout(window)
box = QGroupBox('Installer controls')
outer.addWidget(box)
body = QVBoxLayout(box)

body.addWidget(QLabel('Checkbox and radio states'))
unchecked = QCheckBox('Unchecked, enabled')
checked = QCheckBox('Checked, enabled')
checked.setChecked(True)
checked_off = QCheckBox('Checked, disabled')
checked_off.setChecked(True)
checked_off.setEnabled(False)
unchecked_off = QCheckBox('Unchecked, disabled')
unchecked_off.setEnabled(False)
for widget in (unchecked, checked, checked_off, unchecked_off):
    body.addWidget(widget)
radio_on = QRadioButton('Radio selected')
radio_on.setChecked(True)
radio_off = QRadioButton('Radio disabled')
radio_off.setEnabled(False)
body.addWidget(radio_on)
body.addWidget(radio_off)

body.addWidget(QLabel('Text, combo and buttons'))
focused = QLineEdit('Focused field')
focused.setFocus()
disabled = QLineEdit('Disabled field')
disabled.setEnabled(False)
body.addWidget(focused)
body.addWidget(disabled)
combo = QComboBox()
combo.addItems(['Combo option'])
body.addWidget(combo)
button = QPushButton('Enabled button')
button_off = QPushButton('Disabled button')
button_off.setEnabled(False)
body.addWidget(button)
body.addWidget(button_off)
progress = QProgressBar()
progress.setValue(42)
body.addWidget(progress)

window.resize(520, 520)
window.show()


def capture():
    if not window.grab().save(str(a.output)):
        print('Could not write ' + str(a.output), file=sys.stderr)
        sys.exit(1)
    print('Wrote ' + str(a.output))
    app.quit()


QTimer.singleShot(1800, capture)
sys.exit(app.exec_())

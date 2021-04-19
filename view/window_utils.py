from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt


def get_layout(layout):
    layout.addStretch()
    return layout


def get_grid(spacing=20):
    grid_layout = QtWidgets.QGridLayout()
    grid_layout.setHorizontalSpacing(spacing)
    grid_layout.setVerticalSpacing(spacing)
    grid_layout.setAlignment(Qt.AlignCenter)
    return grid_layout


def get_button(label='Button', enabled=True, action=None, size=(100, 40), shortcut=None, color=None):
    if shortcut is not None:
        button = QtWidgets.QPushButton(label, shortcut=shortcut)
    else:
        button = QtWidgets.QPushButton(label)
    if action is not None:
        button.clicked.connect(action)
    button.setEnabled(enabled)
    if size is not None:
        button.setFixedSize(size[0], size[1])
    else:
        button.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
    if color is not None:
        button.setStyleSheet(f'background-color: #{color};color:#000000;font-weight: bold;')
    return button

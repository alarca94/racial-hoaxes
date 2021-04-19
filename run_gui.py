import sys

from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5 import QtGui

from view.home import MainWindow
from view.download import DownloadWindow
from view.clean import CleanerWindow


class GUI:
    def __init__(self):
        pass


def run():
    app = QApplication(sys.argv)
    font = QtGui.QFont("Times New Roman")
    font.setPointSize(14)
    app.setFont(font)
    # screen_resolution = app.desktop().screenGeometry()
    # width, height = screen_resolution.width(), screen_resolution.height()

    windows = {'home': MainWindow(), 'download': DownloadWindow(), 'cleaner': CleanerWindow()}
    for k, v in windows.items():
        v.set_windows(windows)

    windows['home'].showMaximized()

    app.exec_()

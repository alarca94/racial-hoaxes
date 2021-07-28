import os
import shutil
import pandas as pd

from ast import literal_eval
from utils.constants import *


def read_data(stage='clean'):
    if stage == 'clean':
        file_path = os.path.join(DATA_PATH, CLEAN_FILE)
        if not os.path.isfile(file_path):
            shutil.copy(os.path.join(DATA_PATH, DOWNLOAD_FILE), file_path)
    elif stage == 'annotate':
        file_path = os.path.join(DATA_PATH, ANNOTATE_FILE)
        if not os.path.isfile(file_path):
            shutil.copy(os.path.join(DATA_PATH, CLEAN_FILE), file_path)

    list_converter = lambda s: literal_eval(s)
    converters = {c: list_converter for c in ['urls', 'hashtags', 'annotations']}
    return pd.read_csv(file_path, encoding='utf-8', converters=converters)


class Printer:
    def __init__(self, status_bar):
        self.status_bar = status_bar
        self.default_style = status_bar.styleSheet()

    def set_style(self, style):
        if style == 'error':
            self.status_bar.setStyleSheet("QStatusBar{color:red;font-weight:bold;}")
        elif style == 'success':
            self.status_bar.setStyleSheet("QStatusBar{color:green;font-weight:bold;}")
        elif style == 'warning':
            self.status_bar.setStyleSheet("QStatusBar{color:yellow;font-weight:bold;}")
        elif style == 'default':
            self.status_bar.setStyleSheet(self.default_style)

    def show_message(self, msg, time, style):
        self.set_style(style)
        self.status_bar.showMessage(msg, time)

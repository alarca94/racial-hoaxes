import os
import pandas as pd

from ast import literal_eval


DATA_PATH = './data'
DOWNLOAD_FILE = 'downloaded_tweets.csv'
CLEAN_FILE = 'kept_tweets.csv'


def read_data(stage='clean'):
    if stage == 'clean':
        file = DOWNLOAD_FILE
    elif stage == 'annotate':
        file = CLEAN_FILE

    if os.path.isfile(os.path.join(DATA_PATH, file)):
        list_converter = lambda s: literal_eval(s)
        converters = {c: list_converter for c in ['urls', 'hashtags', 'annotations']}
        return pd.read_csv(os.path.join(DATA_PATH, file), encoding='utf-8', converters=converters)

    return None


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

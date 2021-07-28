import re

from PyQt5 import QtCore
from PyQt5 import QtGui

from utils.inout import Printer
from utils.search import Searcher
from view.window_utils import *
from utils.constants import *


class DownloadWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(DownloadWindow, self).__init__(*args, **kwargs)

        self.setWindowTitle("Twitter Data Downloader")

        self.status = QtWidgets.QStatusBar(self)
        self.default_styleSheet = self.status.styleSheet()
        self.setStatusBar(self.status)

        self.printer = Printer(self.status)
        self.searcher = Searcher(self.printer)

        # -------------- SETTING THE LAYOUTS -------------- #
        gen_layout = get_layout(QtWidgets.QVBoxLayout())
        upper_layout = get_layout(QtWidgets.QHBoxLayout())
        bottom_layout = get_layout(QtWidgets.QHBoxLayout())

        self.add_query_grid(upper_layout)
        self.add_buttons(bottom_layout)

        gen_layout.addLayout(get_layout(QtWidgets.QHBoxLayout()),  15)
        gen_layout.addLayout(upper_layout,  40)
        gen_layout.addLayout(get_layout(QtWidgets.QHBoxLayout()), 10)
        gen_layout.addLayout(bottom_layout, 25)
        gen_layout.addLayout(get_layout(QtWidgets.QHBoxLayout()), 10)

        widget = QtWidgets.QWidget()
        widget.setLayout(gen_layout)

        # Set the central widget of the Window. Widget will expand
        # to take up all the space in the window by default.
        self.setCentralWidget(widget)

    def set_windows(self, windows):
        self.home_window = windows['home']

    def add_query_grid(self, parent_layout):
        # Hashtags, Keywords, Start Date (inclusive), End Date (inclusive), Admit Replies
        grid_layout = QtWidgets.QGridLayout()

        labels = []
        # Hashtags are concatenated with " OR " (The tweet only needs to contain one of the input hashtags)
        self.hashtags = QtWidgets.QTextEdit()
        helper_text = 'Hashtags (if multiple, enter a comma-separated sequence)\n' \
                      'Example: #hate, #stopMigration, #zeroBlack'
        self.hashtags.setPlaceholderText(helper_text)
        self.hashtags.setAcceptRichText(False)
        labels.append(QtWidgets.QLabel('HASHTAGS'))
        # All Keywords must appear in the tweet so they are concatenated with " AND "
        self.keywords = QtWidgets.QTextEdit()
        helper_text = 'Keywords (if multiple, enter a comma-separated sequence)\n' \
                      'Example: hate, migration, racist, black people'
        self.keywords.setPlaceholderText(helper_text)
        self.keywords.setAcceptRichText(False)
        labels.append(QtWidgets.QLabel('KEYWORDS'))
        # Both dates are inclusive (start-end)
        self.start_date = QtWidgets.QDateEdit(displayFormat='dd-MMM-yyyy', calendarPopup=True)
        self.start_date.setDateTime(QtCore.QDateTime.currentDateTime().addDays(-1))
        self.start_date.dateChanged.connect(self.start_date_dateedit)
        self.start_date.setFixedWidth(200)
        self.start_date.setAlignment(Qt.AlignCenter)
        labels.append(QtWidgets.QLabel('START DATE'))
        self.end_date = QtWidgets.QDateEdit(displayFormat='dd-MMM-yyyy', calendarPopup=True)
        self.end_date.setDateTime(QtCore.QDateTime.currentDateTime().addDays(-1))
        self.end_date.dateChanged.connect(self.end_date_dateedit)
        self.end_date.setFixedWidth(200)
        self.end_date.setAlignment(Qt.AlignCenter)
        labels.append(QtWidgets.QLabel('END DATE'))
        # Select the maximum number of tweets to be retrieved from twitter
        self.max_tweets = QtWidgets.QLineEdit()
        self.max_tweets.setPlaceholderText('Minimum value: 10, Maximum value: 2.000.000')
        self.max_tweets.setValidator(QtGui.QIntValidator())
        self.max_tweets.setAlignment(Qt.AlignCenter)
        self.max_tweets.setMinimumSize(300, 0)
        labels.append(QtWidgets.QLabel('MAXIMUM NUMBER OF TWEETS'))
        # Select the language of the tweets
        self.language = QtWidgets.QComboBox()
        self.language.addItems(AVAILABLE_LANGS.keys())
        labels.append(QtWidgets.QLabel('LANGUAGE'))

        l_height = 50
        for l in labels:
            l.setStyleSheet('background-color:#FAEB7C;color:#000000;font-weight: bold;')
            l.setAlignment(Qt.AlignCenter)
            l.setFixedHeight(l_height)

        # Add items to the grid
        grid_layout.addWidget(labels[0], 0, 0)
        grid_layout.addWidget(self.hashtags, 1, 0)
        grid_layout.addWidget(labels[1], 0, 1)
        grid_layout.addWidget(self.keywords, 1, 1)
        grid_layout.addWidget(labels[2], 2, 0)
        grid_layout.addWidget(self.start_date, 3, 0, Qt.AlignCenter)
        grid_layout.addWidget(labels[3], 2, 1)
        grid_layout.addWidget(self.end_date, 3, 1, Qt.AlignCenter)
        grid_layout.addWidget(labels[4], 4, 0)
        grid_layout.addWidget(self.max_tweets, 5, 0, Qt.AlignCenter)
        grid_layout.addWidget(labels[5], 4, 1)
        grid_layout.addWidget(self.language, 5, 1, Qt.AlignCenter)

        parent_layout.addLayout(grid_layout, Qt.AlignCenter)

    def add_buttons(self, layout):
        # Submit query, Clean Query, Last Query
        grid_layout = QtWidgets.QGridLayout()
        grid_layout.setHorizontalSpacing(20)
        grid_layout.setVerticalSpacing(20)

        size = (100, 40)
        submit_button = get_button(label='Submit', action=self.submit_query, size=size, shortcut=Qt.Key_Enter,
                                   color='6CFE87')
        cancel_button = get_button(label='Cancel', action=self.cancel_query, size=size, color='FF8585')
        clear_button = get_button(label='Clear', action=self.clear_fields, size=size, color='B9B9B9')
        back_button = get_button(label='Back', action=self.back_action, size=size, color='B9B9B9')

        grid_layout.addWidget(submit_button, 0, 0, Qt.AlignRight)
        grid_layout.addWidget(cancel_button, 0, 2, Qt.AlignLeft)
        grid_layout.addWidget(clear_button, 2, 0, Qt.AlignRight)
        grid_layout.addWidget(back_button, 2, 2, Qt.AlignLeft)
        layout.addLayout(grid_layout, stretch=True)

    def submit_query(self):
        if not self.searcher.is_running:
            max_tweets = min(max(int(self.max_tweets.text()) if self.max_tweets.text() else 10, 10), 2000000)
            hashtags = list(filter(None, re.split(',\s*', self.hashtags.toPlainText())))
            hashtags = [re.sub('\s', '', h if h.startswith('#') else '#' + h) for h in hashtags]
            keywords = re.split('\s*,\s*', self.keywords.toPlainText())
            query_params = {'hashtags': hashtags,
                            'keywords': keywords,
                            'date_since': self.start_date.dateTime().toString('yyyy-MM-dd'),
                            'date_to': self.end_date.dateTime().addDays(1).toString('yyyy-MM-dd'),
                            'lang': AVAILABLE_LANGS[self.language.currentText()],
                            'max_tweets': max_tweets,
                            'max_results': min(500, max_tweets)}
            self.hashtags.setText(' OR '.join(hashtags))
            self.keywords.setText(' OR '.join(keywords))
            self.searcher.run_query(query_params)
        else:
            self.printer.show_message('Already running another query', 1500, 'error')

    def cancel_query(self):
        self.printer.show_message('Cancel button clicked', 1000, 'success')

    def clear_fields(self):
        self.hashtags.clear()
        self.keywords.clear()
        self.start_date.setDateTime(QtCore.QDateTime.currentDateTime().addDays(-1))
        self.end_date.setDateTime(QtCore.QDateTime.currentDateTime().addDays(-1))
        self.language.setCurrentIndex(0)
        self.max_tweets.clear()
        self.printer.show_message('Clear button clicked', 1000, 'success')

    def back_action(self):
        self.home_window.showMaximized()
        self.close()

    def start_date_dateedit(self):
        if self.start_date.dateTime() > self.end_date.dateTime():
            self.end_date.setDateTime(self.start_date.dateTime())

    def end_date_dateedit(self):
        if self.start_date.dateTime() > self.end_date.dateTime():
            self.start_date.setDateTime(self.end_date.dateTime())

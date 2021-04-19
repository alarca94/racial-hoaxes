from utils.inout import Printer, read_data
from view.window_utils import *


class CleanerWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(CleanerWindow, self).__init__(*args, **kwargs)

        self.setWindowTitle("Twitter Data Cleaner")
        self.row_id = 0

        self.status = QtWidgets.QStatusBar(self)
        self.default_styleSheet = self.status.styleSheet()
        self.setStatusBar(self.status)

        self.printer = Printer(self.status)
        self.data = None

        # -------------- SETTING THE LAYOUTS -------------- #
        gen_layout = get_layout(QtWidgets.QVBoxLayout())
        upper_layout = get_layout(QtWidgets.QHBoxLayout())
        bottom_layout = get_layout(QtWidgets.QHBoxLayout())

        self.add_tweet_viewer(upper_layout)
        self.add_buttons(bottom_layout)

        gen_layout.addLayout(get_layout(QtWidgets.QHBoxLayout()), 15)
        gen_layout.addLayout(upper_layout, 40)
        gen_layout.addLayout(get_layout(QtWidgets.QHBoxLayout()), 10)
        gen_layout.addLayout(bottom_layout, 25)
        gen_layout.addLayout(get_layout(QtWidgets.QHBoxLayout()), 10)

        widget = QtWidgets.QWidget()
        widget.setLayout(gen_layout)

        # Set the central widget of the Window. Widget will expand
        # to take up all the space in the window by default.
        self.setCentralWidget(widget)

    def retrieve_data(self):
        self.data = read_data(stage='clean')

    def update_screen_record(self):
        self.tweet.setText(self.data.iloc[self.row_id].text)
        self.links.setText(self.get_current_links())
        self.id_marker.setText(str(self.row_id))

    def get_current_links(self):
        links = self.data.iloc[self.row_id].urls
        if links:
            return '\n'.join([f'<a href="{l}">Link {i+1}</a>: {l}' for i, l in enumerate(links)])

        return ''

    def add_tweet_viewer(self, layout):
        grid_layout = QtWidgets.QGridLayout()

        labels = []
        self.tweet = QtWidgets.QTextBrowser()
        self.tweet.setAcceptRichText(True)
        self.tweet.setOpenExternalLinks(True)
        self.tweet.setReadOnly(True)
        labels.append(QtWidgets.QLabel('TWEET'))

        self.links = QtWidgets.QTextBrowser()
        self.links.setAcceptRichText(True)
        self.links.setOpenExternalLinks(True)
        self.links.setReadOnly(True)
        labels.append(QtWidgets.QLabel('LINKS'))

        l_height = 50
        for l in labels:
            l.setStyleSheet('background-color:#FAEB7C;color:#000000;font-weight: bold;')
            l.setAlignment(Qt.AlignCenter)
            l.setFixedHeight(l_height)

        grid_layout.addWidget(labels[0], 0, 0)
        grid_layout.addWidget(self.tweet, 1, 0)
        grid_layout.addWidget(labels[1], 0, 1)
        grid_layout.addWidget(self.links, 1, 1)

        layout.addLayout(grid_layout, Qt.AlignCenter)

    def add_buttons(self, layout):
        grid_layout = QtWidgets.QGridLayout()
        grid_layout.setHorizontalSpacing(20)
        grid_layout.setVerticalSpacing(20)

        size = (100, 40)
        self.id_marker = QtWidgets.QLineEdit()
        # self.id_marker.setAcceptRichText(False)
        self.id_marker.setMaximumSize(size[0], size[1])
        self.id_marker.returnPressed.connect(self.go_to_id)
        self.id_marker.setAlignment(Qt.AlignCenter)
        self.id_marker.setEnabled(True)
        prev_button = get_button(label='<<', action=self.get_prev_instance, size=size, shortcut=Qt.Key_Left,
                                 color='B9B9B9')
        next_button = get_button(label='>>', action=self.get_next_instance, size=size, shortcut=Qt.Key_Right,
                                 color='B9B9B9')
        back_button = get_button(label='Back', action=self.back_action, size=size, color='B9B9B9')
        remove_button = get_button(label='Remove', action=self.remove_instance, size=size, color='FF8585')
        commit_button = get_button(label='Commit', action=self.commit_changes, size=None, color='6CFE87')

        grid_layout.addWidget(self.id_marker, 0, 0, 2, 0, Qt.AlignCenter)
        grid_layout.addWidget(prev_button, 2, 0, Qt.AlignRight)
        grid_layout.addWidget(next_button, 2, 2, Qt.AlignLeft)
        grid_layout.addWidget(remove_button, 4, 0, Qt.AlignRight)
        grid_layout.addWidget(back_button, 4, 2, Qt.AlignLeft)
        grid_layout.addWidget(commit_button, 6, 0, 1, 3)
        layout.addLayout(grid_layout)
        layout.addStretch()

    def set_windows(self, windows):
        self.home_window = windows['home']

    def go_to_id(self):
        ix = int(self.id_marker.text())

        if ix > self.data.shape[0] or ix < 0:
            self.printer.show_message('The row id indicated is not valid', 5000, 'error')
        else:
            self.update_id(ix)
            self.update_screen_record()

    def update_id(self, ix):
        self.row_id = ix

    def get_prev_instance(self):
        if self.row_id == 0:
            self.printer.show_message('There is no previous row', 3000, 'error')
        else:
            self.update_id(self.row_id - 1)
            self.update_screen_record()

    def get_next_instance(self):
        if self.row_id == (self.data.shape[0] - 1):
            self.printer.show_message('This is the last record in the file', 3000, 'error')
        else:
            self.update_id(self.row_id + 1)
            self.update_screen_record()

    def back_action(self):
        self.home_window.showMaximized()
        self.close()

    def remove_instance(self):
        self.printer.show_message('Remove button clicked', 1000, 'success')

    def commit_changes(self):
        self.printer.show_message('Commit button clicked', 1000, 'success')

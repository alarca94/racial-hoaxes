import csv
import re

from utils.inout import *
from view.window_utils import *


class AnnotatorWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(AnnotatorWindow, self).__init__(*args, **kwargs)

        self.setWindowTitle("Twitter Data Annotator")
        self.row_id = 0

        self.status = QtWidgets.QStatusBar(self)
        self.default_styleSheet = self.status.styleSheet()
        self.setStatusBar(self.status)

        self.printer = Printer(self.status)
        self.data = None
        self.label_default = {'stereotype': 'none', 'sentiment': 'neutral', 'target': 'none'}

        # -------------- SETTING THE LAYOUTS -------------- #
        gen_layout = get_layout(QtWidgets.QVBoxLayout())
        upper_layout = get_layout(QtWidgets.QVBoxLayout())
        middle_layout = get_layout(QtWidgets.QHBoxLayout())
        bottom_layout = get_layout(QtWidgets.QHBoxLayout())

        self.add_tweet_viewer(upper_layout)
        self.add_labelling_fields(middle_layout)
        self.add_buttons(bottom_layout)

        gen_layout.addLayout(upper_layout, 40)
        gen_layout.addLayout(get_layout(QtWidgets.QHBoxLayout()), 5)
        gen_layout.addLayout(middle_layout, 20)
        gen_layout.addLayout(get_layout(QtWidgets.QHBoxLayout()), 10)
        gen_layout.addLayout(bottom_layout, 20)
        gen_layout.addLayout(get_layout(QtWidgets.QHBoxLayout()), 5)

        widget = QtWidgets.QWidget()
        widget.setLayout(gen_layout)

        # Set the central widget of the Window. Widget will expand
        # to take up all the space in the window by default.
        self.setCentralWidget(widget)

    def retrieve_data(self):
        self.data = read_data(stage='annotate')
        self.data['date'] = pd.to_datetime(self.data['date'].values)
        # If it is the first time annotating the data, add label columns
        if list(self.label_default.keys())[0] not in self.data.columns:
            for col in self.label_default:
                self.data[col] = [self.label_default[col]] * self.data.shape[0]
            self.commit_changes()

    @staticmethod
    def clean_text(text):
        url_regex = '(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?'
        user_regex = '@[\w\d]+'
        text = re.sub(url_regex, '[LINK]', text)
        text = re.sub(user_regex, '[USER]', text)
        text = re.sub('\s+', ' ', text)
        return text

    def update_screen_record(self):
        row = self.data.iloc[self.row_id]
        row.text = self.clean_text(row.text)
        self.tweet.setText(row.text)
        self.links.setText(self.get_current_links(row))
        self.id_marker.setText(str(self.row_id))
        self.stereotype.setCurrentText(row.stereotype)
        self.target.setCurrentText(row.target)
        self.sentiment.setCurrentText(row.sentiment)
        self.likes.setText(str(row.like_count))
        self.quotes.setText(str(row.quote_count))
        self.replies.setText(str(row.reply_count))
        self.retweets.setText(str(row.retweet_count))
        self.date.setText(row.date.strftime('%m-%d-%Y, %H:%M:%S'))
        self.hashtags.setText(',\n'.join([f'#{h}' for h in row.hashtags]))
        self.annotations.setText('\n'.join([f'{a[0]} :: {a[1]}' for a in row.annotations]))
        self.possibly_sensitive.setText(('No', 'Yes')[row.possibly_sensitive])
        if not pd.isna(row.place_name):
            self.place.setText('\n'.join([row.place_name, row.country]))
        else:
            self.place.setText('')

    @staticmethod
    def get_current_links(row):
        links = row.urls
        if links:
            return '<br/>'.join([f'<a href="{l}">Link {i+1}</a>: {l}' for i, l in enumerate(links)])

        return ''

    @staticmethod
    def get_qtextbrowser():
        widget = QtWidgets.QTextBrowser()
        widget.setAcceptRichText(True)
        widget.setOpenExternalLinks(True)
        widget.setReadOnly(True)
        widget.setFixedHeight(150)
        return widget

    def get_qlabel(self, text, font_weight='normal', size=(None, None), alignment=Qt.AlignCenter):
        widget = QtWidgets.QLabel()
        widget.setText(text)
        widget.setAlignment(alignment)
        self.set_labels([widget], '3B3B34', 'FFFFFFFF', size, font_weight, alignment)
        return widget

    @staticmethod
    def set_labels(labels, background_color, color, size, font_weight='bold', alignment=Qt.AlignCenter):
        for l in labels:
            l.setStyleSheet(f'background-color:#{background_color};color:#{color};font-weight:{font_weight};')
            l.setAlignment(alignment)
            if size[0] is not None:
                l.setFixedHeight(size[0])
            if size[1] is not None:
                l.setFixedWidth(size[1])

    def add_tweet_viewer(self, layout):
        grid_layout = QtWidgets.QGridLayout()
        grid_layout2 = QtWidgets.QGridLayout()

        labels = []
        self.tweet = self.get_qtextbrowser()
        labels.append(QtWidgets.QLabel('TWEET'))

        self.links = self.get_qtextbrowser()
        labels.append(QtWidgets.QLabel('LINKS'))

        labels.append(QtWidgets.QLabel('LIKES'))
        labels.append(QtWidgets.QLabel('REPLIES'))
        labels.append(QtWidgets.QLabel('RETWEETS'))
        labels.append(QtWidgets.QLabel('QUOTES'))
        labels.append(QtWidgets.QLabel('DATE'))
        labels.append(QtWidgets.QLabel('POSSIBLY SENSITIVE'))
        labels.append(QtWidgets.QLabel('ANNOTATIONS'))
        labels.append(QtWidgets.QLabel('HASHTAGS'))
        labels.append(QtWidgets.QLabel('PLACE'))

        box_width = None
        self.likes = self.get_qlabel('', font_weight='bold', size=(30, box_width), alignment=Qt.AlignCenter)
        self.replies = self.get_qlabel('', font_weight='bold', size=(30, box_width), alignment=Qt.AlignCenter)
        self.retweets = self.get_qlabel('', font_weight='bold', size=(30, box_width), alignment=Qt.AlignCenter)
        self.quotes = self.get_qlabel('', font_weight='bold', size=(30, box_width), alignment=Qt.AlignCenter)
        self.date = self.get_qlabel('', size=(30, box_width), alignment=Qt.AlignCenter)
        self.possibly_sensitive = self.get_qlabel('', size=(30, box_width), alignment=Qt.AlignCenter)
        self.annotations = self.get_qlabel('', size=(30, box_width), alignment=Qt.AlignCenter)
        self.hashtags = self.get_qlabel('', size=(30, box_width), alignment=Qt.AlignCenter)
        self.place = self.get_qlabel('', size=(30, box_width), alignment=Qt.AlignCenter)

        self.set_labels(labels[:2], background_color='FAEB7C', color='000000', size=(50, None))
        self.set_labels(labels[2:], background_color='FAEB7C', color='000000', size=(30, box_width))

        grid_layout.addWidget(labels[0], 0, 0)
        grid_layout.addWidget(self.tweet, 1, 0)
        grid_layout.addWidget(labels[1], 0, 1)
        grid_layout.addWidget(self.links, 1, 1)
        for i, l in enumerate(labels[2:]):
            grid_layout2.addWidget(l, 0, i)
        extra_widgets = [self.likes, self.replies, self.retweets, self.quotes, self.date, self.possibly_sensitive,
                         self.annotations, self.hashtags, self.place]
        for i, w in enumerate(extra_widgets):
            grid_layout2.addWidget(w, 1, i)

        layout.addLayout(grid_layout, 70)
        layout.addLayout(grid_layout2, 30)

    def add_labelling_fields(self, layout):
        grid_layout = QtWidgets.QGridLayout()
        labels = []

        stereotypes = ['none', '1', '2', '3', '4']
        self.stereotype = QtWidgets.QComboBox()
        self.stereotype.addItems(stereotypes)
        self.stereotype.currentIndexChanged.connect(lambda: self.update_label('stereotype'))
        labels.append(QtWidgets.QLabel('STEREOTYPE'))

        sentiments = ['negative', 'neutral', 'positive']
        self.sentiment = QtWidgets.QComboBox()
        self.sentiment.addItems(sentiments)
        self.sentiment.currentIndexChanged.connect(lambda: self.update_label('sentiment'))
        labels.append(QtWidgets.QLabel('SENTIMENT'))

        targets = ['none', 'individual', 'group']
        self.target = QtWidgets.QComboBox()
        self.target.addItems(targets)
        self.target.currentIndexChanged.connect(lambda: self.update_label('target'))
        labels.append(QtWidgets.QLabel('TARGET'))

        l_height = 50
        for l in labels:
            l.setStyleSheet('background-color:#87D3FC;color:#000000;font-weight: bold;')
            l.setAlignment(Qt.AlignCenter)
            l.setFixedHeight(l_height)

        grid_layout.addWidget(labels[0], 0, 0)
        grid_layout.addWidget(self.stereotype, 1, 0)
        grid_layout.addWidget(labels[1], 0, 1)
        grid_layout.addWidget(self.sentiment, 1, 1)
        grid_layout.addWidget(labels[2], 0, 2)
        grid_layout.addWidget(self.target, 1, 2)

        layout.addLayout(grid_layout, Qt.AlignCenter)

    def update_label(self, field):
        self.data.loc[self.row_id, field] = eval(f'self.{field}.currentText()')

    def reset_labels(self):
        self.stereotype.setCurrentText(self.label_default['stereotype'])
        self.sentiment.setCurrentText(self.label_default['sentiment'])
        self.target.setCurrentText(self.label_default['target'])

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
        commit_button = get_button(label='Commit', action=self.commit_changes, size=size, color='6CFE87')

        grid_layout.addWidget(self.id_marker, 0, 0, 2, 0, Qt.AlignCenter)
        grid_layout.addWidget(prev_button, 2, 0, Qt.AlignRight)
        grid_layout.addWidget(next_button, 2, 2, Qt.AlignLeft)
        grid_layout.addWidget(commit_button, 4, 0, Qt.AlignRight)
        grid_layout.addWidget(back_button, 4, 2, Qt.AlignLeft)
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

    def commit_changes(self):
        self.data.to_csv(os.path.join(DATA_PATH, ANNOTATE_FILE), index=False, quoting=csv.QUOTE_ALL)

from view.window_utils import *
from utils.inout import *


class HomeWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(HomeWindow, self).__init__(*args, **kwargs)

        self.setWindowTitle("Racial Hoaxes App")

        self.status = QtWidgets.QStatusBar(self)
        self.default_styleSheet = self.status.styleSheet()
        self.setStatusBar(self.status)
        self.printer = Printer(self.status)

        gen_layout = get_layout(QtWidgets.QVBoxLayout())

        grid_layout = get_grid(spacing=400)
        grid_layout2 = get_grid(spacing=20)

        size = (200, 80)
        download_button = get_button(label='DOWNLOADER', size=size, action=self.get_downloader_window, color='FAEB7C')
        clean_button = get_button(label='CLEANER', size=size, action=self.get_cleaner_window, color='FAEB7C')
        annotate_button = get_button(label='ANNOTATOR', size=size, action=self.get_labeler_window, color='FAEB7C')

        grid_layout.addWidget(download_button, 0, 0)
        grid_layout.addWidget(clean_button, 0, 1)
        grid_layout2.addWidget(annotate_button, 0, 0)

        gen_layout.addLayout(grid_layout,  50)
        gen_layout.addLayout(grid_layout2, 50)

        widget = QtWidgets.QWidget()
        widget.setLayout(gen_layout)

        self.setCentralWidget(widget)

    def set_windows(self, windows):
        self.downloader_window = windows['download']
        self.cleaner_window = windows['cleaner']
        self.annotator_window = windows['annotator']

    def get_downloader_window(self):
        self.downloader_window.showMaximized()
        self.close()

    def get_cleaner_window(self):
        if os.path.isfile(os.path.join(DATA_PATH, DOWNLOAD_FILE)):
            self.cleaner_window.retrieve_data()
            self.cleaner_window.update_screen_record()
            self.cleaner_window.showMaximized()
            self.close()
        else:
            self.printer.show_message('Please, download data from twitter before attempting to clean it', 3000, 'error')

    def get_labeler_window(self):
        if os.path.isfile(os.path.join(DATA_PATH, CLEAN_FILE)):
            self.annotator_window.retrieve_data()
            self.annotator_window.update_screen_record()
            self.annotator_window.showMaximized()
            self.close()
        else:
            self.printer.show_message('Please, clean data from twitter before attempting to label it', 3000, 'error')

import sys
from PyQt6 import QtWidgets, QtGui, QtCore

class LinuxWhispererTray(QtWidgets.QSystemTrayIcon):
    def __init__(self, app, main_window, icon=None):
        if icon is None:
            icon = QtGui.QIcon()
        super().__init__(icon, parent=app)
        self.app = app
        self.main_window = main_window
        self.setToolTip('Linux Whisperer')
        self.menu = QtWidgets.QMenu()

        self.action_show = QtGui.QAction('Show', self.menu)
        self.action_hide = QtGui.QAction('Hide', self.menu)
        self.action_quit = QtGui.QAction('Quit', self.menu)

        self.menu.addAction(self.action_show)
        self.menu.addAction(self.action_hide)
        self.menu.addSeparator()
        self.menu.addAction(self.action_quit)
        self.setContextMenu(self.menu)

        self.action_show.triggered.connect(self.main_window.show)
        self.action_hide.triggered.connect(self.main_window.hide)
        self.action_quit.triggered.connect(self.quit_app)

    def quit_app(self):
        self.app.quit()

class LinuxWhispererMainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Linux Whisperer')
        self.setGeometry(100, 100, 400, 200)
        self.status_label = QtWidgets.QLabel('Status: Idle', self)
        self.status_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.setCentralWidget(self.status_label)
        # Add more widgets/controls as needed

    def set_status(self, text):
        self.status_label.setText(f'Status: {text}')


def run_qt_ui():
    app = QtWidgets.QApplication(sys.argv)
    main_window = LinuxWhispererMainWindow()
    tray_icon = LinuxWhispererTray(app, main_window, icon=main_window.windowIcon())
    tray_icon.show()
    main_window.show()
    sys.exit(app.exec())

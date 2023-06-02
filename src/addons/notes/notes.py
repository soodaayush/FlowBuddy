import os
import json

from PyQt5.QtCore import Qt, QPoint, pyqtSignal
from PyQt5.QtWidgets import (
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QShortcut,
    QTabWidget,
    QSizePolicy,
    QInputDialog,
    QMessageBox,
)
from PyQt5.QtGui import (
    QTextCursor,
    QPainter,
    QPen,
    QColor,
    QKeySequence,
)

from addon import AddOnBase

from ui.dialog import ConfirmationDialog
from ui.custom_button import RedButton, GrnButton
from ui.settings import UI_SCALE
from ui.utils import get_font


class NoteTab(QTextEdit):
    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path
        self.load_text_from_file()
        self.setFont(get_font(size=16))
        self.textChanged.connect(self.save_text_to_file)
        self.save_text_to_file()
        self.setAcceptRichText(False)
        self.setStyleSheet(
            """
            QTextEdit {
                padding: 24px;
                border: none;
            }
        """
        )

    def load_text_from_file(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, "r") as file:
                self.setPlainText(file.read())
            self.moveCursor(QTextCursor.End)

    def save_text_to_file(self):
        with open(self.file_path, "w") as file:
            file.write(self.toPlainText())


class CustomTabWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # self.addTabButton = QToolButton(self)
        self.addTabButton = GrnButton(self)
        # self.addTabButton.setText("+")
        self.addTabButton.clicked.connect(parent.add_new_tab)

    def movePlusButton(self, no_of_tabs=0):
        """Move the plus button to the correct location."""
        w = self.count()
        self.addTabButton.move(w * 100, 0)


class JottingDownWindow(QWidget):
    window_toggle_signal = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        self.window_toggle_signal.connect(self.toggle_window)

        self.notes_folder = "addons/notes/data"
        if not os.path.exists(self.notes_folder):
            os.makedirs(self.notes_folder)

        self.config_file = os.path.join(self.notes_folder, "config.json")
        self.tab_widget = CustomTabWidget(self)
        self.tab_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(10)
        self.setLayout(layout)

        layout.addWidget(self.tab_widget)

        self.load_tabs()

        new_tab_shortcut = QShortcut(QKeySequence("Ctrl+T"), self)
        new_tab_shortcut.activated.connect(self.add_new_tab)

        self.setStyleSheet(
            """
            QWidget {
                background-color: white;
                border: 2px solid #DADADA;
                border-radius: 12px;
            }
        """
        )
        self.setFixedSize(900 * int(UI_SCALE), 900 * int(UI_SCALE))
        self.old_pos = None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor("#DADADA"), 2))
        painter.setBrush(QColor("white"))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 12, 12)

    def load_tabs(self):
        # Load existing .txt files in the notes folder as tabs
        if os.path.exists(self.config_file):
            with open(self.config_file, "r") as file:
                config = json.load(file)

            # Load tabs based on the order in config["files"]
            for tabno, file_path in enumerate(config["files"]):
                if os.path.exists(file_path):
                    file_name = os.path.basename(file_path)
                    self.tab_widget.addTab(NoteTab(file_path), file_name)
                    self.add_button_to_tab(tabno)

            self.tab_widget.setCurrentIndex(config["last_active"])
        else:
            # If config file doesn't exist, load tabs by iterating
            # over files in the notes folder

            for tabno, file_name in enumerate(os.listdir(self.notes_folder)):
                if file_name.endswith(".txt"):
                    file_path = os.path.join(self.notes_folder, file_name)
                    self.tab_widget.addTab(NoteTab(file_path), file_name)
                    self.add_button_to_tab(tabno)
            # If no tabs are found after loading existing .txt files, add the
            #  default "notes" file
        if self.tab_widget.count() == 0:
            self.add_new_tab("notes")
        self.tab_widget.movePlusButton()

    def add_button_to_tab(self, tabno):
        self.button = RedButton(self.tab_widget, "radial")
        self.tab_widget.tabBar().setTabButton(tabno, 2, self.button)
        tab_text = self.tab_widget.tabBar().tabText(tabno)
        self.button.clicked.connect(lambda: self.delete_tab(tab_text))

    def save_tabs(self):
        config = {
            "files": [
                self.notes_folder + "/" + self.tab_widget.tabText(i)
                for i in range(self.tab_widget.count())
            ],
            "last_active": self.tab_widget.currentIndex(),
        }
        with open(self.config_file, "w") as file:
            json.dump(config, file)

    def delete_tab_text_file(self, file_name):
        file_path = os.path.join(self.notes_folder, file_name)
        if os.path.exists(file_path):
            os.remove(file_path)
        else:
            QMessageBox.warning(self, "File Exists", f"{file_path} does not exist.")

    def delete_tab(self, tab_text):
        tabid = self.get_tab_number_from_text(tab_text)
        file_name = self.tab_widget.tabText(tabid)
        dialog = ConfirmationDialog(f"Delete tab {file_name}?")
        res = dialog.exec()
        if not res:
            return
        self.tab_widget.removeTab(tabid)
        self.delete_tab_text_file(file_name)
        self.tab_widget.movePlusButton()
        self.save_tabs()

    def get_tab_number_from_text(self, tab_text):
        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabText(i) == tab_text:
                return i
        return -1

    def add_new_tab(self, file_name=""):
        if not file_name:
            file_name, ok = QInputDialog.getText(
                self, "New Note", "Enter the note name:"
            )
            if not ok or not file_name:
                return
        file_name = f"{file_name}.txt"

        file_path = os.path.join(self.notes_folder, file_name)
        if not os.path.exists(file_path):
            self.tab_widget.addTab(NoteTab(file_path), file_name)
            self.add_button_to_tab(len(self.tab_widget) - 1)
            self.tab_widget.movePlusButton()
            self.save_tabs()

        else:
            QMessageBox.warning(
                self, "File Exists", f"A file with the name {file_name} already exists."
            )

    def toggle_window(self) -> None:
        if self.isHidden():
            window.show()
            window.activateWindow()
            if current_widget := self.tab_widget.currentWidget():
                current_widget.setFocus()
        else:
            window.hide()


    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if not self.old_pos:
            return
        delta = QPoint(event.globalPos() - self.old_pos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = None

    def closeEvent(self, event):
        self.save_tabs()


window = JottingDownWindow()

AddOnBase().set_shortcut("<ctrl>+`", window.window_toggle_signal.emit)
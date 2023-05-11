from __future__ import annotations
import webbrowser
from typing import Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
    QLayout,
    QApplication
)


import SaveFile as Data
from FileSystem import open_file

from .base_window import BaseWindow
from .utils import get_font
from .custom_button import RedButton, GrnButton, YelButton, TextButton
from .dialog import TaskDialog, GroupDialog, ConfirmationDialog, ACCEPTED, REJECTED


NAME_TO_INT = {
    "group_layout": 0,
}


class BaseNode(QWidget):
    def __init__(self, parent: MainWindow, group_name: str) -> None:
        super().__init__(parent)

        self._parent = parent
        
        self._group_name = group_name
        
        self._layout = QHBoxLayout(self)
        self.setLayout(self._layout)
        self._layout.setSpacing(0)
        

class GroupNode(BaseNode):
    def __init__(self, parent: QWidget, group_name: str) -> None:
        super().__init__(parent, group_name)

        self._layout.setContentsMargins(0, 25, 0, 0)
        
        self._name_label = QLabel(group_name, self)
        self._name_label.setFont(get_font(size=24, weight="semibold"))

        new_task_button = GrnButton(self, "radial")
        edit_group_button = YelButton(self, "radial")
        delete_group_button = RedButton(self, "radial")
        new_task_button.clicked.connect(self.on_new_task)
        edit_group_button.clicked.connect(self.on_edit_group)
        delete_group_button.clicked.connect(self.on_delete_group)
        
        self._parent.add_to_editors(new_task_button, edit_group_button, delete_group_button)
        
        self._layout.addWidget(self._name_label)
        self._layout.addSpacing(10)
        self._layout.addWidget(new_task_button)
        self._layout.addSpacing(7)
        self._layout.addWidget(edit_group_button)
        self._layout.addSpacing(7)
        self._layout.addWidget(delete_group_button)
        self._layout.addStretch()
        
    def on_new_task(self, event) -> None:
        self._parent.add_task(self._group_name)
    
    def on_edit_group(self, event) -> None:
        dialog = GroupDialog(self)
        dialog.for_edit(self._group_name)
        dialog.setTitle("Edit Group")
        if dialog.exec() != REJECTED:
            group_name = dialog.result()
            Data.edit_group(self._group_name, new_group_name=group_name)
            self._name_label.setText(group_name)
    
    def on_delete_group(self, event) -> None:
        self.delete()
        
    def delete(self):
        dialog = ConfirmationDialog(f"Delete '{self._group_name}'?", self)
        if dialog.exec() == ACCEPTED:
            Data.delete_group(self._group_name)
            self._parent.clear_group(self._group_name)
            QApplication.instance().processEvents()
            self._parent.update()
            self._parent.adjustSize()
            

class TaskNode(BaseNode):
    def __init__(self,
                 parent: QWidget,
                 group_name: str = None,
                 task_name: str = None,
                 button_text: Optional[str] = None,
                 url: Optional[str] = None,
                 file_path: Optional[str] = None) -> None:
        super().__init__(parent, group_name)
        
        self._task_name = task_name
        self._button_text = button_text
        self._url = url
        self._file_path = file_path

        self._text_button = None
        
        self._layout.setContentsMargins(0, 12, 0, 0)
        
        self._name_label = QLabel(task_name, self)
        self._name_label.setFont(get_font(size=16))
        self._layout.addWidget(self._name_label)
        self._layout.addSpacing(10)
        
        self._text_button = TextButton(self, self._button_text)
        self._text_button.setFont(get_font(size=16))
        self._text_button.clicked.connect(self.on_text_button)
        self._layout.addWidget(self._text_button)
        self._layout.addSpacing(10)
        if self._button_text is None:
            self._text_button.hide()

        edit_group_button = YelButton(self, "radial")
        delete_group_button = RedButton(self, "radial")
        
        edit_group_button.clicked.connect(self.on_edit_task)
        delete_group_button.clicked.connect(self.on_delete_task)
        
        self._parent.add_to_editors(edit_group_button, delete_group_button)
        
        self._layout.addWidget(edit_group_button)
        self._layout.addSpacing(7)
        self._layout.addWidget(delete_group_button)
        self._layout.addStretch()
        
        
    def on_edit_task(self, event) -> None:
        dialog = TaskDialog(self)
        dialog.for_edit(self._task_name, self._button_text, self._url, self._file_path)
        dialog.setTitle("Edit Task")
        if dialog.exec() != REJECTED:
            self._edit_data(dialog)
            self._parent.update()
            self._parent.adjustSize()

    def on_delete_task(self, event) -> None:
        self.delete()
    
    def on_text_button(self, evet) -> None:
        if self._url is not None:
            [webbrowser.open(url.strip()) for url in self._url.split(",")]
        if self._file_path is not None:
            open_file(self._file_path)
    
    
    def _edit_data(self, dialog: TaskDialog) -> None:
        task_name, button_text, url, file_path = dialog.result()
        Data.edit_task(self._group_name, self._task_name, new_task_name=task_name, new_task_data={
            "button_text": button_text,
            "url": url,
            "file_path": file_path,
        })

        self._name_label.setText(task_name)
        if button_text is not None:
            if self._text_button.isHidden(): self._text_button.show()
            self._text_button.setText(button_text)
        elif not self._text_button.isHidden():
            self._text_button.hide()
        QApplication.instance().processEvents()
        self.update()
        self.adjustSize()
        self._parent.update()
        self._parent.adjustSize()
        self._task_name = task_name
        self._button_text = button_text
        self._url = url
        self._file_path = file_path
        
    def delete(self) -> None:
        dialog = ConfirmationDialog(f"Delete '{self._task_name}' from '{self._group_name}'?", self)
        if dialog.exec() == ACCEPTED:
            Data.delete_task(self._group_name, self._task_name)
            self._parent.clearLayout(self.layout())
            QApplication.instance().processEvents()
            self._parent.update()
            self._parent.adjustSize()
        

class MainWindow(BaseWindow):
    window_toggle_signal = pyqtSignal()
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(True, parent)
        
        self._edit_mode = False
        self._editors: list[QWidget] = []
        self._nodes = {}
        
        self.window_toggle_signal.connect(self.toggle_window)
        
        self.setLayout(layout:=QVBoxLayout())
        layout.setAlignment(Qt.AlignTop)
        

        for group_name in Data.get_name_list():
            self.create_group(group_name)

            for task_name in Data.get_name_list(group_name):

                button_text = Data.task_property(group_name, task_name, "button_text")
                url = Data.task_property(group_name, task_name, "url")
                file_path = Data.task_property(group_name, task_name, "file_path")

                self.create_task(group_name, task_name, button_text, url, file_path)


        layout.addStretch()
        layout.addSpacing(25)
        layout.addLayout(add_group_layout := QHBoxLayout())
        add_group_layout.setAlignment(Qt.AlignTop)

        add_group_label = QLabel("Add New Group", self)
        add_group_label.setFont(get_font(size=24, weight="semibold"))
        add_group_label.setStyleSheet("color: #ABABAB")
        
        add_group_button = GrnButton(self, "radial")
        add_group_button.clicked.connect(self.add_group)

        add_group_layout.addWidget(add_group_label)
        add_group_layout.addSpacing(10)
        add_group_layout.addWidget(add_group_button)
        add_group_layout.addStretch()
        
        self.add_to_editors(add_group_button, add_group_label)
        
        if (position := Data.setting("position")) is not None:
            self.move(position[0], position[1])
        self.toggle_edit_mode(False)
        self.animate = True
        QApplication.instance().processEvents()
        self.adjustSize()


    def toggle_window(self) -> None:
        if self.isHidden():
            self.setFixedSize(1, 1)
            self.show()
            self.adjustSize()
        else:
            self.hide()
    
    
    def add_group(self) -> None:
        dialog = GroupDialog(self)
        if dialog.exec() != REJECTED:
            group_name = dialog.result()
            Data.add_group(group_name)
            self.create_group(group_name)

    def create_group(self, group_name: str) -> None:
        group_layout = QVBoxLayout()
        group_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.layout().insertLayout(len(self._nodes), group_layout)
        group_layout.addWidget(group_node:=GroupNode(self, group_name))
        group_node.on_new_task = self.add_task
        group_node.delete_group_layer = self.delete_group_layer
        group_node.add_to_editors = self.add_to_editors
        self._nodes[group_name] = {0: group_layout}
        QApplication.instance().processEvents()
        self.update()
        self.adjustSize()

    def clear_group(self, group_name: str) -> None:
        self.clearLayout(self._nodes[group_name][NAME_TO_INT["group_layout"]])

    def delete_group_layer(self, group_name: str) -> None:
        self.clearLayout(self._nodes[group_name][NAME_TO_INT["group_layout"]])
        del self._nodes[group_name]
        QApplication.instance().processEvents()
        self.update()
        self.adjustSize()


    def add_task(self, group_name: str) -> None:
        dialog = TaskDialog(self)
        if dialog.exec() != REJECTED:
            task_name, button_text, url, file_path = dialog.result()
            Data.add_task(group_name, task_name)
            Data.edit_task(group_name, task_name, new_task_data={
                "button_text": button_text,
                "url": url,
                "file_path": file_path
            })
            
            self.create_task(group_name, task_name, button_text, url, file_path)
    
    def create_task(self, group_name: str, task_name: str, button_text: str, url: str, file_path: str) -> None:
        task_node = TaskNode(self, group_name, task_name, button_text, url, file_path)
        task_node.add_to_editors = self.add_to_editors
        self._nodes[group_name][NAME_TO_INT["group_layout"]].addWidget(task_node)
        self._nodes[group_name][task_name] = task_node
        QApplication.instance().processEvents()
        self.update()
        self.adjustSize()


    def clearLayout(self, layout: QLayout) -> None:
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.hide()
                    widget.deleteLater()
                else:
                    self.clearLayout(item.layout())
            layout.deleteLater()
        QApplication.instance().processEvents()
        
        
    def add_to_editors(self, *widgets: QWidget) -> None:
        self._editors += [*widgets]
        
    def on_edit_button_clicked(self, event) -> None:
        self.toggle_edit_mode()
        QApplication.instance().processEvents()
        self.adjustSize()
        return super().on_edit_button_clicked(event)

    def toggle_edit_mode(self, mode: Optional[bool] = None) -> None:
        self._edit_mode = not self._edit_mode if mode is None else mode
        for widget in self._editors:
            try:
                widget.setHidden(not self._edit_mode)
            except Exception:
                self._editors.remove(widget)

        QApplication.instance().processEvents()
        
    
    def mouseReleaseEvent(self, a0: QMouseEvent) -> None:
        Data.setting("position", [self.pos().x(), self.pos().y()])
        return super().mouseReleaseEvent(a0)
    
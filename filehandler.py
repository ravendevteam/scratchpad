import sys
import os
import re
import requests
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTextEdit, QAction, 
                             QFileDialog, QMessageBox, QStatusBar, QDialog, 
                             QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout)
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QIcon

class FileHandler(QThread):
    """Thread for handling file operations."""
    file_content_loaded = pyqtSignal(str, str)
    file_saved = pyqtSignal(bool)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path

    def run(self):
        """Read the content of the file."""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            self.file_content_loaded.emit(content, 'UTF-8')
        except Exception as e:
            self.file_content_loaded.emit(f"Error reading file: {e}", '')

    def save(self, content):
        """Save the content to the specified file."""
        try:
            with open(self.file_path, 'w', encoding='utf-8') as file:
                file.write(content)
            self.file_saved.emit(True)
        except Exception as e:
            self.file_saved.emit(False)

    def find_next(self):
        """Find the next occurrence of the text."""
        text_to_find = self.find_input.text()
        if text_to_find:
            cursor = self.text_edit.textCursor()
            cursor = self.text_edit.find(text_to_find, cursor)

            if cursor.isNull():
                QMessageBox.information(self, "Not Found", "No more occurrences found.")
                self.current_index = 0
            else:
                self.text_edit.setTextCursor(cursor)

    def replace(self):
        """Replace the current occurrence."""
        text_to_find = self.find_input.text()
        text_to_replace = self.replace_input.text()
        if text_to_find and text_to_replace:
            content = self.text_edit.toPlainText()
            self.text_edit.setPlainText(content.replace(text_to_find, text_to_replace, 1))

    def replace_all(self):
        """Replace all occurrences."""
        text_to_find = self.find_input.text()
        text_to_replace = self.replace_input.text()
        if text_to_find and text_to_replace:
            content = self.text_edit.toPlainText()
            self.text_edit.setPlainText(content.replace(text_to_find, text_to_replace))
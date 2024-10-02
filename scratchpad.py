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

import findreplace
import mainwindow

class ImportFromWebDialog(QDialog):
    """Dialog for importing content from the web using a URL."""
    def __init__(self, text_edit):
        super().__init__()
        self.text_edit = text_edit
        self.setWindowTitle("Import From Web")

        icon_path = os.path.join(os.path.dirname(__file__), 'icons', 'scratchpad.png')
        if getattr(sys, 'frozen', False):
            icon_path = os.path.join(sys._MEIPASS, 'icons', 'scratchpad.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.layout = QVBoxLayout(self)

        self.url_label = QLabel("Enter URL:")
        self.url_input = QLineEdit(self)
        self.layout.addWidget(self.url_label)
        self.layout.addWidget(self.url_input)

        self.fetch_button = QPushButton("Fetch", self)
        self.layout.addWidget(self.fetch_button)

        self.fetch_button.clicked.connect(self.fetch_from_web)

        self.setLayout(self.layout)

    def fetch_from_web(self):
        """Fetch the content from the provided URL and display it in the text editor."""
        url = self.url_input.text().strip()

        if self.is_valid_url(url):
            try:
                response = requests.get(url)
                response.raise_for_status()
                self.text_edit.setPlainText(response.text)
                self.accept()
            except requests.exceptions.RequestException as e:
                QMessageBox.critical(self, "Error", f"Failed to fetch content: {e}")
        else:
            QMessageBox.warning(self, "Invalid URL", "Please enter a valid HTTPS URL.")

    def is_valid_url(self, url):
        """Check if the provided URL is a valid HTTPS URL."""
        regex = re.compile(
            r'^(https:\/\/)'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'
            r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return re.match(regex, url) is not None
    
class UnsavedWorkDialog(QDialog):
    """Dialog for warning about unsaved changes."""
    def __init__(self, parent=None):
        super().__init__()
        self.setWindowTitle("Unsaved Changes")

        icon_path = os.path.join(os.path.dirname(__file__), 'icons', 'scratchpad.png')
        if getattr(sys, 'frozen', False):
            icon_path = os.path.join(sys._MEIPASS, 'icons', 'scratchpad.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.layout = QVBoxLayout(self)

        self.message_label = QLabel("You have unsaved changes. What would you like to do?")
        self.layout.addWidget(self.message_label)

        self.button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Save Changes", self)
        self.cancel_button = QPushButton("Cancel", self)
        self.discard_button = QPushButton("Discard Changes", self)

        self.button_layout.addWidget(self.save_button)
        self.button_layout.addWidget(self.cancel_button)
        self.button_layout.addWidget(self.discard_button)

        self.layout.addLayout(self.button_layout)

        self.save_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        self.discard_button.clicked.connect(self.discard_changes)

        self.setLayout(self.layout)

    def discard_changes(self):
        """Handle discard changes action."""
        self.reject()
        QApplication.quit()

    def accept(self):
        """Override accept method to save changes before closing."""
        super().accept()

    def reject(self):
        """Override reject method to handle canceling."""
        super().reject()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    scratchpad = mainwindow.Scratchpad()
    scratchpad.show()
    sys.exit(app.exec_())

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

class FindReplaceDialog(QDialog):
    """Dialog for Find and Replace functionality."""
    def __init__(self, text_edit):
        super().__init__()
        self.text_edit = text_edit
        self.setWindowTitle("Find and Replace")

        icon_path = os.path.join(os.path.dirname(__file__), 'icons', 'scratchpad.png')
        if getattr(sys, 'frozen', False):
            icon_path = os.path.join(sys._MEIPASS, 'icons', 'scratchpad.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.layout = QVBoxLayout(self)

        self.find_label = QLabel("Find:")
        self.find_input = QLineEdit(self)
        self.layout.addWidget(self.find_label)
        self.layout.addWidget(self.find_input)

        self.replace_label = QLabel("Replace with:")
        self.replace_input = QLineEdit(self)
        self.layout.addWidget(self.replace_label)
        self.layout.addWidget(self.replace_input)

        self.button_layout = QHBoxLayout()
        self.find_button = QPushButton("Find Next", self)
        self.replace_button = QPushButton("Replace", self)
        self.replace_all_button = QPushButton("Replace All", self)

        self.button_layout.addWidget(self.find_button)
        self.button_layout.addWidget(self.replace_button)
        self.button_layout.addWidget(self.replace_all_button)

        self.layout.addLayout(self.button_layout)

        self.find_button.clicked.connect(self.find_next)
        self.replace_button.clicked.connect(self.replace)
        self.replace_all_button.clicked.connect(self.replace_all)

        self.setLayout(self.layout)

        self.current_index = 0

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


class Scratchpad(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_file = None
        self.file_handler = None
        self.unsaved_changes = False
        self.initUI()

    def initUI(self):
        """Initialize the UI components."""
        self.setWindowTitle('Scratchpad - Unnamed')
        self.setGeometry(100, 100, 800, 600)

        icon_path = os.path.join(os.path.dirname(__file__), 'icons', 'scratchpad.png')
        if getattr(sys, 'frozen', False):
            icon_path = os.path.join(sys._MEIPASS, 'icons', 'scratchpad.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print(f"Icon file not found: {icon_path}")

        self.textEdit = QTextEdit(self)
        self.setCentralWidget(self.textEdit)

        self.statusBar = QStatusBar(self)
        self.setStatusBar(self.statusBar)

        self.line = 1
        self.column = 1
        self.char_count = 0
        self.encoding = "UTF-8"
        
        self.textEdit.cursorPositionChanged.connect(self.updateStatusBar)
        
        self.createMenu()
        self.loadStyle()
        self.setMenuIcons()

        self.textEdit.textChanged.connect(self.on_text_changed)

    def on_text_changed(self):
        """Update the unsaved changes flag when text is modified."""
        self.unsaved_changes = True

    def closeEvent(self, event):
        if self.textEdit.document().isModified():
            dialog = UnsavedWorkDialog(self)
            result = dialog.exec_()

            if result == QDialog.Accepted:
                self.saveFile()
                event.accept()
            elif result == QDialog.Rejected:
                event.ignore()
            elif result == QDialog.Discarded:
                event.accept()

    def loadStyle(self):
        """Load CSS styles from 'spstyle.css' in the user's home directory if available, otherwise use 'style.css' from the package."""
        user_css_path = os.path.join(os.path.expanduser("~"), "spstyle.css")

        if os.path.exists(user_css_path):
            try:
                with open(user_css_path, 'r') as css_file:
                    self.setStyleSheet(css_file.read())
                print(f"Loaded user CSS style from: {user_css_path}")
            except Exception as e:
                print(f"Error loading user CSS: {e}")

        else:
            css_file_path = os.path.join(os.path.dirname(__file__), 'style.css')
            if getattr(sys, 'frozen', False):
                css_file_path = os.path.join(sys._MEIPASS, 'style.css')

            try:
                with open(css_file_path, 'r') as css_file:
                    self.setStyleSheet(css_file.read())
            except FileNotFoundError:
                print(f"Default CSS file not found: {css_file_path}")

    def createMenu(self):
        """Create the menu bar and connect actions."""
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')

        self.createFileActions(fileMenu)
        editMenu = menubar.addMenu('&Edit')

        self.createEditActions(editMenu)

    def createFileActions(self, menu):
        """Create file actions and add them to the given menu."""
        self.actions = {}

        newAction = QAction('New', self)
        newAction.setShortcut('Ctrl+N')
        newAction.triggered.connect(self.newFile)
        menu.addAction(newAction)
        self.actions['new'] = newAction

        openAction = QAction('Open...', self)
        openAction.setShortcut('Ctrl+O')
        openAction.triggered.connect(self.openFile)
        menu.addAction(openAction)
        self.actions['open'] = openAction

        saveAction = QAction('Save', self)
        saveAction.setShortcut('Ctrl+S')
        saveAction.triggered.connect(self.saveFile)
        menu.addAction(saveAction)
        self.actions['save'] = saveAction

        saveAsAction = QAction('Save As...', self)
        saveAsAction.triggered.connect(self.saveFileAs)
        menu.addAction(saveAsAction)
        self.actions['saveas'] = saveAsAction

        importFromWebAction = QAction('Import From Web', self)
        importFromWebAction.triggered.connect(self.importFromWeb)
        menu.addAction(importFromWebAction)
        self.actions['importfromweb'] = importFromWebAction

        exitAction = QAction('Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.triggered.connect(self.close)
        menu.addAction(exitAction)
        self.actions['exit'] = exitAction

    def createEditActions(self, menu):
        """Create edit actions and add them to the given menu."""
        undoAction = QAction('Undo', self)
        undoAction.setShortcut('Ctrl+Z')
        undoAction.triggered.connect(self.textEdit.undo)
        menu.addAction(undoAction)
        self.actions['undo'] = undoAction

        redoAction = QAction('Redo', self)
        redoAction.setShortcuts(['Ctrl+Y', 'Ctrl+Shift+Z'])
        redoAction.triggered.connect(self.textEdit.redo)
        menu.addAction(redoAction)
        self.actions['redo'] = redoAction

        cutAction = QAction('Cut', self)
        cutAction.setShortcut('Ctrl+X')
        cutAction.triggered.connect(self.textEdit.cut)
        menu.addAction(cutAction)
        self.actions['cut'] = cutAction

        copyAction = QAction('Copy', self)
        copyAction.setShortcut('Ctrl+C')
        copyAction.triggered.connect(self.textEdit.copy)
        menu.addAction(copyAction)
        self.actions['copy'] = copyAction

        pasteAction = QAction('Paste', self)
        pasteAction.setShortcut('Ctrl+V')
        pasteAction.triggered.connect(self.textEdit.paste)
        menu.addAction(pasteAction)
        self.actions['paste'] = pasteAction

        selectAllAction = QAction('Select All', self)
        selectAllAction.setShortcut('Ctrl+A')
        selectAllAction.triggered.connect(self.textEdit.selectAll)
        menu.addAction(selectAllAction)
        self.actions['selectall'] = selectAllAction

        findReplaceAction = QAction('Find and Replace...', self)
        findReplaceAction.triggered.connect(self.openFindReplaceDialog)
        menu.addAction(findReplaceAction)
        self.actions['findreplace'] = findReplaceAction

    def setMenuIcons(self):
        """Set icons for menu actions if available in the icons folder."""
        print(os.name)
        icons_folder = os.path.join(os.path.dirname(__file__), 'icons')
        if getattr(sys, 'frozen', False):
            icons_folder = os.path.join(sys._MEIPASS, 'icons')
        icon_files = {
            'copy': 'copy.png',
            'cut': 'cut.png',
            'exit': 'exit.png',
            'findreplace': 'findreplace.png',
            'importfromweb': 'importfromweb.png',
            'new': 'new.png',
            'open': 'open.png',
            'paste': 'paste.png',
            'redo': 'redo.png',
            'save': 'save.png',
            'saveas': 'saveas.png',
            'selectall': 'selectall.png',
            'undo': 'undo.png'
        }

        for action_name, icon_filename in icon_files.items():
            icon_path = os.path.join(icons_folder, icon_filename)
            if os.path.isfile(icon_path):
                self.actions[action_name].setIcon(QIcon(icon_path))

    def openFindReplaceDialog(self):
        """Open the find and replace dialog."""
        dialog = FindReplaceDialog(self.textEdit)
        dialog.exec_()

    def importFromWeb(self):
        """Open the dialog to import content from the web."""
        dialog = ImportFromWebDialog(self.textEdit)
        dialog.exec_()

    def newFile(self):
        """Create a new file."""
        self.current_file = None
        self.textEdit.clear()
        self.setWindowTitle('Scratchpad - Unnamed')

    def openFile(self):
        """Open a file for editing."""
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Open File", "", "Text Files (*.txt);;All Files (*)", options=options)
        if file_name:
            self.current_file = file_name
            self.file_handler = FileHandler(file_name)
            self.file_handler.file_content_loaded.connect(self.loadFileContent)
            self.file_handler.start()

    def loadFileContent(self, content, encoding):
        """Load the content into the text edit."""
        if encoding:
            self.encoding = encoding
        self.textEdit.setPlainText(content)
        self.setWindowTitle(f'Scratchpad - {os.path.basename(self.current_file)}')

    def saveFile(self):
        """Save the current file."""
        if self.current_file:
            self.file_handler = FileHandler(self.current_file)
            self.file_handler.file_saved.connect(self.handleSaveFile)
            self.file_handler.save(self.textEdit.toPlainText())
        else:
            self.saveFileAs()

    def handleSaveFile(self, success):
        """Handle the result of the save operation."""
        if success:
            self.unsaved_changes = False
            self.updateStatusBar()
        else:
            QMessageBox.warning(self, "Error", "Failed to save file!")

    def saveFileAs(self):
        """Save the current file as a new file."""
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Save File As", "", "Text Files (*.txt);;All Files (*)", options=options)
        if file_name:
            self.current_file = file_name
            self.saveFile()

    def updateStatusBar(self, after_save=False):
        """Update the status bar with line and column information."""
        cursor = self.textEdit.textCursor()
        self.line = cursor.blockNumber() + 1
        self.column = cursor.columnNumber() + 1
        self.char_count = len(self.textEdit.toPlainText())

        asterisk = ""
        if not after_save:
            asterisk = "| Changes made" if self.unsaved_changes else ""

        self.statusBar.showMessage(f"Line: {self.line} | Column: {self.column} | Characters: {self.char_count} | Encoding: {self.encoding} {asterisk}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    scratchpad = Scratchpad()
    scratchpad.show()
    sys.exit(app.exec_())

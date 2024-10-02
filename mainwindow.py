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

import importfromweb
import findreplace
import filehandler

FileHandler = filehandler.FileHandler

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
            dialog = importfromweb.UnsavedWorkDialog(self)
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
        saveAsAction.setShortcut('Ctrl+Shift+S')
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
        if sys.platform != 'darwin':
            redoAction.setShortcuts(['Ctrl+Y', 'Ctrl+Shift+Z'])
        else:
            redoAction.setShortcuts(['Ctrl+Shift+Z', 'Ctrl+Y'])
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
        findReplaceAction.setShortcut('Ctrl+F')
        findReplaceAction.triggered.connect(self.openFindReplaceDialog)
        menu.addAction(findReplaceAction)
        self.actions['findreplace'] = findReplaceAction

    def setMenuIcons(self):
        """Set icons for menu actions if available in the icons folder."""
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

        print("Current OS: " + sys.platform)

        # If the os is Windows, use icons. If it isn't, dont add icons.
        if(sys.platform != 'darwin'):
            for action_name, icon_filename in icon_files.items():
                icon_path = os.path.join(icons_folder, icon_filename)
                if os.path.isfile(icon_path):
                    self.actions[action_name].setIcon(QIcon(icon_path))

    def openFindReplaceDialog(self):
        """Open the find and replace dialog."""
        dialog = findreplace.FindReplaceDialog(self.textEdit)
        dialog.exec_()

    def importFromWeb(self):
        """Open the dialog to import content from the web."""
        dialog = importfromweb.ImportFromWebDialog(self.textEdit)
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
            asterisk = "Changes made" if self.unsaved_changes else ""

        self.statusBar.showMessage(f"Line: {self.line} | Column: {self.column} | Characters: {self.char_count} | Encoding: {self.encoding} | {asterisk}")
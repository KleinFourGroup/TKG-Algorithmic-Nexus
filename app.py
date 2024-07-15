from PySide6.QtWidgets import QWidget, QFrame, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, QPushButton, QFileDialog, QSizePolicy
from records import Database, emptyDB
from utils import newHLine

import os

def createTab():
    tab = QWidget()
    label = QLabel("TODO")
    layout = QVBoxLayout(tab)
    layout.addWidget(label)
    tab.setLayout(layout)
    return tab

class MainWindow(QWidget):
    def __init__(self, db: Database = None):
        super().__init__()
        self.setWindowTitle("Algorithmic Nexus for Information and Knowledge Analysis")
        if db == None:
            self.db = emptyDB()
        else:
            self.db = db
        
        from file_manager import FileManager
        self.fileManager = FileManager(self)

        self.resize(1280, 720)

        # Create a QTabWidget
        self.tab_widget = QTabWidget()

        # Add tabs to the QTabWidget
        from parts_tab import PartsTab
        self.partsTab = PartsTab(self)
        self.tab_widget.addTab(self.partsTab, "Parts")
        from mixtures_tab import MixturesTab
        self.mixturesTab = MixturesTab(self)
        self.tab_widget.addTab(self.mixturesTab, "Mixtures")
        from materials_tab import MaterialsTab
        self.materialsTab = MaterialsTab(self)
        self.tab_widget.addTab(self.materialsTab, "Materials")
        from packaging_tab import PackagingTab
        self.packagingTab = PackagingTab(self)
        self.tab_widget.addTab(self.packagingTab, "Packaging")
        from globals_tab import GlobalsTab
        self.globalsTab = GlobalsTab(self)
        self.tab_widget.addTab(self.globalsTab, "Globals")

        self.openButton = QPushButton("Open")
        self.openButton.clicked.connect(self.open)
        self.saveButton = QPushButton("Save")
        self.saveButton.setEnabled(not self.fileManager.filePath == None)
        self.saveButton.clicked.connect(self.save)
        self.saveAsButton = QPushButton("Save As")
        self.saveAsButton.clicked.connect(self.saveAs)
        
        hlayout = QHBoxLayout()
        hlayout.addWidget(self.openButton)
        hlayout.addWidget(self.saveButton)
        hlayout.addWidget(self.saveAsButton)

        hline = newHLine(1)

        self.dbFileLabel = QLabel()
        self.setFileLabel()

        # Create a layout for the main window
        layout = QVBoxLayout(self)
        layout.addWidget(self.tab_widget)
        layout.addWidget(hline)
        layout.addLayout(hlayout)
        layout.addWidget(self.dbFileLabel)

        # Set the layout for the main window
        self.setLayout(layout)
    
    def setFileLabel(self):
        self.dbFileLabel.setText(f"File: {self.fileManager.filePath}")

    def open(self):
        self.openButton.setEnabled(False)
        self.saveButton.setEnabled(False)
        self.saveAsButton.setEnabled(False)
        dbFile  = QFileDialog.getOpenFileName(self, "Open Database", os.path.expanduser("~"), "Database (*.db)")
        if not dbFile[0] == "":
            if self.fileManager.setFile(dbFile[0]):
                self.fileManager.loadFile()
        self.setFileLabel()
        self.openButton.setEnabled(True)
        self.saveButton.setEnabled(not self.fileManager.filePath == None)
        self.saveAsButton.setEnabled(True)
        self.materialsTab.refreshTable()
        self.mixturesTab.refreshTable()
        self.packagingTab.refreshTable()
        self.partsTab.refreshTable()
        self.globalsTab.refreshTab()
    
    def save(self):
        assert(not self.fileManager.filePath == None)
        self.fileManager.saveFile()

    def saveAs(self):
        self.openButton.setEnabled(False)
        self.saveButton.setEnabled(False)
        self.saveAsButton.setEnabled(False)
        dbFile  = QFileDialog.getSaveFileName(self, "Save Database As", os.path.expanduser("~"), "Database (*.db)")
        if not dbFile[0] == "":
            if self.fileManager.setFile(dbFile[0]):
                self.fileManager.saveFile()
        self.setFileLabel()
        self.openButton.setEnabled(True)
        self.saveButton.setEnabled(not self.fileManager.filePath == None)
        self.saveAsButton.setEnabled(True)

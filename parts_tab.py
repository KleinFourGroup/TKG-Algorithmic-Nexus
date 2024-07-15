from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QCheckBox, QMessageBox, QFileDialog
from PySide6.QtCore import Qt
from table import DBTable
from app import MainWindow
from records import Part
from error import ErrorWindow, errorMessage
from utils import getComboBox, widgetFromList, checkInput, startfile

from report import PDFReport
import os

class PartsTab(QWidget):
    def __init__(self, mainApp: MainWindow) -> None:
        super().__init__()
        self.mainApp = mainApp
        self.windows = []
        # self.error = None
        self.genTableData()
        self.table = DBTable(self.parts, self.headers)
        self.table.parentTab = self

        self.selection = []
        self.selectLabel = QLabel("Selection: N/A")

        details = QPushButton("Details")
        details.clicked.connect(self.openDetails)
        edit = QPushButton("Edit")
        edit.clicked.connect(self.openEdits)
        new = QPushButton("New")
        new.clicked.connect(self.openNew)
        delete = QPushButton("Delete")
        delete.clicked.connect(self.deleteSelection)
        report = QPushButton("Report")
        report.clicked.connect(self.reportSales)

        barLayout = QHBoxLayout()
        barLayout.addWidget(self.selectLabel)
        barLayout.addWidget(details)
        barLayout.addWidget(edit)
        barLayout.addWidget(new)
        barLayout.addWidget(delete)
        barLayout.addWidget(report)

        layout = QVBoxLayout()
        layout.addWidget(self.table)
        layout.addLayout(barLayout)
        self.setLayout(layout)
    
    def genTableData(self):
        db = self.mainApp.db
        def getKey(entry):
            item = db.parts[entry]
            isQuote = 0 if isinstance(item.sales, int) else 1
            return (isQuote, entry)
        self.headers = ["Part", "Weight", "Mix", "Materials", "Labor", "Scrap", "Packaging", "Var. Cost", "Man. Cost", "Total Cost", "Price", "Sales"]
        self.parts = [[
            entry,
            "{} lbs".format(db.parts[entry].weight),
            db.parts[entry].mix,
            "${:.4f}".format(db.parts[entry].getMatlCost()),
            "${:.4f}".format(db.parts[entry].getLaborCost()),
            "{:.2f}%".format(100 * db.parts[entry].getScrap()),
            "${:.4f}".format(db.parts[entry].getPackagingCost()),
            "${:.4f}".format(db.parts[entry].getVariableCost()),
            "${:.4f}".format(db.parts[entry].getManufacturingCost()),
            "${:.4f}".format(db.parts[entry].getTotalCost()),
            "${:.4f}".format(db.parts[entry].price),
            str(db.parts[entry].sales)
        ] for entry in db.parts]
        self.parts.sort(key=lambda row: getKey(row[0]))
    
    def setSelection(self, selection):
        self.selection = selection
        self.selectLabel.setText(f"Selection: {",".join(selection)}")
    
    def openDetails(self):
        if len(self.selection) == 0:
            # self.error = ErrorWindow(["No parts selected."])
            errorMessage(self.mainApp, ["No parts selected."])
        for part in self.selection:
            print(part)
            self.windows.append(PartsDetailsWindow(part, self.mainApp))
    
    def openEdits(self):
        for part in self.selection:
            print(part)
            self.windows.append(PartsEditWindow(part, self.mainApp))

    def deleteSelection(self):
        if len(self.selection) == 0:
            errorMessage(self.mainApp, ["No parts selected."])
        for part in self.selection:
            confirm = QMessageBox.question(self, f"Delete {part}?", f"Are you sure you want to delete {part}?")

            if confirm == QMessageBox.StandardButton.Yes:
                self.mainApp.db.delPart(part)
                self.refreshTable()
                QMessageBox.information(self.mainApp, "Success!", f"Deleted part {part}")

    def reportSales(self):
        reportFile  = QFileDialog.getSaveFileName(self, f"Save Sales Report As", os.path.expanduser("~"), "Portable Document Format (*.pdf)")
        if not reportFile[0] == "":
            pdf = PDFReport(self.mainApp.db, reportFile[0])
            pdf.salesReport()
            startfile(reportFile[0])
    
    def openNew(self):
        self.windows.append(PartsEditWindow(None, self.mainApp))
    
    def refreshTable(self):
        self.genTableData()
        self.table.setData(self.parts)
        selection = [part for part in self.selection if part in self.mainApp.db.parts]
        self.setSelection(selection)

class PartsDetailsWindow(QWidget):
    def __init__(self, entry, mainApp: MainWindow):
        super().__init__()
        self.mainApp = mainApp
        self.setWindowTitle(f"Details: {entry}")

        part = self.mainApp.db.parts[entry]        
        labels = [
            [QLabel(f"Part: {entry}")],
            [QLabel(f"Weight: {part.weight} lbs"), QLabel(f"Mix: {part.mix}")],
            [QLabel(f"Pressing: {part.pressing} pieces/hour"), QLabel(f"Turning: {part.turning} pieces/hour")],
            [QLabel(f"Box: {part.box}"), QLabel(f"Pieces / box: {part.piecesPerBox}"), QLabel(f"Pallet: {part.pallet}"), QLabel(f"Boxes / pallet: {part.boxesPerPallet}"), QLabel(f"Pads: {", ".join(part.pad)}"), QLabel(f"Pads / box: {", ".join(map(str, part.padsPerBox))}"), QLabel(f"Misc.: {", ".join(part.misc)}")],
            [QLabel(f"Green scrap: {part.db.globals.greenScrap}%"), QLabel(f"Fire scrap: {100 * part.fireScrap}%")],
            [QLabel(f"Price: ${part.price}"), QLabel(f"Annual sales: ${part.sales}")]
        ]

        widgetFromList(self, labels)
        self.show()

class PartsEditWindow(QWidget):
    def __init__(self, entry, mainApp: MainWindow):
        super().__init__()
        self.mainApp = mainApp
        self.setWindowTitle(f"Edit: {entry if not entry == None else "New Part"}")

        part = self.mainApp.db.parts[entry] if not entry == None else None
        self.part = part

        self.error = None

        padsWidget = QWidget()
        self.padsLayout = []

        pads = ["None"]
        pads.extend([key for key in self.mainApp.db.packaging if self.mainApp.db.packaging[key].kind == "pad"])

        for i in range(5):
            if (not part == None) and i < len(part.pad):
                self.padsLayout.append([
                    QLabel("Pad:"),
                    getComboBox(pads, part.pad[i]),
                    QLabel("Pads / box:"),
                    QLineEdit(f"{part.padsPerBox[i]}")
                ])
            else:
                self.padsLayout.append([
                    QLabel("Pad:"),
                    getComboBox(pads, None),
                    QLabel("Pads / box:"),
                    QLineEdit()
                ])
        
        widgetFromList(padsWidget, self.padsLayout)

        miscWidget = QWidget()
        self.miscLayout = []
        miscs = ["None"]
        miscs.extend([key for key in self.mainApp.db.packaging if self.mainApp.db.packaging[key].kind == "misc"])

        for i in range(5):
            if (not part == None) and i < len(part.misc):
                self.miscLayout.append([QLabel("Misc.:"), getComboBox(miscs, part.misc[i])])
            else:
                self.miscLayout.append([QLabel("Misc.:"), getComboBox(miscs, None)])
        
        widgetFromList(miscWidget, self.miscLayout)

        self.mainLayout = [
            [QLabel("Part:"), QLineEdit(f"{entry if not entry == None else "New Part"}")],
            [
                QLabel("Weight:"), QLineEdit(f"{part.weight if not part == None else ""}"), QLabel("lbs"),
                QLabel("Mix:"), getComboBox(list(self.mainApp.db.mixtures.keys()), part.mix if not part == None else None)
            ],
            [
                QLabel("Pressing:"), QLineEdit(f"{part.pressing if not part == None else ""}"), QLabel("pieces/hour"),
                QLabel("Turning:"), QLineEdit(f"{part.turning if not part == None else ""}"), QLabel("pieces/hour")
            ],
            [
                QLabel("Box:"), getComboBox([key for key in self.mainApp.db.packaging if self.mainApp.db.packaging[key].kind == "box"], part.box if not part == None else None),
                QLabel("Pieces / box:"), QLineEdit(f"{part.piecesPerBox if not part == None else ""}"),
                QLabel("Pallet:"), getComboBox([key for key in self.mainApp.db.packaging if self.mainApp.db.packaging[key].kind == "pallet"], part.pallet if not part == None else None),
                QLabel("Boxes / pallet:"), QLineEdit(f"{part.boxesPerPallet if not part == None else ""}"),
                padsWidget,
                miscWidget
            ],
            [
                QLabel("Fire scrap:"), QLineEdit(f"{100 * part.fireScrap if not part == None else ""}"), QLabel("%")
            ],
            [
                QLabel("Price:"), QLineEdit(f"{part.price if not part == None else ""}"),
                QLabel("Annual sales:"), QLineEdit(f"{part.sales if not part == None else ""}"), QCheckBox("Quote")
            ],
            [
                QPushButton("Update"), QPushButton("Create")
            ]
        ]

        widgetFromList(self, self.mainLayout)
        if not part == None:
            self.mainLayout[6][0].clicked.connect(self.updatePart)
        else:
            self.mainLayout[6][0].setEnabled(False)
            self.mainLayout[5][3].setEnabled(False)
            self.mainLayout[5][4].setCheckState(Qt.CheckState.Checked)
        self.mainLayout[6][1].clicked.connect(self.newPart)
        self.mainLayout[5][4].stateChanged.connect(self.quote)
        self.show()
    
    def quote(self, state):
        if state == Qt.CheckState.Checked.value:
            print("Disable")
            self.mainLayout[5][3].setEnabled(False)
        else:
            print("Enable")
            self.mainLayout[5][3].setEnabled(True)

    def readData(self, isNew):
        res = False
        errors = []
        name = self.mainLayout[0][1].text()
        if name in self.mainApp.db.parts:
            if isNew or (not name == self.part.name):
                errors.append(f"Part name '{name}' already in use")
        weight = checkInput(self.mainLayout[1][1].text(), float, "pos", errors, "weight")
        mix = self.mainLayout[1][4].currentText()
        pressing = checkInput(self.mainLayout[2][1].text(), float, "pos", errors, "pressing")
        turning = checkInput(self.mainLayout[2][4].text(), float, "pos", errors, "turning")
        loading = None
        unloading = None
        inspection = None
        box = self.mainLayout[3][1].currentText()
        piecesPerBox = checkInput(self.mainLayout[3][3].text(), int, "pos", errors, "pieces / box")
        pallet = self.mainLayout[3][5].currentText()
        boxesPerPallet = checkInput(self.mainLayout[3][7].text(), int, "pos", errors, "boxes / pallet")
        greenScrap = None
        fireScrap = checkInput(self.mainLayout[4][1].text(), float, "nonneg", errors, "fire scrap") / 100
        price = checkInput(self.mainLayout[5][1].text(), float, "nonneg", errors, "price")
        sales = "Quote" if self.mainLayout[5][4].isChecked() else checkInput(self.mainLayout[5][3].text(), int, "nonneg", errors, "annual sales")
        
        pad = []
        padsPerBox = []
        for row in self.padsLayout:
            if not row[1].currentText() == "None":
                pad.append(row[1].currentText())
                padsPerBox.append(checkInput(row[3].text(), int, "pos", errors, "pads / box"))
        misc = []
        for row in self.miscLayout:
            if not row[1].currentText() == "None":
                misc.append(row[1].currentText())

        if len(errors) == 0:
            isNone = self.part == None
            if isNew:
                self.part = Part(name)
                self.mainApp.db.addPart(self.part)
            else:
                assert(not isNone)
                self.mainApp.db.updatePart(self.part.name, name)
            self.part.setProduction(weight, mix, pressing, turning, loading, unloading, inspection, greenScrap, fireScrap, price)
            self.part.setPackaging(box, piecesPerBox, pallet, boxesPerPallet, pad, padsPerBox, misc)
            self.part.sales = sales
            if isNone:
                self.part = None
            self.mainApp.partsTab.refreshTable()
            res = True
        else:
            # self.error = ErrorWindow(errors)
            errorMessage(self, errors)
        self.setWindowTitle(f"Edit: {self.part.name if not self.part == None else "New Part"}")
        return res
    
    def updatePart(self):
        success = self.readData(False)
        if success:
            QMessageBox.information(self, "Success", "Update successful!")
            self.close()
    
    def newPart(self):
        success = self.readData(True)
        if success:
            QMessageBox.information(self, "Success", "Creation successful!")
            self.close()
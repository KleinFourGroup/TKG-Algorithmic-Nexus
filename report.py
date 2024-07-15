from math import floor

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

from records import Database

class PDFReport:
    def __init__(self, db: Database, path: str, margin: float = inch) -> None:
        self.db = db
        self.pdf = canvas.Canvas(path, pagesize=letter)
        self.lineSpace = 1.3
        self.calculateMargins(margin)
        self.pageNum = 1
        self.setFont("Times-Roman", 12)

    def calculateMargins(self, margin: float):
        self.margin = margin
        self.top = letter[1] - self.margin
        self.bottom = self.margin
        self.left = self.margin
        self.right = letter[0] - self.margin

    def setupPage(self):
        self.lastLine = self.top
    
    def nextPage(self):
        self.pdf.showPage()
        self.pageNum += 1
        self.setupPage()
    
    def setFont(self, font: str, size: int):
        self.pdf.setFont(font, size)
        self.font = font
        self.fontSize = size
    
    def skipLines(self, numLines):
        self.lastLine -= self.fontSize * self.lineSpace * numLines
    
    def drawText(self, text: str):
        self.pdf.drawString(self.left, self.lastLine - self.fontSize, text)
        self.skipLines(1)
    
    def drawTitle(self, text: str):
        oldFont = (self.font, self.fontSize)
        self.setFont("Times-Bold", 24)
        self.drawText(text)
        self.setFont(*oldFont)
    
    def drawSection(self, text: str):
        oldFont = (self.font, self.fontSize)
        self.setFont("Times-Bold", 18)
        self.drawText(text)
        self.setFont(*oldFont)
    
    def drawTable(self, data: list[list[str]], headers: list[str] = None, widths: list[float] = None):
        hasHeader = not headers == None
        columns = len(widths) if not widths == None else len(headers) if hasHeader else len(data[0]) if len(data) > 0 else 1

        if widths == None:
            widths = [(self.right - self.left) / columns for i in range(columns)]

        totalWidth = 0
        for width in widths:
            totalWidth += width

        startX = self.left + ((self.right - self.left - totalWidth) / 2.0)
        xVals = [startX]
        for width in widths:
            xVals.append(xVals[-1] + width)
        
        padding = self.fontSize / 3
        rowHeight = self.fontSize + 1.5 * padding
        # includes header
        maxRows = floor((self.lastLine - self.bottom) / rowHeight)
        rows = min((1 if hasHeader else 0) + len(data), maxRows)
        if rows == 0:
            return 0
        
        yVals = [self.lastLine - i * rowHeight for i in range(rows + 1)]

        self.pdf.grid(xVals, yVals)

        if hasHeader:
            oldFont = (self.font, self.fontSize)
            self.setFont("Times-Bold", self.fontSize)
            drawY = yVals[1]
            for i in range(columns):
                self.pdf.drawString(xVals[i] + padding, drawY + padding, headers[i])
            self.setFont(*oldFont)
        
        drawn = 0
        for row in range(2 if hasHeader else 1, len(yVals)):
            drawY = yVals[row]
            dataRow = data[row - (2 if hasHeader else 1)]
            for i in range(columns):
                self.pdf.drawString(xVals[i] + padding, drawY + padding, dataRow[i])
            drawn += 1
        self.lastLine = yVals[-1] - self.fontSize * self.lineSpace
        return drawn
    
    def globalsReport(self):
        globalKeys = self.db.globals.getGlobals()
        globalStrings = self.db.globals.getStrings()
        self.setupPage()
        self.drawTitle("TKG Production Report")
        self.skipLines(2)
        self.drawSection("Global Values")
        for glob in globalKeys:
            self.drawText(f"{globalStrings[glob][0]}: {getattr(self.db.globals, glob)} ({globalStrings[glob][1]})")
        self.nextPage()
        self.pdf.save()

    def mixReport(self, mixName):
        if mixName in self.db.mixtures:
            mix = self.db.mixtures[mixName]
            self.setupPage()
            self.drawTitle("TKG Production Report")
            self.skipLines(2)

            self.drawSection(f"{mixName} Mixture Composition")
            headers = ["Material", "Weight"]
            data = [[f"{mix.materials[i]}", f"{mix.weights[i]}"] for i in range(len(mix.materials))]
            self.drawTable(data, headers)

            self.drawTable([], ["Total", f"{mix.getBatchWeight()}"])

            self.drawSection(f"{mixName} Chemical Analysis")
            data = [
                ("SiO2", f"{mix.getProp("SiO2"):.4f}%"),
                ("Al2O3", f"{mix.getProp("Al2O3"):.4f}%"),
                ("Fe2O3", f"{mix.getProp("Fe2O3"):.4f}%"),
                ("TiO2", f"{mix.getProp("TiO2"):.4f}%"),
                ("Li2O", f"{mix.getProp("Li2O"):.4f}%"),
                ("P2O5", f"{mix.getProp("P2O5"):.4f}%"),
                ("Na2O", f"{mix.getProp("Na2O"):.4f}%"),
                ("CaO", f"{mix.getProp("CaO"):.4f}%"),
                ("K2O", f"{mix.getProp("K2O"):.4f}%"),
                ("MgO", f"{mix.getProp("MgO"):.4f}%")
            ]
            self.drawTable(data)

            self.drawSection(f"{mixName} Sizing Analysis")
            headers = ["+50", "-50+100", "-100+200", "-200+325", "-325"]
            data = [[
                f"{mix.getProp("Plus50", False):.1f}%",
                f"{mix.getProp("Sub50Plus100", False):.1f}%",
                f"{mix.getProp("Sub100Plus200", False):.1f}%",
                f"{mix.getProp("Sub200Plus325", False):.1f}%",
                f"{mix.getProp("Sub325", False):.1f}%"
            ]]

            self.drawTable(data, headers)

            self.nextPage()
            self.pdf.save()

    def salesReport(self):
        parts = [self.db.parts[name] for name in self.db.parts.keys() if isinstance(self.db.parts[name].sales, int) and self.db.parts[name].sales > 0]
        data = []
        total = 0
        for part in parts:
            data.append([f"{part.name}", f"${part.getManufacturingCost():.4f}", f"{part.sales}", f"${part.sales * part.getManufacturingCost():.2f}"])
            total += part.sales * part.getManufacturingCost()
        while len(data) > 0:
            self.setupPage()
            self.drawTitle("TKG Production Report")
            self.skipLines(2)

            self.drawSection("Cost Analysis Report" if len(data) == len(parts) else "Sales (cont.)")
            headers = ["Part", "Manufacturing Cost", "Sales", "COGS"]
            drawn = self.drawTable(data, headers)

            if drawn == len(data):
                self.drawTable([], ["Total", "---", "---", f"${total:.2f}"])
            
            data = data[drawn:]
            self.nextPage()
        self.pdf.save()
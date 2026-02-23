from PyQt5.QtWidgets import QMainWindow,QApplication,QDialog,QWidget,QPushButton,QLineEdit,QLabel,QComboBox,QTableWidget,QMessageBox,QAction, QHeaderView, QDesktopWidget
from PyQt5 import QtWidgets, uic, QtCore, QtPrintSupport,QtGui
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtGui import QPainter, QFont
import sys
import mysql.connector

# helper for db

def get_connection():
    return mysql.connector.connect(user='andriefendy', password='Andri2608.', host='127.0.0.1', database='warungme')

class lognin(QDialog):
    def __init__(self):
        super().__init__()
        # note: original UI file uses capital 'L'
        uic.loadUi("Login.ui", self)
        self.center()
        self.masuk.clicked.connect(self.loginfungsion)

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    
    def loginfungsion(self):
        username = self.emailfield.text()
        password = self.passwordfield.text()
        conn = get_connection()
        curr = conn.cursor()
        curr.execute("SELECT * FROM auth WHERE username=%s AND pass=%s", (username, password))
        user = curr.fetchone()
        curr.close()
        conn.close()
        if user is not None:
            self.masukkasir()
        else:
            self.error.setText("masukkan akun yang benar")
    
    def masukkasir(self):
        self.openkasir = kasir()
        self.openkasir.show()
        self.close()
        
                        
class kasir(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("CheckOut.ui", self)
        self.center()
        self.table_1.clicked.connect(self.getitem)
        self.simpan.clicked.connect(self.simpandat)
        self.bayar.clicked.connect(self.bayarr)
        self.keluar.clicked.connect(self.keluars)
        self.hapus.clicked.connect(self.hapuss)
        self.batal.clicked.connect(self.batals)
        self.activeText(False)
        self.tableWidgt()
        self.loaddata()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def tableWidgt(self):
        header = self.table_1.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.table_1.setColumnWidth(0,100)
        self.table_1.setColumnWidth(1,250)
        self.table_1.setColumnWidth(2,180)

        header2 = self.table_2.horizontalHeader()
        header2.setSectionResizeMode(QHeaderView.Stretch)
        self.table_2.setColumnWidth(0,100)
        self.table_2.setColumnWidth(1,200)
        self.table_2.setColumnWidth(2,150)
        self.table_2.setColumnWidth(3,50)


    def activeText(self,bool):
        self.kategori.setEnabled(bool)
        self.pilihanmenu.setEnabled(bool)
        self.harga.setEnabled(bool)
        self.totalbayar.setEnabled(bool)
        self.kembalian.setEnabled(bool)
        self.jumlah2.setEnabled(bool)
    
    def clearform(self):
        self.kategori.setText('')
        self.pilihanmenu.setText('')
        self.harga.setText('')
        self.jumlah.setText('0')
    
    def clearform2(self):
        self.totalbayar.setText('')
        self.uangpembayaran.setText('')
        self.table_2.clearContents()
        self.table_2.setRowCount(0)
        self.kembalian.setText('')
        self.pemesan.setText('')
        self.jumlah2.setText('')
        
    def clear(self):
        self.clearform2()

    def bayarr(self):
        conn = get_connection()
        curr = conn.cursor()
        namapembeli = self.pemesan.text()
        jumlah = str(self.jumlah2.text())
        totalbayar = str(self.totalbayar.text())
        total = float(self.totalbayar.text())
        payment = float(self.uangpembayaran.text())
        if payment >= total:
            change = payment - total
            self.kembalian.setText(str(change))
            curr.execute("INSERT INTO laporan (nama, jumlah, total) VALUES (%s, %s, %s)",
                         (namapembeli, jumlah, totalbayar))
            conn.commit()
            curr.close()
            conn.close()
            QMessageBox.information(self, "info", "Pembayaran Berhasil")
            self.cetak_struk()
        else:
            self.kembalian.setText("Uang Kurang")
            curr.close()
            conn.close()
        
    def simpandat(self):
        row = self.table_2.rowCount()
        self.table_2.insertRow(row)
        kategori = self.kategori.text()
        menu = self.pilihanmenu.text()
        harga = self.harga.text()
        jumlah = self.jumlah.text()

        if jumlah:
            self.table_2.setItem(row, 0, QtWidgets.QTableWidgetItem(kategori))
            self.table_2.setItem(row, 1, QtWidgets.QTableWidgetItem(menu))
            self.table_2.setItem(row, 2, QtWidgets.QTableWidgetItem(str(harga)))
            self.table_2.setItem(row, 3, QtWidgets.QTableWidgetItem(str(jumlah)))

            value = float(jumlah)
            hitung = value * float(harga)
            self.table_2.setItem(row, 4, QtWidgets.QTableWidgetItem(str(hitung)))

            self.jum()
            self.tot()
            self.clearform()
                    
                    
    def cetak_struk(self):
        printer = QPrinter(QPrinter.HighResolution)
        printer.setPageSize(QtPrintSupport.QPrinter.A6)
        dialog = QPrintDialog(printer, self)
        if dialog.exec_() == QPrintDialog.Accepted:
            painter = QPainter(printer)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Membuat konten struk
            margin = 70
            x = margin
            y = margin
            line_height = 150
                    
            painter.setFont(QtGui.QFont("Arial", 12))
            judul_text = "Restorant Cepat Saji"
            judul_text_width = painter.fontMetrics().boundingRect(judul_text).width()
            total_x = (printer.pageRect().width() - judul_text_width) / 2
            painter.drawText(total_x, y, judul_text)
            y += line_height

            painter.setFont(QtGui.QFont("Arial", 12))
            Univ = "Universitas Borneo Tarakan"
            univ_text_width = painter.fontMetrics().boundingRect(Univ).width()
            univ_x = (printer.pageRect().width() - univ_text_width) / 2
            painter.drawText(univ_x, y, Univ)
            y += line_height

            painter.setFont(QtGui.QFont("Arial", 12, QtGui.QFont.Bold))
            tek_kom_text = "Teknik Komputer"
            tek_kom_text_width = painter.fontMetrics().boundingRect(tek_kom_text).width()
            tek_kom_x = (printer.pageRect().width() - tek_kom_text_width) / 2
            painter.drawText(tek_kom_x, y, tek_kom_text)
            y += line_height

            garis =  "==========================================="
            garis_width = painter.fontMetrics().boundingRect(garis).width()
            garis_x = (printer.pageRect().width() - garis_width) / 2
            painter.drawText(garis_x, y, garis)
            y += line_height

            painter.setFont(QtGui.QFont("Arial", 12))
            painter.drawText(x, y, "Struk Belanja")
            y += line_height
            
            painter.setFont(QtGui.QFont("Arial", 10))
            painter.drawText(x, y, "Daftar Belanja:")
            y += line_height
            
            row_count = self.table_2.rowCount()
            for row in range(row_count):
                nama_barang = self.table_2.item(row, 1).text()
                harga = str(self.table_2.item(row, 2).text())
                jumlah = str(self.table_2.item(row, 3).text())
                subtotal = str(self.table_2.item(row, 4).text())
                subtotal_width = painter.fontMetrics().boundingRect(subtotal).width()
                text = f"{nama_barang}: {harga} x {jumlah}"
                subtotal_x = printer.pageRect().width() - margin - subtotal_width
                painter.drawText(subtotal_x, y, subtotal)
                painter.drawText(x, y, text)
                y += line_height
            
            painter.setFont(QtGui.QFont("Arial", 12))
            garis =  "==========================================="
            garis_width = painter.fontMetrics().boundingRect(garis).width()
            garis_x = (printer.pageRect().width() - garis_width) / 2
            painter.drawText(garis_x, y, garis)
            y += line_height
            
            painter.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
            painter.drawText(x, y, "Total:")
            
            total_text = str(self.hitung_total())
            total_text_width = painter.fontMetrics().boundingRect(total_text).width()
            total_x = printer.pageRect().width() - margin - total_text_width
            painter.drawText(total_x, y, total_text)
            y += line_height

            painter.setFont(QtGui.QFont("Arial", 12))
            garis =  "============================================="
            garis_width = painter.fontMetrics().boundingRect(garis).width()
            garis_x = (printer.pageRect().width() - garis_width) / 2
            painter.drawText(garis_x, y, garis)
            y += line_height
            
            painter.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
            painter.drawText(x, y, "Bayar:")
            

            bayar_text = str(self.uangpembayaran.text())
            bayar_text_width = painter.fontMetrics().boundingRect(bayar_text).width()
            bayar_x = printer.pageRect().width() - margin - bayar_text_width
            painter.drawText(bayar_x, y, bayar_text)
            y += line_height

            painter.setFont(QtGui.QFont("Arial", 10))
            painter.drawText(x, y, "kembalian:")
            
            if bayar_text:
                bayar = int(bayar_text)
                total = int(total_text)
                kembali_text = bayar - total
                kembali_text = str(kembali_text)
                kembali_text_width = painter.fontMetrics().boundingRect(kembali_text).width()
                kembali_x = printer.pageRect().width() - margin - kembali_text_width
                painter.drawText(kembali_x, y, kembali_text)
            else:
                # Handle case when the input is empty
                kembali_text = "Input bayar tidak valid"
                kembali_text_width = painter.fontMetrics().boundingRect(kembali_text).width()
                kembali_x = printer.pageRect().width() - margin - kembali_text_width
                painter.drawText(kembali_x, y, kembali_text)
            y += line_height
            
            painter.setFont(QtGui.QFont("Arial", 12))
            garis =  "============================================="
            garis_width = painter.fontMetrics().boundingRect(garis).width()
            garis_x = (printer.pageRect().width() - garis_width) / 2
            painter.drawText(garis_x, y, garis)
            y += line_height

            painter.setFont(QtGui.QFont("Arial", 12))
            judul_text = "Terima Kasih Telah Berbelanja"
            judul_text_width = painter.fontMetrics().boundingRect(judul_text).width()
            total_x = (printer.pageRect().width() - judul_text_width) / 2
            painter.drawText(total_x, y, judul_text)
            
            painter.end()
            self.clearform2()

    def jum(self):
        jum = 0
        rowcount = self.table_2.rowCount()
        for row in range(rowcount):
            item = self.table_2.item(row, 3)
            if item is not None:
                juml = float(item.text())
                jum += juml
                self.jumlah2.setText("{:.0f}".format(jum))

    #untuk struk        
    def hitung_total(self):
        total = 0
        row_count = self.table_2.rowCount()
        for row in range(row_count):
            harga = int(self.table_2.item(row, 2).text())
            jumlah = int(self.table_2.item(row, 3).text())
            total += harga * jumlah
        return total
    
    #untuk bayar
    def tot(self):
        tota = 0
        rowcount = self.table_2.rowCount()
        for row in range(rowcount):
            item = self.table_2.item(row, 4)
            if item is not None:
                harga = float(item.text())
                tota += harga
                self.totalbayar.setText("{:.0f}".format(tota))

    def hapuss(self):
        row = self.table_2.currentRow()
        if row != -1:
            self.table_2.removeRow(row)
            self.tot()
            self.jum()


    def getitem(self):
        row = self.table_1.currentRow()
        tipeMenu = self.table_1.item(row,0).text()
        namaMenu = self.table_1.item(row,1).text()
        hargaa = self.table_1.item(row,2).text()
        self.kategori.setText(tipeMenu)
        self.pilihanmenu.setText(namaMenu)
        self.harga.setText(hargaa)
    
    #def printstruk(self):
        #doc 
    
    def batals(self):
        self.clearform()
        self.clearform2()        
        
    def loaddata(self):
        conn = get_connection()
        curr = conn.cursor()
        curr.execute("SELECT * FROM tbbarang")
        result = curr.fetchall()
        curr.close()
        conn.close()
        self.table_1.setRowCount(len(result))
        for row, item in enumerate(result):
            self.table_1.setItem(row,0,QtWidgets.QTableWidgetItem(item[1]))
            self.table_1.setItem(row,1,QtWidgets.QTableWidgetItem(item[2]))
            self.table_1.setItem(row,2,QtWidgets.QTableWidgetItem(str(item[3])))
    
    def keluars(self):
        self.logout = lognin()
        self.logout.show()
        self.close()

        

if __name__ == "__main__":
	MainApp = QtWidgets.QApplication(sys.argv)
	widget = QWidget,QTableWidget()
	App = lognin()
	App.show()
	sys.exit(MainApp.exec_())

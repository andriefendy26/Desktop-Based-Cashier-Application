from PyQt5.QtWidgets import QDialog, QApplication, QDesktopWidget, QWidget, QMessageBox, QHeaderView
from PyQt5 import QtWidgets, uic, QtCore
import mysql.connector
import sys

# helper to obtain a database connection

_window = None

def get_connection():
    return mysql.connector.connect(
        user='root',
        password='',
        host='127.0.0.1',
        database='warungme',
        use_pure=True
    )


class login(QDialog):
    def __init__(self):
        super().__init__()
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
        conn = None
        curr = None
        try:
            conn = get_connection()
            curr = conn.cursor()
            curr.execute("SELECT * FROM auth WHERE username=%s AND pass=%s", (username, password))
            user = curr.fetchone()
        except Exception as e:
            QMessageBox.critical(self, 'Database Error', f'Could not login: {e}')
            return
        finally:
            if curr is not None:
                curr.close()
            if conn is not None:
                conn.close()

        if user:
            self.masukkasir()
            QMessageBox.information(self, 'Alert', 'login berhasil')
        else:
            self.error.setText("masukkan akun yang benar")

    # def masukkasir(self):
    #     self.openkasir = Pilihan()
    #     self.openkasir.show()
    #     self.close()

    def masukkasir(self):
        global _window
        _window = Pilihan()   # ← simpan ke global, bukan self
        _window.show()
        self.close()


class Pilihan(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("Pilihan.ui", self)
        self.center()
        self.tombol()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def tombol(self):
        self.Menu.clicked.connect(self.Dftrmenu)
        self.Lprn.clicked.connect(self.Lapar)
        self.logout.clicked.connect(self.Keluar)

    def Dftrmenu(self):
        self.openkasir = DftrMenu()
        self.openkasir.show()
        self.close()

    def Lapar(self):
        self.openkasir = Laporan()
        self.openkasir.show()
        self.close()

    def Keluar(self):
        self.openkasir = login()
        self.openkasir.show()
        self.close()


class DftrMenu(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("DaftarMenu.ui", self)
        self.center()
        self.tombol()
        self.tabelWidtg()
        self.loaddata()
        self.activeText(False)

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def tombol(self):
        self.keluar.clicked.connect(self.kembali)
        self.batal.clicked.connect(self.batals)
        self.edit.clicked.connect(self.edittext)
        self.tableWidget.clicked.connect(self.getitem)
        self.hapus.clicked.connect(self.hapusData)
        self.simpan.clicked.connect(self.simpandata)

    def tabelWidtg(self):
        header = self.tableWidget.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.tableWidget.setColumnWidth(0,100)
        self.tableWidget.setColumnWidth(1,150)
        self.tableWidget.setColumnWidth(2,180)
        self.tableWidget.setColumnWidth(3,165)

    def loaddata(self):
        conn = get_connection()
        curr = conn.cursor()
        curr.execute("SELECT * FROM tbbarang ORDER BY total DESC")
        result = curr.fetchall()
        curr.close()
        conn.close()
        self.tableWidget.setRowCount(len(result))
        for row, item in enumerate(result):
            self.tableWidget.setItem(row,0,QtWidgets.QTableWidgetItem(item[0]))
            self.tableWidget.setItem(row,1,QtWidgets.QTableWidgetItem(item[1]))
            self.tableWidget.setItem(row,2,QtWidgets.QTableWidgetItem(item[2]))
            self.tableWidget.setItem(row,3,QtWidgets.QTableWidgetItem(str(item[3])))

    def clearform(self):
        self.textIdMenu.setFocus()
        self.textIdMenu.clear()
        self.cbKategori.setCurrentText('')
        self.textMenu.clear()
        self.textHarga.clear()

    def activeText(self, enable):
        self.textIdMenu.setEnabled(enable)
        self.cbKategori.setEnabled(enable)
        self.textMenu.setEnabled(enable)
        self.textHarga.setEnabled(enable)

    def getitem(self):
        row = self.tableWidget.currentRow()
        if row < 0:
            return
        id_item = self.tableWidget.item(row,0)
        if id_item is None:
            return
        idMenu = id_item.text()
        tipeMenu = self.tableWidget.item(row,1).text()
        namaMenu = self.tableWidget.item(row,2).text()
        hargaa = self.tableWidget.item(row,3).text()
        self.textIdMenu.setText(idMenu)
        self.cbKategori.setCurrentText(tipeMenu)
        self.textMenu.setText(namaMenu)
        self.textHarga.setText(hargaa)

    def edittext(self):
        cb = self.edit.text()
        if cb == 'edit tabel':
            self.activeText(True)
            self.clearform()
            self.edit.setText('simpan')
        elif cb == 'simpan':
            idMenu = self.textIdMenu.text()
            if len(idMenu) > 5:
                QMessageBox.warning(self, "Input Error", "ID menu cannot be longer than 5 characters.")
                return
            conn = get_connection()
            curr = conn.cursor()
            tipeMenu = self.cbKategori.currentText()
            namaMenu = self.textMenu.text()
            hargaa = self.textHarga.text()
            try:
                curr.execute(
                    "UPDATE tbbarang SET kategori=%s, namaMenu=%s, harga=%s WHERE idMenu=%s",
                    (tipeMenu, namaMenu, hargaa, idMenu),
                )
                conn.commit()
            except mysql.connector.DataError as e:
                QMessageBox.critical(self, "Database Error", f"Failed to update data: {e}")
            finally:
                curr.close()
                conn.close()
            self.loaddata()
            self.activeText(False)
            self.clearform()
            self.edit.setText('edit tabel')

    def hapusData(self):
        conn = get_connection()
        curr = conn.cursor()
        idMenu = self.textIdMenu.text()
        curr.execute("DELETE FROM tbbarang WHERE idMenu=%s", (idMenu,))
        conn.commit()
        curr.close()
        conn.close()
        self.loaddata()

    def batals(self):
        cb = self.simpan.text()
        ed = self.edit.text()
        if cb == 'simpan':
            self.simpan.setText('baru')
            self.clearform()
            self.activeText(False)
        elif ed == 'simpan':
            self.edit.setText('edit tabel')
            self.clearform()
            self.activeText(False)

    def simpandata(self):
        cb = self.simpan.text()
        if cb == 'baru':
            self.activeText(True)
            self.clearform()
            self.simpan.setText('simpan')
        elif cb == 'simpan':
            # validation: IdMenu length must fit in schema (varchar(5))
            idMenu = self.textIdMenu.text()
            if len(idMenu) > 5:
                QMessageBox.warning(self, "Input Error", "ID menu cannot be longer than 5 characters.")
                return
            tipeMenu = self.cbKategori.currentText()
            namaMenu = self.textMenu.text()
            hargaa = self.textHarga.text()
            try:
                conn = get_connection()
                curr = conn.cursor()
                curr.execute("INSERT INTO tbbarang (idMenu, kategori, namaMenu, harga) VALUES (%s, %s, %s, %s)",
                             (idMenu, tipeMenu, namaMenu, hargaa))
                conn.commit()
            except mysql.connector.DataError as e:
                QMessageBox.critical(self, "Database Error", f"Failed to save data: {e}")
            finally:
                try:
                    curr.close()
                    conn.close()
                except Exception:
                    pass
            self.loaddata()
            self.activeText(False)
            self.clearform()

    def kembali(self):
        self.openkasir = Pilihan()
        self.openkasir.show()
        self.close()


class Laporan(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("Data.ui", self)
        self.center()
        self.tombol()
        self.loaddata2()
        self.tabelWidtg()
        self.tot()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def tabelWidtg(self):
        header = self.tableWidget_2.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.tableWidget_2.setColumnWidth(0,330)
        self.tableWidget_2.setColumnWidth(1,250)
        self.tableWidget_2.setColumnWidth(2,280)

    def tombol(self):
        self.keluar.clicked.connect(self.kembali)

    def loaddata2(self):
        conn = get_connection()
        curr = conn.cursor()
        curr.execute("SELECT * FROM laporan")
        result = curr.fetchall()
        curr.close()
        conn.close()
        self.tableWidget_2.setRowCount(len(result))
        for row, item in enumerate(result):
            self.tableWidget_2.setItem(row,0,QtWidgets.QTableWidgetItem(item[1]))
            self.tableWidget_2.setItem(row,1,QtWidgets.QTableWidgetItem(str(item[2])))
            self.tableWidget_2.setItem(row,2,QtWidgets.QTableWidgetItem(str(item[3])))

    def tot(self):
        tota = 0
        conn = get_connection()
        curr = conn.cursor()
        curr.execute("SELECT total FROM laporan")
        rows = curr.fetchall()
        curr.close()
        conn.close()
        for row in rows:
            tota += float(row[0])
        self.Total.setStyleSheet("font-size: 18px")
        self.Total.setText("RP.{:.0f}".format(tota))

    def kembali(self):
        self.openkasir = Pilihan()
        self.openkasir.show()
        self.close()


if __name__ == "__main__":
    MainApp = QtWidgets.QApplication(sys.argv)
    MainApp.setQuitOnLastWindowClosed(False) 
    widget = QWidget()
    App = login()
    App.show()
    sys.exit(MainApp.exec_())

from PyQt5.QtWidgets import QDialog, QApplication, QDesktopWidget, QStackedWidget, QWidget, QMessageBox, QHeaderView
from PyQt5 import QtWidgets, uic, QtCore
import mysql.connector
import sys

# database helper

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
        
		# self.setGeometry(100, 100, 450, 530)
        # self.setFixedSize(self.size())
        
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

        if user is not None:
            self.masukkasir()
            QMessageBox.information(self, 'Alert', 'login berhasil')
        else:
            self.error.setText("masukkan akun yang benar")

    def masukkasir(self):
        self.openkasir = Main_UI()
        self.openkasir.show()
        self.close()


class Main_UI(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("main.ui", self)
        self.center()
        self.isEdit = False
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.tot()
        self.mainEvent()
        self.tabelWidtg()
        self.loaddata2()
        self.loaddata()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def mainEvent(self):
        self.pushButton.clicked.connect(lambda: MainApp.exit())
        self.pushButton_2.clicked.connect(lambda: self.showFullScreen())
        self.pushButton_3.clicked.connect(lambda: self.showMinimized())
        self.frame_2.mouseMoveEvent = self.MoveWindow
        self.toolButton_2.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.Daftarmenu))
        self.toolButton_3.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.Datapendapatan))
        self.simpan.clicked.connect(self.simpandata)
        # self.edit.clicked.connect(self.editData)
        self.hapus.clicked.connect(self.hapusData)
        self.tableWidget.clicked.connect(self.getitem)
        self.edit.clicked.connect(self.edittext)
        self.batal.clicked.connect(self.batals)
        self.activeText(False)
        self.toolButton.clicked.connect(lambda: self.Side_Menu_Def_0())
        QtWidgets.QSizeGrip(self.frame_6)
        self.frame_5.mousePressEvent = self.Side_Menu_Def_1

    def tabelWidtg(self):
        #Tabel Daftar Menu
        header = self.tableWidget.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.tableWidget.setColumnWidth(0,100)
        self.tableWidget.setColumnWidth(1,150)
        self.tableWidget.setColumnWidth(2,180)
        self.tableWidget.setColumnWidth(3,165)

        #Tabel Data Pendapatan
        header2 = self.tableWidget_2.horizontalHeader()
        header2.setSectionResizeMode(QHeaderView.Stretch)
        self.tableWidget_2.setColumnWidth(0,330)
        self.tableWidget_2.setColumnWidth(1,250)
        self.tableWidget_2.setColumnWidth(2,280)

    def getitem(self):
        row = self.tableWidget.currentRow()
        if row < 0:
            return
        idMenu = self.tableWidget.item(row,0).text()
        tipeMenu = self.tableWidget.item(row,1).text()
        namaMenu = self.tableWidget.item(row,2).text()
        hargaa = self.tableWidget.item(row,3).text()
        self.textIdMenu.setText(idMenu)
        self.cbKategori.setCurrentText(tipeMenu)
        self.textMenu.setText(namaMenu)
        self.textHarga.setText(hargaa)

    def clearform(self):
        self.textIdMenu.setFocus()
        self.textIdMenu.setText('')
        self.cbKategori.setCurrentText('')
        self.textMenu.setText('')
        self.textHarga.setText('')

    def activeText(self, bool):
        self.textIdMenu.setEnabled(bool)
        self.cbKategori.setEnabled(bool)
        self.textMenu.setEnabled(bool)
        self.textHarga.setEnabled(bool)

    def hapusData(self):
        conn = get_connection()
        curr = conn.cursor()
        idMenu = self.textIdMenu.text()
        curr.execute("DELETE FROM tbbarang WHERE idMenu=%s", (idMenu,))
        conn.commit()
        curr.close()
        conn.close()
        self.loaddata()

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

    def simpandata(self):
        cb = self.simpan.text()
        if cb == 'baru':
            self.activeText(True)
            self.clearform()
            self.simpan.setText('simpan')
        elif cb == 'simpan':
            idMenu = self.textIdMenu.text()
            if len(idMenu) > 5:
                QMessageBox.warning(self, "Input Error", "ID menu cannot be longer than 5 characters.")
                return
            conn = get_connection()
            curr = conn.cursor()
            self.simpan.setText('baru')
            tipeMenu = self.cbKategori.currentText()
            namaMenu = self.textMenu.text()
            hargaa = self.textHarga.text()
            try:
                curr.execute("INSERT INTO tbbarang (idMenu, kategori, namaMenu, harga) VALUES (%s, %s, %s, %s)",
                             (idMenu, tipeMenu, namaMenu, hargaa))
                conn.commit()
            except mysql.connector.DataError as e:
                QMessageBox.critical(self, "Database Error", f"Failed to save data: {e}")
            finally:
                curr.close()
                conn.close()
            self.loaddata()
            self.activeText(False)
            self.clearform()

    # ... other methods (batals, loaddata, etc.) should be copied as-is below

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

    def Side_Menu_Def_0(self):
        if self.frame_4.width() <= 50:
            self.animation1 = QtCore.QPropertyAnimation(self.frame_4, b"maximumWidth")
            self.animation1.setDuration(500)
            self.animation1.setStartValue(35)
            self.animation1.setEndValue(110)
            self.animation1.setEasingCurve(QtCore.QEasingCurve.InOutSine)
            self.animation1.start()

            self.animation2 = QtCore.QPropertyAnimation(self.frame_4, b"minimumWidth")
            self.animation2.setDuration(500)
            self.animation2.setStartValue(35)
            self.animation2.setEndValue(110)
            self.animation2.setEasingCurve(QtCore.QEasingCurve.InOutSine)
            self.animation2.start()

        else:
            self.animation1 = QtCore.QPropertyAnimation(self.frame_4, b"maximumWidth")
            self.animation1.setDuration(500)
            self.animation1.setStartValue(110)
            self.animation1.setEndValue(35)
            self.animation1.setEasingCurve(QtCore.QEasingCurve.InOutSine)
            self.animation1.start()

            self.animation2 = QtCore.QPropertyAnimation(self.frame_4, b"minimumWidth")
            self.animation2.setDuration(500)
            self.animation2.setStartValue(110)
            self.animation2.setEndValue(35)
            self.animation2.setEasingCurve(QtCore.QEasingCurve.InOutSine)
            self.animation2.start()

    def Side_Menu_Def_1(self, Event):
        if Event.button() == QtCore.Qt.LeftButton:
            if self.frame_4.width() >= 50:
                self.animation1 = QtCore.QPropertyAnimation(self.frame_4, b"maximumWidth")
                self.animation1.setDuration(500)
                self.animation1.setStartValue(110)
                self.animation1.setEndValue(35)
                self.animation1.setEasingCurve(QtCore.QEasingCurve.InOutSine)
                self.animation1.start()

                self.animation2 = QtCore.QPropertyAnimation(self.frame_4, b"minimumWidth")
                self.animation2.setDuration(500)
                self.animation2.setStartValue(110)
                self.animation2.setEndValue(35)
                self.animation2.setEasingCurve(QtCore.QEasingCurve.InOutSine)
                self.animation2.start()
            else:
                pass

    def MoveWindow(self, event):
        if self.isMaximized() == False:
            self.move(self.pos() + event.globalPos() - self.clickPosition)
            self.clickPosition = event.globalPos()
            event.accept()
            pass

    def mousePressEvent(self, event):
        self.clickPosition = event.globalPos()
        pass

if __name__ == "__main__":
    MainApp = QtWidgets.QApplication(sys.argv)
    MainApp.setQuitOnLastWindowClosed(False) 
    widget = QWidget()
    App = login()
    App.show()
    sys.exit(MainApp.exec_())

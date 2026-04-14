from PyQt5.QtWidgets import QDialog, QApplication, QDesktopWidget, QWidget, QMessageBox, QHeaderView
from PyQt5 import QtWidgets, uic, QtCore
import mysql.connector
import sys

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
            QMessageBox.information(self, 'Alert', 'Login berhasil')
        else:
            self.error.setText("Masukkan akun yang benar")

    def masukkasir(self):
        global _window
        _window = Pilihan()
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
        # FIX: set state awal tombol dengan benar
        self.simpan.setText('baru')
        self.edit.setText('edit tabel')
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

    def loaddata(self):
        conn = None
        curr = None
        try:
            conn = get_connection()
            curr = conn.cursor()
            # FIX: ORDER BY total diganti harga karena kolom 'total' tidak ada di tbbarang
            curr.execute("SELECT idMenu, kategori, namaMenu, harga FROM tbbarang ORDER BY harga DESC")
            result = curr.fetchall()
        except Exception as e:
            QMessageBox.critical(self, 'Database Error', f'Gagal memuat data: {e}')
            return
        finally:
            if curr:
                curr.close()
            if conn:
                conn.close()

        self.tableWidget.setRowCount(len(result))
        for row, item in enumerate(result):
            for col in range(4):
                self.tableWidget.setItem(row, col, QtWidgets.QTableWidgetItem(str(item[col])))

    def clearform(self):
        self.textIdMenu.setFocus()
        self.textIdMenu.clear()
        self.cbKategori.setCurrentIndex(0)
        self.textMenu.clear()
        self.textHarga.clear()

    def activeText(self, enable):
        self.textIdMenu.setEnabled(enable)
        self.cbKategori.setEnabled(enable)
        self.textMenu.setEnabled(enable)
        self.textHarga.setEnabled(enable)

    def _validate_form(self):
        """Validasi input form sebelum INSERT atau UPDATE."""
        idMenu = self.textIdMenu.text().strip()
        namaMenu = self.textMenu.text().strip()
        hargaa = self.textHarga.text().strip()

        if not idMenu:
            QMessageBox.warning(self, "Input Error", "ID Menu tidak boleh kosong.")
            return False
        if len(idMenu) > 5:
            QMessageBox.warning(self, "Input Error", "ID Menu maksimal 5 karakter.")
            return False
        if not namaMenu:
            QMessageBox.warning(self, "Input Error", "Nama menu tidak boleh kosong.")
            return False
        if not hargaa.isdigit():
            QMessageBox.warning(self, "Input Error", "Harga harus berupa angka.")
            return False
        return True

    def getitem(self):
        row = self.tableWidget.currentRow()
        if row < 0:
            return
        # FIX: cek semua kolom, bukan hanya kolom pertama
        items = [self.tableWidget.item(row, col) for col in range(4)]
        if any(i is None for i in items):
            return
        self.textIdMenu.setText(items[0].text())
        self.cbKategori.setCurrentText(items[1].text())
        self.textMenu.setText(items[2].text())
        self.textHarga.setText(items[3].text())

    def edittext(self):
        cb = self.edit.text()
        if cb == 'edit tabel':
            # FIX: pastikan ada baris yang dipilih sebelum masuk mode edit
            row = self.tableWidget.currentRow()
            if row < 0:
                QMessageBox.warning(self, "Pilih Data", "Pilih baris yang ingin diedit terlebih dahulu.")
                return
            self.activeText(True)
            self.edit.setText('simpan')

        elif cb == 'simpan':
            if not self._validate_form():
                return

            idMenu   = self.textIdMenu.text().strip()
            tipeMenu = self.cbKategori.currentText()
            namaMenu = self.textMenu.text().strip()
            hargaa   = self.textHarga.text().strip()

            conn = None
            curr = None
            try:
                conn = get_connection()
                curr = conn.cursor()
                curr.execute(
                    "UPDATE tbbarang SET kategori=%s, namaMenu=%s, harga=%s WHERE idMenu=%s",
                    (tipeMenu, namaMenu, hargaa, idMenu),
                )
                conn.commit()
                # FIX: cek apakah data benar-benar terupdate
                if curr.rowcount == 0:
                    QMessageBox.warning(self, "Tidak Ditemukan", f"ID '{idMenu}' tidak ditemukan di database.")
                    return
                QMessageBox.information(self, "Berhasil", "Data berhasil diperbarui.")
            except mysql.connector.Error as e:
                QMessageBox.critical(self, "Database Error", f"Gagal mengupdate data: {e}")
                return
            finally:
                if curr:
                    curr.close()
                if conn:
                    conn.close()

            self.loaddata()
            self.activeText(False)
            self.clearform()
            self.edit.setText('edit tabel')

    def hapusData(self):
        # FIX: validasi idMenu tidak kosong sebelum hapus
        idMenu = self.textIdMenu.text().strip()
        if not idMenu:
            QMessageBox.warning(self, "Pilih Data", "Pilih baris yang ingin dihapus terlebih dahulu.")
            return

        # FIX: tambah konfirmasi sebelum hapus agar tidak terhapus tidak sengaja
        konfirmasi = QMessageBox.question(
            self, "Konfirmasi Hapus",
            f"Yakin ingin menghapus item dengan ID '{idMenu}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if konfirmasi != QMessageBox.Yes:
            return

        conn = None
        curr = None
        try:
            conn = get_connection()
            curr = conn.cursor()
            curr.execute("DELETE FROM tbbarang WHERE idMenu=%s", (idMenu,))
            conn.commit()
            if curr.rowcount == 0:
                QMessageBox.warning(self, "Tidak Ditemukan", f"ID '{idMenu}' tidak ditemukan.")
                return
            QMessageBox.information(self, "Berhasil", "Data berhasil dihapus.")
        except mysql.connector.Error as e:
            QMessageBox.critical(self, "Database Error", f"Gagal menghapus data: {e}")
            return
        finally:
            if curr:
                curr.close()
            if conn:
                conn.close()

        self.loaddata()
        self.activeText(False)
        self.clearform()

    def batals(self):
        # FIX: sederhanakan — langsung reset semua state tanpa cek kondisi ganda
        self.simpan.setText('baru')
        self.edit.setText('edit tabel')
        self.clearform()
        self.activeText(False)

    def simpandata(self):
        cb = self.simpan.text()
        if cb == 'baru':
            self.activeText(True)
            self.clearform()
            self.simpan.setText('simpan')
            # FIX: pastikan tombol edit tidak bentrok di mode tambah data baru
            self.edit.setText('edit tabel')

        elif cb == 'simpan':
            if not self._validate_form():
                return

            idMenu   = self.textIdMenu.text().strip()
            tipeMenu = self.cbKategori.currentText()
            namaMenu = self.textMenu.text().strip()
            hargaa   = self.textHarga.text().strip()

            conn = None
            curr = None
            try:
                conn = get_connection()
                curr = conn.cursor()
                curr.execute(
                    "INSERT INTO tbbarang (idMenu, kategori, namaMenu, harga) VALUES (%s, %s, %s, %s)",
                    (idMenu, tipeMenu, namaMenu, hargaa)
                )
                conn.commit()
                QMessageBox.information(self, "Berhasil", "Data berhasil disimpan.")
            except mysql.connector.IntegrityError:
                # FIX: tangkap error duplikat primary key secara spesifik
                QMessageBox.critical(self, "Duplikasi", f"ID Menu '{idMenu}' sudah ada. Gunakan ID yang berbeda.")
                return
            except mysql.connector.Error as e:
                QMessageBox.critical(self, "Database Error", f"Gagal menyimpan data: {e}")
                return
            finally:
                if curr:
                    curr.close()
                if conn:
                    conn.close()

            # FIX: ubah state tombol SETELAH commit berhasil, bukan sebelumnya
            self.simpan.setText('baru')
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
        self.tabelWidtg()
        self.loaddata2()
        self.tot()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def tabelWidtg(self):
        header = self.tableWidget_2.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

    def tombol(self):
        self.keluar.clicked.connect(self.kembali)

    def loaddata2(self):
        conn = None
        curr = None
        try:
            conn = get_connection()
            curr = conn.cursor()
            curr.execute("SELECT * FROM laporan")
            result = curr.fetchall()
        except Exception as e:
            QMessageBox.critical(self, 'Database Error', f'Gagal memuat laporan: {e}')
            return
        finally:
            if curr:
                curr.close()
            if conn:
                conn.close()

        self.tableWidget_2.setRowCount(len(result))
        for row, item in enumerate(result):
            self.tableWidget_2.setItem(row, 0, QtWidgets.QTableWidgetItem(str(item[1])))
            self.tableWidget_2.setItem(row, 1, QtWidgets.QTableWidgetItem(str(item[2])))
            self.tableWidget_2.setItem(row, 2, QtWidgets.QTableWidgetItem(str(item[3])))

    def tot(self):
        tota = 0.0
        conn = None
        curr = None
        try:
            conn = get_connection()
            curr = conn.cursor()
            curr.execute("SELECT total FROM laporan")
            rows = curr.fetchall()
            for row in rows:
                # FIX: skip nilai None agar tidak crash saat float(None)
                if row[0] is not None:
                    tota += float(row[0])
        except Exception as e:
            QMessageBox.critical(self, 'Database Error', f'Gagal memuat total: {e}')
        finally:
            if curr:
                curr.close()
            if conn:
                conn.close()

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
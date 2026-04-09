from PyQt5.QtWidgets import (QApplication, QDialog, QWidget, QPushButton,
                             QLineEdit, QLabel, QTableWidget, QMessageBox,
                             QHeaderView, QDesktopWidget)
from PyQt5 import QtWidgets, uic, QtGui, QtPrintSupport
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtGui import QPainter
import sys
import mysql.connector


def get_connection():
    return mysql.connector.connect(
        user='andriefendy',
        password='Andri2608.',
        host='127.0.0.1',
        database='warungme'
    )


class lognin(QDialog):
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
        conn = get_connection()
        curr = conn.cursor()
        curr.execute("SELECT * FROM auth WHERE username=%s AND pass=%s", (username, password))
        user = curr.fetchone()
        curr.close()
        conn.close()
        if user is not None:
            self.masukkasir()
        else:
            self.error.setText("Masukkan akun yang benar!")

    def masukkasir(self):
        self.openkasir = kasir()
        self.openkasir.show()
        self.close()


class kasir(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("CheckOut.ui", self)
        self.center()
        self.setWindowTitle("Check Out — Kasir")

        # Koneksi sinyal
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
        # Table Daftar Menu
        h1 = self.table_1.horizontalHeader()
        h1.setSectionResizeMode(QHeaderView.Stretch)
        self.table_1.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_1.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_1.verticalHeader().setVisible(False)
        self.table_1.setAlternatingRowColors(True)
        self.table_1.setStyleSheet(
            self.table_1.styleSheet() +
            "QTableWidget { alternate-background-color: #1e2538; }"
        )

        # Table Keranjang
        h2 = self.table_2.horizontalHeader()
        h2.setSectionResizeMode(QHeaderView.Stretch)
        self.table_2.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_2.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_2.verticalHeader().setVisible(False)
        self.table_2.setAlternatingRowColors(True)
        self.table_2.setStyleSheet(
            self.table_2.styleSheet() +
            "QTableWidget { alternate-background-color: #1e2538; }"
        )

    def activeText(self, enabled):
        self.kategori.setEnabled(enabled)
        self.pilihanmenu.setEnabled(enabled)
        self.harga.setEnabled(enabled)
        self.totalbayar.setEnabled(enabled)
        self.kembalian.setEnabled(enabled)
        self.jumlah2.setEnabled(enabled)

    def clearform(self):
        self.kategori.clear()
        self.pilihanmenu.clear()
        self.harga.clear()
        self.jumlah.setText('0')

    def clearform2(self):
        self.totalbayar.clear()
        self.uangpembayaran.clear()
        self.table_2.clearContents()
        self.table_2.setRowCount(0)
        self.kembalian.clear()
        self.pemesan.clear()
        self.jumlah2.clear()

    def bayarr(self):
        namapembeli = self.pemesan.text().strip()
        uang_text = self.uangpembayaran.text().strip()
        total_text = self.totalbayar.text().strip()

        if not namapembeli:
            QMessageBox.warning(self, "Perhatian", "Nama pemesan belum diisi!")
            return
        if not uang_text or not total_text:
            QMessageBox.warning(self, "Perhatian", "Total bayar atau uang pembayaran kosong!")
            return

        try:
            total = float(total_text)
            payment = float(uang_text)
        except ValueError:
            QMessageBox.warning(self, "Error", "Format angka tidak valid!")
            return

        if payment >= total:
            change = payment - total
            self.kembalian.setText(f"{change:.0f}")
            conn = get_connection()
            curr = conn.cursor()
            curr.execute(
                "INSERT INTO laporan (nama, jumlah, total) VALUES (%s, %s, %s)",
                (namapembeli, self.jumlah2.text(), total_text)
            )
            conn.commit()
            curr.close()
            conn.close()
            QMessageBox.information(self, "Sukses", "✅ Pembayaran Berhasil!")
            self.cetak_struk()
        else:
            kekurangan = total - payment
            self.kembalian.setText("Uang Kurang")
            QMessageBox.warning(self, "Pembayaran Gagal",
                                f"Uang kurang Rp {kekurangan:,.0f}")

    def simpandat(self):
        kategori = self.kategori.text()
        menu = self.pilihanmenu.text()
        harga = self.harga.text()
        jumlah = self.jumlah.text()

        if not jumlah or not menu:
            QMessageBox.warning(self, "Perhatian", "Pilih menu dan isi jumlah terlebih dahulu!")
            return

        try:
            nilai_jumlah = float(jumlah)
            nilai_harga = float(harga)
        except ValueError:
            QMessageBox.warning(self, "Error", "Jumlah atau harga tidak valid!")
            return

        row = self.table_2.rowCount()
        self.table_2.insertRow(row)
        hitung = nilai_jumlah * nilai_harga

        self.table_2.setItem(row, 0, QtWidgets.QTableWidgetItem(kategori))
        self.table_2.setItem(row, 1, QtWidgets.QTableWidgetItem(menu))
        self.table_2.setItem(row, 2, QtWidgets.QTableWidgetItem(f"{nilai_harga:.0f}"))
        self.table_2.setItem(row, 3, QtWidgets.QTableWidgetItem(f"{nilai_jumlah:.0f}"))
        self.table_2.setItem(row, 4, QtWidgets.QTableWidgetItem(f"{hitung:.0f}"))

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

            margin = 70
            x = margin
            y = margin
            lh = 150
            pw = printer.pageRect().width()

            def center_text(text, font, ypos):
                painter.setFont(font)
                w = painter.fontMetrics().boundingRect(text).width()
                painter.drawText((pw - w) // 2, ypos, text)

            center_text("Restoran Cepat Saji", QtGui.QFont("Arial", 12, QtGui.QFont.Bold), y); y += lh
            center_text("Universitas Borneo Tarakan", QtGui.QFont("Arial", 11), y); y += lh
            center_text("Teknik Komputer", QtGui.QFont("Arial", 11, QtGui.QFont.Bold), y); y += lh
            center_text("=" * 40, QtGui.QFont("Arial", 10), y); y += lh

            painter.setFont(QtGui.QFont("Arial", 11, QtGui.QFont.Bold))
            painter.drawText(x, y, "Struk Belanja"); y += lh

            painter.setFont(QtGui.QFont("Arial", 10))
            painter.drawText(x, y, "Daftar Belanja:"); y += lh

            for row in range(self.table_2.rowCount()):
                nama = self.table_2.item(row, 1).text()
                hrg = self.table_2.item(row, 2).text()
                jml = self.table_2.item(row, 3).text()
                sub = self.table_2.item(row, 4).text()
                painter.setFont(QtGui.QFont("Arial", 10))
                painter.drawText(x, y, f"{nama}: Rp{hrg} x {jml}")
                sw = painter.fontMetrics().boundingRect(f"Rp{sub}").width()
                painter.drawText(pw - margin - sw, y, f"Rp{sub}")
                y += lh

            center_text("=" * 40, QtGui.QFont("Arial", 10), y); y += lh

            total_val = self.hitung_total()
            bayar_val = self.uangpembayaran.text()

            painter.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
            painter.drawText(x, y, "Total:")
            tv = f"Rp{total_val:,}"
            tw = painter.fontMetrics().boundingRect(tv).width()
            painter.drawText(pw - margin - tw, y, tv); y += lh

            painter.drawText(x, y, "Bayar:")
            bv = f"Rp{bayar_val}"
            bw = painter.fontMetrics().boundingRect(bv).width()
            painter.drawText(pw - margin - bw, y, bv); y += lh

            painter.setFont(QtGui.QFont("Arial", 10))
            painter.drawText(x, y, "Kembalian:")
            try:
                kb = int(bayar_val) - int(total_val)
                kv = f"Rp{kb:,}"
            except Exception:
                kv = "—"
            kw = painter.fontMetrics().boundingRect(kv).width()
            painter.drawText(pw - margin - kw, y, kv); y += lh

            center_text("=" * 40, QtGui.QFont("Arial", 10), y); y += lh
            center_text("Terima Kasih Telah Berbelanja!", QtGui.QFont("Arial", 12, QtGui.QFont.Bold), y)

            painter.end()
            self.clearform2()

    def jum(self):
        jum = 0
        for row in range(self.table_2.rowCount()):
            item = self.table_2.item(row, 3)
            if item:
                jum += float(item.text())
        self.jumlah2.setText(f"{jum:.0f}")

    def hitung_total(self):
        total = 0
        for row in range(self.table_2.rowCount()):
            try:
                h = float(self.table_2.item(row, 2).text())
                j = float(self.table_2.item(row, 3).text())
                total += h * j
            except (ValueError, AttributeError):
                pass
        return total

    def tot(self):
        total = 0
        for row in range(self.table_2.rowCount()):
            item = self.table_2.item(row, 4)
            if item:
                try:
                    total += float(item.text())
                except ValueError:
                    pass
        self.totalbayar.setText(f"{total:.0f}")

    def hapuss(self):
        row = self.table_2.currentRow()
        if row != -1:
            self.table_2.removeRow(row)
            self.tot()
            self.jum()
        else:
            QMessageBox.information(self, "Info", "Pilih item yang ingin dihapus!")

    def getitem(self):
        row = self.table_1.currentRow()
        if row < 0:
            return
        self.kategori.setText(self.table_1.item(row, 0).text())
        self.pilihanmenu.setText(self.table_1.item(row, 1).text())
        self.harga.setText(self.table_1.item(row, 2).text())
        self.jumlah.setFocus()

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
            self.table_1.setItem(row, 0, QtWidgets.QTableWidgetItem(item[1]))
            self.table_1.setItem(row, 1, QtWidgets.QTableWidgetItem(item[2]))
            self.table_1.setItem(row, 2, QtWidgets.QTableWidgetItem(str(item[3])))

    def keluars(self):
        self.logout = lognin()
        self.logout.show()
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = lognin()
    window.show()
    sys.exit(app.exec_())
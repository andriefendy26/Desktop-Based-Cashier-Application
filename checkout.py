from PyQt5.QtWidgets import (QApplication, QDialog, QTableWidget, QMessageBox,
                             QHeaderView, QDesktopWidget)
from PyQt5 import QtWidgets, uic, QtGui
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog
from PyQt5.QtGui import QPainter, QFont, QFontMetrics
from PyQt5.QtCore import Qt
import sys
import mysql.connector


def get_connection():
    return mysql.connector.connect(
        user='root',
        password='',
        host='127.0.0.1',
        database='warungme',
        use_pure=True
    )


class lognin(QDialog):
    def __init__(self):
        super().__init__()
        print("Load Login.ui...")
        try:
            uic.loadUi("Login.ui", self)
            print("Login.ui sukses")
            self.center()
            self.masuk.clicked.connect(self.loginfungsion)
        except Exception as e:
            print(f"Error loading UI: {e}")
            raise

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
            print("Login berhasil!")
            self.masukkasir()
        else:
            print("Login gagal: Akun tidak ditemukan.")
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

        # Koneksi sinyal — dua tabel menu terpisah
        self.table_makanan.clicked.connect(lambda: self.getitem(self.table_makanan))
        self.table_minuman.clicked.connect(lambda: self.getitem(self.table_minuman))

        self.simpan.clicked.connect(self.simpandat)
        self.bayar.clicked.connect(self.bayarr)
        self.keluar.clicked.connect(self.keluars)
        self.hapus.clicked.connect(self.hapuss)
        self.batal.clicked.connect(self.batals)

        # self._tambah_tombol_preview()

        self.activeText(False)
        self.tableWidgt()
        self.loaddata()

    # def _tambah_tombol_preview(self):
    #     self.preview_btn = QtWidgets.QPushButton("🔍  Preview Struk", self.widget)
    #     self.preview_btn.setObjectName("preview_btn")
    #     self.preview_btn.setGeometry(320, 690, 160, 36)
    #     self.preview_btn.setStyleSheet("""
    #         QPushButton#preview_btn {
    #             background-color: #7c3aed;
    #             color: #ede9fe;
    #             border-radius: 8px;
    #             padding: 8px 18px;
    #             font-size: 13px;
    #             font-weight: 600;
    #             border: none;
    #         }
    #         QPushButton#preview_btn:hover { background-color: #8b5cf6; }
    #         QPushButton#preview_btn:pressed { background-color: #6d28d9; }
    #     """)
    #     self.preview_btn.clicked.connect(self.preview_struk)
    #     self.preview_btn.show()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def _setup_table(self, table):
        h = table.horizontalHeader()
        h.setSectionResizeMode(QHeaderView.Stretch)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        table.setStyleSheet(
            table.styleSheet() +
            "QTableWidget { alternate-background-color: #1e2538; }"
        )

    def tableWidgt(self):
        self._setup_table(self.table_makanan)
        self._setup_table(self.table_minuman)
        self._setup_table(self.table_2)

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

    # ─────────────────────────────────────────────
    #  PRINTER
    # ─────────────────────────────────────────────
    def _buat_printer(self):
        printer = QPrinter(QPrinter.HighResolution)
        printer.setPageSize(QPrinter.A6)
        printer.setOrientation(QPrinter.Portrait)
        printer.setFullPage(False)
        return printer

    def _render_struk(self, printer):
        painter = QPainter()
        if not painter.begin(printer):
            QMessageBox.critical(self, "Error", "Gagal memulai painter pada printer!")
            return

        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        page_rect = printer.pageRect()
        pw  = page_rect.width()
        dpi = printer.resolution()

        def pt(points):
            return int(points * dpi / 72)

        margin = pt(4)
        lh     = pt(14)

        def make_font(size_pt, bold=False):
            f = QFont("Courier New", size_pt)
            f.setBold(bold)
            f.setPixelSize(pt(size_pt))
            return f

        def draw_center(text, font, y):
            painter.setFont(font)
            fm = QFontMetrics(font)
            w  = fm.horizontalAdvance(text)
            painter.drawText((pw - w) // 2, y, text)

        def draw_left(text, font, y):
            painter.setFont(font)
            painter.drawText(margin, y, text)

        def draw_right(text, font, y):
            painter.setFont(font)
            fm = QFontMetrics(font)
            w  = fm.horizontalAdvance(text)
            painter.drawText(pw - margin - w, y, text)

        def draw_lr(left_text, right_text, font, y):
            draw_left(left_text, font, y)
            draw_right(right_text, font, y)

        def separator(y, char="─"):
            draw_center(char * 32, make_font(7), y)

        total_val  = self.hitung_total()
        bayar_text = self.uangpembayaran.text().strip()
        try:
            bayar_val = float(bayar_text)
        except ValueError:
            bayar_val = 0.0
        kembali_val = bayar_val - total_val

        y = pt(6)

        draw_center("Restoran Cepat Saji",       make_font(10, bold=True), y); y += lh
        draw_center("Universitas Borneo Tarakan", make_font(8),             y); y += lh
        draw_center("Teknik Komputer",            make_font(9, bold=True),  y); y += lh
        separator(y); y += lh
        draw_center("STRUK BELANJA", make_font(10, bold=True), y); y += int(lh * 1.2)

        nama_pemesan = self.pemesan.text().strip() or "-"
        draw_lr("Pemesan :", nama_pemesan, make_font(8), y); y += lh
        separator(y); y += lh
        draw_left("Item Pesanan:", make_font(8, bold=True), y); y += lh

        for row in range(self.table_2.rowCount()):
            nama = self.table_2.item(row, 1).text()
            hrg  = self.table_2.item(row, 2).text()
            jml  = self.table_2.item(row, 3).text()
            sub  = self.table_2.item(row, 4).text()
            draw_left(f"  {nama}", make_font(8), y); y += lh
            draw_lr(f"   Rp{int(float(hrg)):,} x {jml}",
                    f"Rp{int(float(sub)):,}", make_font(8), y); y += lh

        separator(y); y += lh

        font_bold = make_font(9, bold=True)
        font_norm = make_font(8)
        draw_lr("Total Belanja :", f"Rp{int(total_val):,}",   font_bold, y); y += lh
        draw_lr("Uang Bayar    :", f"Rp{int(bayar_val):,}",   font_norm, y); y += lh
        draw_lr("Kembalian     :", f"Rp{int(kembali_val):,}", font_bold, y); y += lh

        separator(y, "═"); y += int(lh * 1.3)
        draw_center("Terima Kasih Telah Berbelanja!", make_font(9, bold=True), y); y += lh
        draw_center("Selamat Makan! 😊",              make_font(8),            y)

        painter.end()

    # def preview_struk(self):
    #     if self.table_2.rowCount() == 0:
    #         QMessageBox.information(self, "Info", "Keranjang masih kosong!")
    #         return
    #     printer = self._buat_printer()
    #     preview = QPrintPreviewDialog(printer, self)
    #     preview.setWindowTitle("Preview Struk")
    #     preview.paintRequested.connect(self._render_struk)
    #     preview.exec_()

    def cetak_struk(self):
        printer = self._buat_printer()
        dialog  = QPrintDialog(printer, self)
        if dialog.exec_() == QPrintDialog.Accepted:
            self._render_struk(printer)
            self.clearform2()

    # ─────────────────────────────────────────────
    #  KALKULASI
    # ─────────────────────────────────────────────
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

    def getitem(self, table):
        row = table.currentRow()
        if row < 0:
            return
        self.kategori.setText(table.item(row, 0).text())
        self.pilihanmenu.setText(table.item(row, 1).text())
        self.harga.setText(table.item(row, 2).text())
        self.jumlah.setFocus()

    def batals(self):
        self.clearform()
        self.clearform2()

    def loaddata(self):
        """Load data dari DB, pisahkan ke tabel makanan & minuman."""
        conn = get_connection()
        curr = conn.cursor()
        curr.execute("SELECT * FROM tbbarang")
        result = curr.fetchall()
        curr.close()
        conn.close()

        # Filter berdasarkan kolom kategori (index 1)
        makanan = [r for r in result if r[1].strip().lower() == "makanan"]
        minuman = [r for r in result if r[1].strip().lower() == "minuman"]

        self.table_makanan.setRowCount(len(makanan))
        for i, item in enumerate(makanan):
            self.table_makanan.setItem(i, 0, QtWidgets.QTableWidgetItem(item[1]))
            self.table_makanan.setItem(i, 1, QtWidgets.QTableWidgetItem(item[2]))
            self.table_makanan.setItem(i, 2, QtWidgets.QTableWidgetItem(str(item[3])))

        self.table_minuman.setRowCount(len(minuman))
        for i, item in enumerate(minuman):
            self.table_minuman.setItem(i, 0, QtWidgets.QTableWidgetItem(item[1]))
            self.table_minuman.setItem(i, 1, QtWidgets.QTableWidgetItem(item[2]))
            self.table_minuman.setItem(i, 2, QtWidgets.QTableWidgetItem(str(item[3])))

    def keluars(self):
        self.logout = lognin()
        self.logout.show()
        self.close()


if __name__ == "__main__":
    print("1. Mulai aplikasi")
    app = QApplication(sys.argv)
    print("2. QApplication berhasil")
    window = lognin()
    print("3. Login.ui berhasil dibuka")
    window.show()
    print("4. Window tampil")
    sys.exit(app.exec_())
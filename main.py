from PyQt5.QtWidgets import (QApplication, QDialog, QTableWidget, QMessageBox,
                             QHeaderView, QDesktopWidget, QInputDialog)
from PyQt5 import QtWidgets, uic, QtGui
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtGui import QPainter, QFont, QFontMetrics
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout,
                             QLabel, QSpinBox, QPushButton, QDateEdit)
import sys
from datetime import datetime, time
import mysql.connector


# ─────────────────────────────────────────────
#  DATABASE CONNECTION
# ─────────────────────────────────────────────
def get_connection():
    return mysql.connector.connect(
        user='root',
        password='',
        host='127.0.0.1',
        database='warungme',
        use_pure=True
    )


# ─────────────────────────────────────────────
#  DIALOG EDIT JUMLAH (untuk fitur edit keranjang)
# ─────────────────────────────────────────────
class EditJumlahDialog(QDialog):
    def __init__(self, nama_item, jml_lama, parent=None, stock_maks=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Jumlah")
        self.setFixedWidth(340)
        self.setModal(True)
        self.stock_maks = stock_maks
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1f2e;
                border: 1px solid #2d3548;
                border-radius: 14px;
            }
            QLabel#lbl_title {
                color: #38bdf8;
                font-size: 15px;
                font-weight: 700;
            }
            QLabel#lbl_sub {
                color: #94a3b8;
                font-size: 12px;
            }
            QLabel#lbl_field {
                color: #94a3b8;
                font-size: 12px;
            }
            QSpinBox {
                background-color: #252d3d;
                border: 1.5px solid #38bdf8;
                border-radius: 8px;
                color: #f1f5f9;
                font-size: 18px;
                font-weight: 700;
                padding: 6px 10px;
                min-height: 38px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 0; border: none;
            }
            QPushButton#btn_minus, QPushButton#btn_plus {
                background-color: #252d3d;
                border: 1px solid #2d3548;
                border-radius: 8px;
                color: #38bdf8;
                font-size: 20px;
                font-weight: 700;
                min-width: 38px;
                min-height: 38px;
                padding: 0;
            }
            QPushButton#btn_minus:hover, QPushButton#btn_plus:hover {
                background-color: #1e3a5f;
            }
            QPushButton#btn_minus:pressed, QPushButton#btn_plus:pressed {
                background-color: #1e40af;
            }
            QPushButton#btn_ok {
                background-color: #059669;
                border: none;
                border-radius: 8px;
                color: #ecfdf5;
                font-size: 13px;
                font-weight: 700;
                padding: 9px 0;
                min-height: 38px;
            }
            QPushButton#btn_ok:hover  { background-color: #10b981; }
            QPushButton#btn_ok:pressed { background-color: #047857; }
            QPushButton#btn_batal {
                background-color: #374151;
                border: 1px solid #4b5563;
                border-radius: 8px;
                color: #d1d5db;
                font-size: 13px;
                font-weight: 600;
                padding: 9px 0;
                min-height: 38px;
            }
            QPushButton#btn_batal:hover { background-color: #4b5563; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 20)
        layout.setSpacing(8)

        lbl_title = QLabel("✏  Edit Jumlah")
        lbl_title.setObjectName("lbl_title")

        lbl_sub = QLabel(f"Item: <b style='color:#f1f5f9'>{nama_item}</b>")
        lbl_sub.setObjectName("lbl_sub")
        lbl_sub.setTextFormat(Qt.RichText)

        lbl_field = QLabel("Jumlah pesanan")
        lbl_field.setObjectName("lbl_field")

        self.spin = QSpinBox()
        # Batasi maksimal sesuai stock yang tersedia (jika diketahui)
        batas_atas = int(stock_maks) if stock_maks is not None else 999
        batas_atas = max(batas_atas, jml_lama)  # jangan sampai lebih kecil dari nilai lama
        self.spin.setRange(1, batas_atas if batas_atas > 0 else 1)
        self.spin.setValue(jml_lama)
        self.spin.setAlignment(Qt.AlignCenter)

        btn_minus = QPushButton("−")
        btn_minus.setObjectName("btn_minus")
        btn_minus.setFixedSize(38, 38)
        btn_minus.clicked.connect(lambda: self.spin.setValue(self.spin.value() - 1))

        btn_plus = QPushButton("+")
        btn_plus.setObjectName("btn_plus")
        btn_plus.setFixedSize(38, 38)
        btn_plus.clicked.connect(lambda: self.spin.setValue(self.spin.value() + 1))

        spin_row = QHBoxLayout()
        spin_row.setSpacing(8)
        spin_row.addWidget(btn_minus)
        spin_row.addWidget(self.spin)
        spin_row.addWidget(btn_plus)

        lbl_stock_info = QLabel(
            f"Stok tersedia: {stock_maks:.0f}" if stock_maks is not None else ""
        )
        lbl_stock_info.setObjectName("lbl_sub")

        btn_batal = QPushButton("↩  Batal")
        btn_batal.setObjectName("btn_batal")
        btn_batal.clicked.connect(self.reject)

        btn_ok = QPushButton("✔  Simpan")
        btn_ok.setObjectName("btn_ok")
        btn_ok.clicked.connect(self.accept)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addWidget(btn_batal)
        btn_row.addWidget(btn_ok)

        layout.addWidget(lbl_title)
        layout.addWidget(lbl_sub)
        layout.addSpacing(8)
        layout.addWidget(lbl_field)
        layout.addLayout(spin_row)
        if stock_maks is not None:
            layout.addWidget(lbl_stock_info)
        layout.addSpacing(8)
        layout.addLayout(btn_row)

    def get_value(self):
        return self.spin.value()


# ─────────────────────────────────────────────
#  LOGIN
# ─────────────────────────────────────────────
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
        conn = get_connection()
        curr = conn.cursor()
        curr.execute("SELECT * FROM auth WHERE username=%s AND pass=%s", (username, password))
        user = curr.fetchone()
        curr.close()
        conn.close()
        if user:
            self.masukkasir()
            QMessageBox.information(self, 'Alert', 'Login berhasil')
        else:
            self.error.setText("Masukkan akun yang benar")

    def masukkasir(self):
        self.openkasir = Pilihan()
        self.openkasir.show()
        self.close()


# ─────────────────────────────────────────────
#  PILIHAN — sekarang ada 3 menu: Checkout, Daftar Menu, Laporan
# ─────────────────────────────────────────────
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
        self.Checkout.clicked.connect(self.BukaCheckout)   # tombol baru
        self.Menu.clicked.connect(self.Dftrmenu)
        self.Lprn.clicked.connect(self.Lapar)
        self.logout.clicked.connect(self.Keluar)

    def BukaCheckout(self):
        self.openkasir = kasir(parent_pilihan=self)
        self.openkasir.show()
        self.hide()   # sembunyikan Pilihan, bukan close, agar kasir bisa kembali

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


# ─────────────────────────────────────────────
#  KASIR / CHECK OUT
# ─────────────────────────────────────────────
class kasir(QDialog):
    def __init__(self, parent_pilihan=None):
        super().__init__()
        uic.loadUi("CheckOut.ui", self)
        self.center()
        self.setWindowTitle("Check Out — Kasir")

        # Simpan referensi ke window Pilihan agar bisa kembali
        self._parent_pilihan = parent_pilihan

        self._all_makanan = []
        self._all_minuman = []

        # Item yang sedang dipilih dari tabel makanan/minuman
        self._selected_id = None
        self._selected_stock = None

        self.table_makanan.clicked.connect(lambda: self.getitem(self.table_makanan))
        self.table_minuman.clicked.connect(lambda: self.getitem(self.table_minuman))

        self.simpan.clicked.connect(self.simpandat)
        self.bayar.clicked.connect(self.bayarr)
        self.keluar.clicked.connect(self.keluars)
        self.hapus.clicked.connect(self.hapuss)
        self.batal.clicked.connect(self.batals)
        self.edit_item.clicked.connect(self.edit_keranjang)

        self.search_makanan.textChanged.connect(self.filter_makanan)
        self.search_minuman.textChanged.connect(self.filter_minuman)

        self.activeText(False)
        self.tableWidgt()
        self.loaddata()

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
        self.jumlah.clear()
        self._selected_id = None
        self._selected_stock = None

    def clearform2(self):
        self.totalbayar.clear()
        self.uangpembayaran.clear()
        self.table_2.clearContents()
        self.table_2.setRowCount(0)
        self.kembalian.clear()
        self.pemesan.clear()
        self.jumlah2.clear()

    def loaddata(self):
        try:
            conn = get_connection()
            curr = conn.cursor()
            curr.execute("SELECT * FROM tbbarang")
            rows = curr.fetchall()

            col_names = [desc[0].lower() for desc in curr.description]
            curr.close()
            conn.close()

            def _col_index(candidates):
                for c in candidates:
                    if c in col_names:
                        return col_names.index(c)
                return None

            idx_id       = _col_index(['id', 'kode', 'kd_barang', 'kd', 'idmenu'])
            idx_kategori = _col_index(['kategori', 'category', 'jenis', 'tipe'])
            idx_nama     = _col_index(['nama', 'nama_barang', 'menu', 'nama_menu', 'item', 'namamenu'])
            idx_harga    = _col_index(['harga', 'price', 'harga_jual', 'harga_barang'])
            idx_stock    = _col_index(['stock', 'stok', 'qty', 'jumlah_stock', 'jumlah_stok'])

            if None in (idx_id, idx_kategori, idx_nama, idx_harga):
                idx_id, idx_kategori, idx_nama, idx_harga = 0, 1, 2, 3
            if idx_stock is None:
                idx_stock = 4 if len(col_names) > 4 else None

            processed = []
            for r in rows:
                try:
                    stock_val = float(r[idx_stock]) if idx_stock is not None else 0.0
                    processed.append((
                        str(r[idx_id]),
                        str(r[idx_kategori]),
                        str(r[idx_nama]),
                        float(r[idx_harga]),
                        stock_val
                    ))
                except Exception as e:
                    print(f"[WARNING] Baris dilewati: {r} — {e}")

            self._all_makanan = [r for r in processed if 'makanan' in r[1].lower()]
            self._all_minuman = [r for r in processed if 'minuman' in r[1].lower()]

            self.filter_makanan("")
            self.filter_minuman("")

        except Exception as e:
            QMessageBox.critical(self, "Error DB", f"Gagal memuat data menu:\n{e}")

    def filter_makanan(self, text):
        keyword = text.strip().lower()
        filtered = (
            [r for r in self._all_makanan if keyword in r[2].lower() or keyword in r[1].lower()]
            if keyword else self._all_makanan
        )
        self.table_makanan.setRowCount(len(filtered))
        for i, item in enumerate(filtered):
            self.table_makanan.setItem(i, 0, QtWidgets.QTableWidgetItem(item[0]))
            self.table_makanan.setItem(i, 1, QtWidgets.QTableWidgetItem(item[1]))
            self.table_makanan.setItem(i, 2, QtWidgets.QTableWidgetItem(item[2]))
            self.table_makanan.setItem(i, 3, QtWidgets.QTableWidgetItem(f"{item[3]:.0f}"))
            if self.table_makanan.columnCount() > 4:
                self.table_makanan.setItem(i, 4, QtWidgets.QTableWidgetItem(f"{item[4]:.0f}"))

    def filter_minuman(self, text):
        keyword = text.strip().lower()
        filtered = (
            [r for r in self._all_minuman if keyword in r[2].lower() or keyword in r[1].lower()]
            if keyword else self._all_minuman
        )
        self.table_minuman.setRowCount(len(filtered))
        for i, item in enumerate(filtered):
            self.table_minuman.setItem(i, 0, QtWidgets.QTableWidgetItem(item[0]))
            self.table_minuman.setItem(i, 1, QtWidgets.QTableWidgetItem(item[1]))
            self.table_minuman.setItem(i, 2, QtWidgets.QTableWidgetItem(item[2]))
            self.table_minuman.setItem(i, 3, QtWidgets.QTableWidgetItem(f"{item[3]:.0f}"))
            if self.table_minuman.columnCount() > 4:
                self.table_minuman.setItem(i, 4, QtWidgets.QTableWidgetItem(f"{item[4]:.0f}"))

    def getitem(self, table):
        row = table.currentRow()
        if row < 0:
            return
        id_item  = table.item(row, 0).text()
        kategori = table.item(row, 1).text()
        nama     = table.item(row, 2).text()
        harga    = table.item(row, 3).text()

        # Ambil stock terkini dari sumber data (bukan dari tabel, supaya selalu akurat)
        sumber = self._all_makanan if 'makanan' in kategori.lower() else self._all_minuman
        stock = next((r[4] for r in sumber if r[0] == id_item), 0.0)

        self.kategori.setText(kategori)
        self.pilihanmenu.setText(nama)
        self.harga.setText(harga)
        self.jumlah.setText("1")
        self.jumlah.setFocus()
        self.jumlah.selectAll()

        self._selected_id = id_item
        self._selected_stock = stock

        if stock <= 0:
            QMessageBox.warning(self, "Stok Habis", f"Stok untuk '{nama}' sudah habis!")

    def _jumlah_di_keranjang(self, menu):
        """Total kuantitas item 'menu' yang sudah ada di keranjang."""
        for r in range(self.table_2.rowCount()):
            item = self.table_2.item(r, 1)
            if item and item.text() == menu:
                try:
                    return float(self.table_2.item(r, 3).text())
                except (ValueError, AttributeError):
                    return 0.0
        return 0.0

    def simpandat(self):
        kategori = self.kategori.text().strip()
        menu     = self.pilihanmenu.text().strip()
        harga    = self.harga.text().strip()
        jumlah   = self.jumlah.text().strip()

        if not menu:
            QMessageBox.warning(self, "Perhatian", "Pilih menu dari daftar terlebih dahulu!")
            return
        if not jumlah:
            QMessageBox.warning(self, "Perhatian", "Isi jumlah pesanan!")
            return
        if not harga:
            QMessageBox.warning(self, "Perhatian", "Harga tidak boleh kosong!")
            return

        try:
            nilai_jumlah = float(jumlah)
            nilai_harga  = float(harga)
        except ValueError:
            QMessageBox.warning(self, "Error", "Jumlah atau harga harus berupa angka!")
            return

        if nilai_jumlah <= 0:
            QMessageBox.warning(self, "Perhatian", "Jumlah harus lebih dari 0!")
            return

        # ── Validasi stock ──
        if self._selected_stock is not None:
            sudah_di_keranjang = self._jumlah_di_keranjang(menu)
            if sudah_di_keranjang + nilai_jumlah > self._selected_stock:
                sisa = self._selected_stock - sudah_di_keranjang
                QMessageBox.warning(
                    self, "Stok Tidak Cukup",
                    f"Stok '{menu}' tersisa {sisa:.0f} (sudah {sudah_di_keranjang:.0f} di keranjang)."
                )
                return

        for r in range(self.table_2.rowCount()):
            if self.table_2.item(r, 1) and self.table_2.item(r, 1).text() == menu:
                jml_lama = float(self.table_2.item(r, 3).text())
                jml_baru = jml_lama + nilai_jumlah
                sub_baru = jml_baru * nilai_harga
                self.table_2.setItem(r, 3, QtWidgets.QTableWidgetItem(f"{jml_baru:.0f}"))
                self.table_2.setItem(r, 4, QtWidgets.QTableWidgetItem(f"{sub_baru:.0f}"))
                self.jum()
                self.tot()
                self.clearform()
                return

        row    = self.table_2.rowCount()
        self.table_2.insertRow(row)
        hitung = nilai_jumlah * nilai_harga

        item_kategori = QtWidgets.QTableWidgetItem(kategori)
        item_nama     = QtWidgets.QTableWidgetItem(menu)
        # Simpan id menu secara tersembunyi di item nama, dipakai saat checkout untuk update stock
        item_nama.setData(Qt.UserRole, self._selected_id)

        self.table_2.setItem(row, 0, item_kategori)
        self.table_2.setItem(row, 1, item_nama)
        self.table_2.setItem(row, 2, QtWidgets.QTableWidgetItem(f"{nilai_harga:.0f}"))
        self.table_2.setItem(row, 3, QtWidgets.QTableWidgetItem(f"{nilai_jumlah:.0f}"))
        self.table_2.setItem(row, 4, QtWidgets.QTableWidgetItem(f"{hitung:.0f}"))

        self.jum()
        self.tot()
        self.clearform()

    def edit_keranjang(self):
        row = self.table_2.currentRow()
        if row == -1:
            QMessageBox.information(self, "Info", "Pilih item di keranjang yang ingin diedit!")
            return

        nama_item  = self.table_2.item(row, 1).text()
        id_item    = self.table_2.item(row, 1).data(Qt.UserRole)
        harga_item = float(self.table_2.item(row, 2).text())
        jml_lama   = int(float(self.table_2.item(row, 3).text()))

        # Ambil stock terkini untuk item ini
        stock_maks = None
        sumber = self._all_makanan + self._all_minuman
        match = next((r for r in sumber if r[0] == id_item), None)
        if match:
            stock_maks = match[4]

        dialog = EditJumlahDialog(nama_item, jml_lama, parent=self, stock_maks=stock_maks)
        if dialog.exec_() == QDialog.Accepted:
            jumlah_baru   = dialog.get_value()
            subtotal_baru = jumlah_baru * harga_item
            self.table_2.setItem(row, 3, QtWidgets.QTableWidgetItem(f"{jumlah_baru:.0f}"))
            self.table_2.setItem(row, 4, QtWidgets.QTableWidgetItem(f"{subtotal_baru:.0f}"))
            self.jum()
            self.tot()

    def _validasi_stock_sebelum_bayar(self):
        """Cek ulang stock terbaru di DB sebelum benar-benar memotong stock.
        Mengembalikan (True, None) jika aman, atau (False, pesan_error)."""
        conn = get_connection()
        curr = conn.cursor()
        try:
            for row in range(self.table_2.rowCount()):
                id_item = self.table_2.item(row, 1).data(Qt.UserRole)
                nama    = self.table_2.item(row, 1).text()
                jml     = float(self.table_2.item(row, 3).text())
                if not id_item:
                    continue
                curr.execute("SELECT stock FROM tbbarang WHERE idMenu=%s", (id_item,))
                res = curr.fetchone()
                if res is None:
                    continue
                stock_sekarang = float(res[0])
                if jml > stock_sekarang:
                    return False, f"Stok '{nama}' tinggal {stock_sekarang:.0f}, tidak cukup untuk {jml:.0f} pesanan."
            return True, None
        finally:
            curr.close()
            conn.close()

    def bayarr(self):
        namapembeli = self.pemesan.text().strip()
        uang_text   = self.uangpembayaran.text().strip()
        total_text  = self.totalbayar.text().strip()

        if not namapembeli:
            QMessageBox.warning(self, "Perhatian", "Nama pemesan belum diisi!")
            return
        if self.table_2.rowCount() == 0:
            QMessageBox.warning(self, "Perhatian", "Keranjang masih kosong!")
            return
        if not uang_text or not total_text:
            QMessageBox.warning(self, "Perhatian", "Total bayar atau uang pembayaran kosong!")
            return

        try:
            total   = float(total_text)
            payment = float(uang_text)
        except ValueError:
            QMessageBox.warning(self, "Error", "Format angka tidak valid!")
            return

        if payment >= total:
            change = payment - total
            self.kembalian.setText(f"{change:.0f}")

            # ── Cek ulang stock sebelum memproses ──
            ok, pesan = self._validasi_stock_sebelum_bayar()
            if not ok:
                QMessageBox.warning(self, "Stok Tidak Cukup", pesan)
                return

            waktu_transaksi = datetime.now()
            try:
                conn = get_connection()
                curr = conn.cursor()

                # Simpan laporan beserta waktu transaksi
                curr.execute(
                    "INSERT INTO laporan (nama, jumlah, total, tanggal) VALUES (%s, %s, %s, %s)",
                    (namapembeli, self.jumlah2.text(), total_text, waktu_transaksi)
                )

                # Kurangi stock tiap item yang dibeli
                for row in range(self.table_2.rowCount()):
                    id_item = self.table_2.item(row, 1).data(Qt.UserRole)
                    jml     = float(self.table_2.item(row, 3).text())
                    if id_item:
                        curr.execute(
                            "UPDATE tbbarang SET stock = stock - %s WHERE idMenu = %s",
                            (jml, id_item)
                        )

                conn.commit()
                curr.close()
                conn.close()
            except Exception as e:
                QMessageBox.critical(self, "Error DB", f"Gagal menyimpan laporan/stok:\n{e}")
                return

            # ── Tanya apakah struk ingin dicetak ──
            pilihan = QMessageBox.question(
                self,
                "Pembayaran Berhasil",
                "✅ Pembayaran berhasil!\n\nApakah Anda ingin mencetak struk?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            if pilihan == QMessageBox.Yes:
                self.cetak_struk(waktu_transaksi)

            # Apapun pilihannya, keranjang tetap dikosongkan
            # dan data menu (termasuk stok terbaru) di-refresh
            self.clearform2()
            self.loaddata()
        else:
            kekurangan = total - payment
            self.kembalian.setText("Uang Kurang")
            QMessageBox.warning(self, "Pembayaran Gagal",
                                f"Uang kurang Rp {kekurangan:,.0f}")

    def _buat_printer(self):
        printer = QPrinter(QPrinter.HighResolution)
        printer.setPageSize(QPrinter.A6)
        printer.setOrientation(QPrinter.Portrait)
        printer.setFullPage(False)
        return printer

    def _render_struk(self, printer, waktu_transaksi=None):
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

        waktu = waktu_transaksi or datetime.now()
        waktu_str = waktu.strftime("%d-%m-%Y %H:%M:%S")

        y = pt(6)

        draw_center("Restoran Cepat Saji",       make_font(10, bold=True), y); y += lh
        draw_center("Universitas Borneo Tarakan", make_font(8),             y); y += lh
        draw_center("Teknik Komputer",            make_font(9, bold=True),  y); y += lh
        separator(y); y += lh
        draw_center("STRUK BELANJA", make_font(10, bold=True), y); y += lh
        draw_center(waktu_str, make_font(7), y); y += int(lh * 1.2)

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
        draw_center("Selamat Makan!",                 make_font(8),            y)

        painter.end()

    def cetak_struk(self, waktu_transaksi=None):
        """Tampilkan dialog print. Keranjang TIDAK dikosongkan di sini —
        pengosongan keranjang & refresh data menu ditangani terpusat di bayarr(),
        supaya tetap terjadi baik struk jadi dicetak maupun dialog print dibatalkan."""
        printer = self._buat_printer()
        dialog  = QPrintDialog(printer, self)
        if dialog.exec_() == QPrintDialog.Accepted:
            self._render_struk(printer, waktu_transaksi)

    def jum(self):
        jum = 0
        for row in range(self.table_2.rowCount()):
            item = self.table_2.item(row, 3)
            if item:
                try:
                    jum += float(item.text())
                except ValueError:
                    pass
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

    def batals(self):
        self.clearform()
        self.clearform2()

    def keluars(self):
        """Kembali ke menu Pilihan (bukan logout)."""
        self.clearform()
        self.clearform2()
        if self._parent_pilihan:
            self._parent_pilihan.show()
        else:
            self._fallback = Pilihan()
            self._fallback.show()
        self.close()


# ─────────────────────────────────────────────
#  DAFTAR MENU
# ─────────────────────────────────────────────
class DftrMenu(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("DaftarMenu.ui", self)
        self.center()
        self._simpan_mode = 'baru'   # tambahkan
        self._edit_mode = 'view'     # tambahkan
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

    def loaddata(self):
        conn = get_connection()
        curr = conn.cursor()
        curr.execute("SELECT idMenu, kategori, namaMenu, harga, stock FROM tbbarang ORDER BY harga DESC")
        result = curr.fetchall()
        curr.close()
        conn.close()
        self.tableWidget.setRowCount(len(result))
        for row, item in enumerate(result):
            self.tableWidget.setItem(row, 0, QtWidgets.QTableWidgetItem(str(item[0])))
            self.tableWidget.setItem(row, 1, QtWidgets.QTableWidgetItem(str(item[1])))
            self.tableWidget.setItem(row, 2, QtWidgets.QTableWidgetItem(str(item[2])))
            self.tableWidget.setItem(row, 3, QtWidgets.QTableWidgetItem(str(item[3])))
            if self.tableWidget.columnCount() > 4:
                self.tableWidget.setItem(row, 4, QtWidgets.QTableWidgetItem(str(item[4])))

    def clearform(self):
        self.textIdMenu.setFocus()
        self.textIdMenu.clear()
        self.cbKategori.setCurrentText('')
        self.textMenu.clear()
        self.textHarga.clear()
        if hasattr(self, 'textStock'):
            self.textStock.clear()

    def activeText(self, enable):
        self.textIdMenu.setEnabled(enable)
        self.cbKategori.setEnabled(enable)
        self.textMenu.setEnabled(enable)
        self.textHarga.setEnabled(enable)
        if hasattr(self, 'textStock'):
            self.textStock.setEnabled(enable)

    def getitem(self):
        row = self.tableWidget.currentRow()
        if row < 0:
            return
        id_item = self.tableWidget.item(row, 0)
        if id_item is None:
            return
        self.textIdMenu.setText(id_item.text())
        self.cbKategori.setCurrentText(self.tableWidget.item(row, 1).text())
        self.textMenu.setText(self.tableWidget.item(row, 2).text())
        self.textHarga.setText(self.tableWidget.item(row, 3).text())
        if hasattr(self, 'textStock') and self.tableWidget.item(row, 4):
            self.textStock.setText(self.tableWidget.item(row, 4).text())

    def edittext(self):
        if self._edit_mode == 'view':
            self.activeText(True)
            self.clearform()
            self.edit.setText('💾  Simpan')
            self._edit_mode = 'save'
        elif self._edit_mode == 'save':
            idMenu = self.textIdMenu.text()
            if len(idMenu) > 10:
                QMessageBox.warning(self, "Input Error", "ID menu tidak boleh lebih dari 10 karakter.")
                return
            stock_text = self.textStock.text().strip() if hasattr(self, 'textStock') else '0'
            try:
                stock_val = int(float(stock_text)) if stock_text else 0
            except ValueError:
                QMessageBox.warning(self, "Input Error", "Stock harus berupa angka.")
                return
            conn = get_connection()
            curr = conn.cursor()
            tipeMenu = self.cbKategori.currentText()
            namaMenu = self.textMenu.text()
            hargaa   = self.textHarga.text()
            try:
                curr.execute(
                    "UPDATE tbbarang SET kategori=%s, namaMenu=%s, harga=%s, stock=%s WHERE idMenu=%s",
                    (tipeMenu, namaMenu, hargaa, stock_val, idMenu),
                )
                conn.commit()
            except mysql.connector.DataError as e:
                QMessageBox.critical(self, "Database Error", f"Gagal update data: {e}")
            finally:
                curr.close()
                conn.close()
            self.loaddata()
            self.activeText(False)
            self.clearform()
            self.edit.setText('✏  Edit')
            self._edit_mode = 'view'

    def hapusData(self):
        idMenu = self.textIdMenu.text()
        if not idMenu:
            QMessageBox.warning(self, "Perhatian", "Pilih item yang ingin dihapus!")
            return
        conn = get_connection()
        curr = conn.cursor()
        curr.execute("DELETE FROM tbbarang WHERE idMenu=%s", (idMenu,))
        conn.commit()
        curr.close()
        conn.close()
        self.loaddata()

    def batals(self):
        if self._simpan_mode == 'save':
            self.simpan.setText('＋  Baru')
            self._simpan_mode = 'baru'
            self.clearform()
            self.activeText(False)
        elif self._edit_mode == 'save':
            self.edit.setText('✏  Edit')
            self._edit_mode = 'view'
            self.clearform()
            self.activeText(False)

    def generate_next_id(self):
        """Ambil ID terakhir dari DB, lalu buat ID berikutnya.
        Mendukung format seperti 'M001', 'MK01', atau angka murni '001'."""
        import re
        conn = get_connection()
        curr = conn.cursor()
        curr.execute("SELECT idMenu FROM tbbarang")
        rows = curr.fetchall()
        curr.close()
        conn.close()

        max_num = 0
        prefix  = ''
        width   = 3   # default lebar angka, misal 001, 002, dst

        for (idm,) in rows:
            idm = str(idm)
            m = re.match(r'^([A-Za-z]*)(\d+)$', idm)
            if m:
                p, num = m.group(1), m.group(2)
                n = int(num)
                if n > max_num:
                    max_num = n
                    prefix  = p
                    width   = len(num)

        next_num = max_num + 1
        new_id   = f"{prefix}{next_num:0{width}d}"

        # Jaga-jaga kalau kolom idMenu maksimal 5 karakter
        if len(new_id) > 5:
            new_id = new_id[-5:]

        return new_id

    def simpandata(self):
        if self._simpan_mode == 'baru':
            self.activeText(True)
            self.clearform()
            self.textIdMenu.setText(self.generate_next_id())   # <-- auto generate di sini
            self.simpan.setText('💾  Simpan')
            self._simpan_mode = 'save'
        elif self._simpan_mode == 'save':
            idMenu = self.textIdMenu.text()
            if not idMenu:
                QMessageBox.warning(self, "Perhatian", "ID Menu gagal dibuat, coba lagi!")
                return
            if not self.textMenu.text().strip():
                QMessageBox.warning(self, "Perhatian", "Nama menu tidak boleh kosong!")
                return
            if not self.textHarga.text().strip():
                QMessageBox.warning(self, "Perhatian", "Harga tidak boleh kosong!")
                return

            stock_text = self.textStock.text().strip() if hasattr(self, 'textStock') else '0'
            try:
                stock_val = int(float(stock_text)) if stock_text else 0
            except ValueError:
                QMessageBox.warning(self, "Perhatian", "Stock harus berupa angka!")
                return

            tipeMenu = self.cbKategori.currentText()
            namaMenu = self.textMenu.text()
            hargaa   = self.textHarga.text()
            try:
                conn = get_connection()
                curr = conn.cursor()
                curr.execute(
                    "INSERT INTO tbbarang (idMenu, kategori, namaMenu, harga, stock) VALUES (%s, %s, %s, %s, %s)",
                    (idMenu, tipeMenu, namaMenu, hargaa, stock_val)
                )
                conn.commit()
            except mysql.connector.DataError as e:
                QMessageBox.critical(self, "Database Error", f"Gagal simpan data: {e}")
                return
            except mysql.connector.IntegrityError:
                # Kalau ID bentrok (race condition), coba generate ulang sekali
                QMessageBox.warning(self, "Perhatian", "ID sudah dipakai, mencoba ID baru...")
                self.textIdMenu.setText(self.generate_next_id())
                return
            finally:
                try:
                    curr.close()
                    conn.close()
                except Exception:
                    pass

            self.loaddata()
            self.activeText(False)
            self.clearform()
            self.simpan.setText('＋  Baru')
            self._simpan_mode = 'baru'

    def kembali(self):
        self.openkasir = Pilihan()
        self.openkasir.show()
        self.close()


# ─────────────────────────────────────────────
#  LAPORAN
# ─────────────────────────────────────────────
class Laporan(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("Data.ui", self)
        self.center()
        self._buat_filter_tanggal()
        self.tombol()
        self.loaddata2()
        self.tabelWidtg()
        self.tot()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def _buat_filter_tanggal(self):
        """Tambahkan kontrol filter tanggal secara dinamis (tidak perlu edit Data.ui).
        Jika Data.ui punya QVBoxLayout/QHBoxLayout utama, filter disisipkan di atas.
        Kalau tidak ada layout (widget diposisikan manual), filter ditempel di
        pojok kiri atas dengan geometry tetap — silakan geser di Qt Designer bila perlu."""
        self.dateDari = QDateEdit(self)
        self.dateDari.setCalendarPopup(True)
        self.dateDari.setDate(QDate.currentDate().addMonths(-1))

        self.dateSampai = QDateEdit(self)
        self.dateSampai.setCalendarPopup(True)
        self.dateSampai.setDate(QDate.currentDate())

        self.btnFilter = QPushButton("🔍  Filter", self)
        self.btnReset = QPushButton("↩  Reset", self)

        style_datepicker = """
            QDateEdit {
                background-color: #1e2538; border: 1.5px solid #2d3548;
                border-radius: 8px; padding: 6px 10px; color: #f1f5f9;
            }
            QPushButton {
                background-color: #1e40af; color: #e0f2fe; border: none;
                border-radius: 8px; padding: 6px 14px; font-weight: 600;
            }
            QPushButton:hover { background-color: #2563eb; }
        """
        for w in (self.dateDari, self.dateSampai, self.btnFilter, self.btnReset):
            w.setStyleSheet(style_datepicker)

        existing_layout = self.layout()
        if existing_layout is not None:
            baris_filter = QHBoxLayout()
            baris_filter.addWidget(QLabel("Dari:"))
            baris_filter.addWidget(self.dateDari)
            baris_filter.addWidget(QLabel("Sampai:"))
            baris_filter.addWidget(self.dateSampai)
            baris_filter.addWidget(self.btnFilter)
            baris_filter.addWidget(self.btnReset)
            baris_filter.addStretch()
            existing_layout.insertLayout(0, baris_filter)
        else:
            # Tidak ada layout utama -> posisikan manual di pojok kiri atas
            lbl_dari = QLabel("Dari:", self)
            lbl_dari.setGeometry(20, 16, 40, 24)
            self.dateDari.setGeometry(60, 12, 130, 30)

            lbl_sampai = QLabel("Sampai:", self)
            lbl_sampai.setGeometry(200, 16, 50, 24)
            self.dateSampai.setGeometry(255, 12, 130, 30)

            self.btnFilter.setGeometry(395, 12, 90, 30)
            self.btnReset.setGeometry(490, 12, 90, 30)

            lbl_dari.show()
            lbl_sampai.show()

        self.dateDari.show()
        self.dateSampai.show()
        self.btnFilter.show()
        self.btnReset.show()

        self.btnFilter.clicked.connect(self.terapkan_filter)
        self.btnReset.clicked.connect(self.reset_filter)

    def tabelWidtg(self):
        header = self.tableWidget_2.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

    def tombol(self):
        self.keluar.clicked.connect(self.kembali)

    def terapkan_filter(self):
        dari    = self.dateDari.date().toString("yyyy-MM-dd") + " 00:00:00"
        sampai  = self.dateSampai.date().toString("yyyy-MM-dd") + " 23:59:59"
        self.loaddata2(dari, sampai)
        self.tot(dari, sampai)

    def reset_filter(self):
        self.dateDari.setDate(QDate.currentDate().addMonths(-1))
        self.dateSampai.setDate(QDate.currentDate())
        self.loaddata2()
        self.tot()

    def loaddata2(self, dari=None, sampai=None):
        conn = get_connection()
        curr = conn.cursor()
        if dari and sampai:
            curr.execute(
                "SELECT * FROM laporan WHERE tanggal BETWEEN %s AND %s ORDER BY tanggal DESC",
                (dari, sampai)
            )
        else:
            curr.execute("SELECT * FROM laporan ORDER BY tanggal DESC")
        result = curr.fetchall()
        col_names = [desc[0].lower() for desc in curr.description]
        curr.close()
        conn.close()

        idx_tanggal = col_names.index('tanggal') if 'tanggal' in col_names else None

        self.tableWidget_2.setRowCount(len(result))
        for row, item in enumerate(result):
            self.tableWidget_2.setItem(row, 0, QtWidgets.QTableWidgetItem(str(item[1])))
            self.tableWidget_2.setItem(row, 1, QtWidgets.QTableWidgetItem(str(item[2])))
            self.tableWidget_2.setItem(row, 2, QtWidgets.QTableWidgetItem(str(item[3])))
            if idx_tanggal is not None and self.tableWidget_2.columnCount() > 3:
                waktu = item[idx_tanggal]
                waktu_str = waktu.strftime("%d-%m-%Y %H:%M") if hasattr(waktu, 'strftime') else str(waktu)
                self.tableWidget_2.setItem(row, 3, QtWidgets.QTableWidgetItem(waktu_str))

    def tot(self, dari=None, sampai=None):
        tota = 0
        conn = get_connection()
        curr = conn.cursor()
        if dari and sampai:
            curr.execute("SELECT total FROM laporan WHERE tanggal BETWEEN %s AND %s", (dari, sampai))
        else:
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


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = login()
    window.show()
    sys.exit(app.exec_())
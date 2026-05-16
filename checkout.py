from PyQt5.QtWidgets import (QApplication, QDialog, QTableWidget, QMessageBox,
                             QHeaderView, QDesktopWidget, QInputDialog)
from PyQt5 import QtWidgets, uic, QtGui
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtGui import QPainter, QFont, QFontMetrics
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout,
                             QLabel, QSpinBox, QPushButton)
# from PyQt5.QtCore import Qt
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

class EditJumlahDialog(QDialog):
    def __init__(self, nama_item, jml_lama, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Jumlah")
        self.setFixedWidth(340)
        self.setModal(True)
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

        # ── Spin row ──
        self.spin = QSpinBox()
        self.spin.setRange(1, 999)
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

        # ── Button row ──
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
        layout.addSpacing(8)
        layout.addLayout(btn_row)

    def get_value(self):
        return self.spin.value()


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

        # Simpan semua data menu untuk keperluan filter pencarian
        self._all_makanan = []
        self._all_minuman = []

        # Koneksi sinyal — dua tabel menu terpisah
        self.table_makanan.clicked.connect(lambda: self.getitem(self.table_makanan))
        self.table_minuman.clicked.connect(lambda: self.getitem(self.table_minuman))

        self.simpan.clicked.connect(self.simpandat)
        self.bayar.clicked.connect(self.bayarr)
        self.keluar.clicked.connect(self.keluars)
        self.hapus.clicked.connect(self.hapuss)
        self.batal.clicked.connect(self.batals)
        self.edit_item.clicked.connect(self.edit_keranjang)

        # ── Fitur Pencarian ──
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
        self.jumlah.clear()          # FIX 1: clear() bukan setText('0') agar konsisten

    def clearform2(self):
        self.totalbayar.clear()
        self.uangpembayaran.clear()
        self.table_2.clearContents()
        self.table_2.setRowCount(0)
        self.kembalian.clear()
        self.pemesan.clear()
        self.jumlah2.clear()

    # ─────────────────────────────────────────────
    #  LOAD DATA — FIX 2: deteksi urutan kolom otomatis
    # ─────────────────────────────────────────────
    def loaddata(self):
        """
        Load data dari DB. Karena urutan kolom tabel tbbarang bisa berbeda-beda
        di tiap instalasi, kita baca nama kolom dulu lalu petakan secara eksplisit.
        Asumsi nama kolom: id / kode, nama / menu, kategori, harga / price
        Jika struktur tabel Anda berbeda, sesuaikan nama kolom di bagian _col_index.
        """
        try:
            conn = get_connection()
            curr = conn.cursor()
            curr.execute("SELECT * FROM tbbarang")
            rows = curr.fetchall()

            # Ambil nama kolom dari cursor
            col_names = [desc[0].lower() for desc in curr.description]
            curr.close()
            conn.close()

            print(f"[DEBUG] Kolom tbbarang: {col_names}")
            print(f"[DEBUG] Contoh baris pertama: {rows[0] if rows else 'kosong'}")

            # Tentukan index tiap kolom secara fleksibel
            def _col_index(candidates):
                for c in candidates:
                    if c in col_names:
                        return col_names.index(c)
                return None

            idx_id       = _col_index(['id', 'kode', 'kd_barang', 'kd'])
            idx_kategori = _col_index(['kategori', 'category', 'jenis', 'tipe'])
            idx_nama     = _col_index(['nama', 'nama_barang', 'menu', 'nama_menu', 'item'])
            idx_harga    = _col_index(['harga', 'price', 'harga_jual', 'harga_barang'])

            # Fallback: jika nama kolom tidak dikenali, pakai posisi default
            if None in (idx_id, idx_kategori, idx_nama, idx_harga):
                print("[WARNING] Nama kolom tidak dikenali, pakai posisi default 0,1,2,3")
                idx_id, idx_kategori, idx_nama, idx_harga = 0, 1, 2, 3

            # Bangun list internal: (id, kategori, nama, harga)
            processed = []
            for r in rows:
                try:
                    processed.append((
                        str(r[idx_id]),
                        str(r[idx_kategori]),
                        str(r[idx_nama]),
                        float(r[idx_harga])
                    ))
                except Exception as e:
                    print(f"[WARNING] Baris dilewati: {r} — {e}")

            # Pisahkan makanan & minuman (case-insensitive)
            self._all_makanan = [r for r in processed if 'makanan' in r[1].lower()]
            self._all_minuman = [r for r in processed if 'minuman' in r[1].lower()]

            print(f"[DEBUG] Makanan: {len(self._all_makanan)} item, Minuman: {len(self._all_minuman)} item")

            self.filter_makanan("")
            self.filter_minuman("")

        except Exception as e:
            QMessageBox.critical(self, "Error DB", f"Gagal memuat data menu:\n{e}")
            print(f"[ERROR] loaddata: {e}")

    # ─────────────────────────────────────────────
    #  FITUR PENCARIAN MENU
    # ─────────────────────────────────────────────
    def filter_makanan(self, text):
        keyword = text.strip().lower()
        filtered = (
            [r for r in self._all_makanan if keyword in r[2].lower() or keyword in r[1].lower()]
            if keyword else self._all_makanan
        )
        self.table_makanan.setRowCount(len(filtered))
        for i, item in enumerate(filtered):
            self.table_makanan.setItem(i, 0, QtWidgets.QTableWidgetItem(item[0]))           # ID
            self.table_makanan.setItem(i, 1, QtWidgets.QTableWidgetItem(item[1]))           # Kategori
            self.table_makanan.setItem(i, 2, QtWidgets.QTableWidgetItem(item[2]))           # Nama
            self.table_makanan.setItem(i, 3, QtWidgets.QTableWidgetItem(f"{item[3]:.0f}"))  # Harga

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

    # ─────────────────────────────────────────────
    #  GETITEM — FIX 3: kolom Nama ada di kolom 2, bukan 1
    # ─────────────────────────────────────────────
    def getitem(self, table):
        row = table.currentRow()
        if row < 0:
            return

        # Tabel menu: kolom 0=ID, 1=Kategori, 2=Nama, 3=Harga
        id_item  = table.item(row, 0).text()   # noqa — tidak dipakai di form tapi berguna untuk debug
        kategori = table.item(row, 1).text()   # Kategori → field kategori
        nama     = table.item(row, 2).text()   # Nama     → field pilihanmenu
        harga    = table.item(row, 3).text()   # Harga    → field harga

        self.kategori.setText(kategori)
        self.pilihanmenu.setText(nama)
        self.harga.setText(harga)
        self.jumlah.setText("1")               # FIX 3b: isi default 1 agar user tidak lupa mengisi
        self.jumlah.setFocus()
        self.jumlah.selectAll()

    # ─────────────────────────────────────────────
    #  SIMPAN KE KERANJANG — FIX 4: validasi jumlah kosong
    # ─────────────────────────────────────────────
    def simpandat(self):
        kategori = self.kategori.text().strip()
        menu     = self.pilihanmenu.text().strip()
        harga    = self.harga.text().strip()
        jumlah   = self.jumlah.text().strip()

        # FIX 4a: validasi field wajib
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

        # FIX 4b: jumlah harus > 0
        if nilai_jumlah <= 0:
            QMessageBox.warning(self, "Perhatian", "Jumlah harus lebih dari 0!")
            return

        # Cek apakah menu sudah ada di keranjang → tambah jumlah saja
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

        # Tambah baris baru ke keranjang
        row    = self.table_2.rowCount()
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
    #  FITUR EDIT KERANJANG
    # ─────────────────────────────────────────────
    def edit_keranjang(self):
        row = self.table_2.currentRow()
        if row == -1:
            QMessageBox.information(self, "Info", "Pilih item di keranjang yang ingin diedit!")
            return

        nama_item  = self.table_2.item(row, 1).text()
        harga_item = float(self.table_2.item(row, 2).text())
        jml_lama   = int(float(self.table_2.item(row, 3).text()))

        dialog = EditJumlahDialog(nama_item, jml_lama, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            jumlah_baru   = dialog.get_value()
            subtotal_baru = jumlah_baru * harga_item
            self.table_2.setItem(row, 3, QtWidgets.QTableWidgetItem(f"{jumlah_baru:.0f}"))
            self.table_2.setItem(row, 4, QtWidgets.QTableWidgetItem(f"{subtotal_baru:.0f}"))
            self.jum()
            self.tot()

        # if ok:
        #     subtotal_baru = jumlah_baru * harga_item
        #     self.table_2.setItem(row, 3, QtWidgets.QTableWidgetItem(f"{jumlah_baru:.0f}"))
        #     self.table_2.setItem(row, 4, QtWidgets.QTableWidgetItem(f"{subtotal_baru:.0f}"))
        #     self.jum()
        #     self.tot()

    # ─────────────────────────────────────────────
    #  PEMBAYARAN
    # ─────────────────────────────────────────────
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
            try:
                conn = get_connection()
                curr = conn.cursor()
                curr.execute(
                    "INSERT INTO laporan (nama, jumlah, total) VALUES (%s, %s, %s)",
                    (namapembeli, self.jumlah2.text(), total_text)
                )
                conn.commit()
                curr.close()
                conn.close()
            except Exception as e:
                QMessageBox.critical(self, "Error DB", f"Gagal menyimpan laporan:\n{e}")
                return
            QMessageBox.information(self, "Sukses", "✅ Pembayaran Berhasil!")
            self.cetak_struk()
        else:
            kekurangan = total - payment
            self.kembalian.setText("Uang Kurang")
            QMessageBox.warning(self, "Pembayaran Gagal",
                                f"Uang kurang Rp {kekurangan:,.0f}")

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
        draw_center("Selamat Makan!",                 make_font(8),            y)

        painter.end()

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
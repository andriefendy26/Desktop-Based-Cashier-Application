from PyQt5.QtWidgets import (QApplication, QDialog, QTableWidget, QMessageBox,
                             QHeaderView, QDesktopWidget, QInputDialog)
from PyQt5 import QtWidgets, uic, QtGui
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtGui import QPainter, QFont, QFontMetrics
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout,
                             QLabel, QSpinBox, QPushButton, QDateEdit)
import sys
import re
from datetime import datetime, time
import mysql.connector
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter

# ── Palet chart (tema terang, senada halaman laporan) ──
CHART_BG    = '#ffffff'
CHART_TEXT  = '#64748b'
CHART_TITLE = '#1e3a8a'
CHART_GRID  = '#e5edfb'
CHART_AXIS  = '#bfdbfe'
CHART_COLOR = {'Harian': '#3b82f6', 'Mingguan': '#38bdf8', 'Tahunan': '#818cf8'}


# ─────────────────────────────────────────────
#  FORMAT MATA UANG (Rupiah / format Indonesia)
# ─────────────────────────────────────────────
def fmt_rp(value, prefix="Rp "):
    """1500000 -> 'Rp 1.500.000' (pemisah ribuan titik, gaya Indonesia)."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return str(value)
    return f"{prefix}{v:,.0f}".replace(",", ".")


def fmt_ribuan(value):
    """1500000 -> '1.500.000' (tanpa prefix Rp)."""
    return fmt_rp(value, prefix="")


def parse_angka(text, default=0.0):
    """Kebalikan fmt_rp: 'Rp 1.500.000' -> 1500000.0
    Aman dipakai untuk teks yang sudah maupun belum terformat."""
    if text is None:
        return default
    if isinstance(text, (int, float)):
        return float(text)
    s = re.sub(r'[^\d\-]', '', str(text))
    if s in ('', '-'):
        return default
    try:
        return float(s)
    except ValueError:
        return default


def item_rp(value):
    """QTableWidgetItem berisi nominal terformat, rata kanan."""
    it = QtWidgets.QTableWidgetItem(fmt_rp(value))
    it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
    return it


def _fmt_singkat(v, _pos=None):
    """1.500.000 -> 1.5jt, supaya label sumbu Y tidak memenuhi chart."""
    if v >= 1_000_000_000: return f"{v/1_000_000_000:g}M"
    if v >= 1_000_000:     return f"{v/1_000_000:g}jt"
    if v >= 1_000:         return f"{v/1_000:g}rb"
    return f"{v:g}"


def pasang_format_uang(line_edit):
    """Buat QLineEdit otomatis menampilkan pemisah ribuan saat diketik.
    Nilai aslinya diambil kembali dengan parse_angka(line_edit.text())."""
    def _on_text_changed(text):
        digits = re.sub(r'\D', '', text)
        baru = f"{int(digits):,}".replace(",", ".") if digits else ""
        if baru != text:
            line_edit.blockSignals(True)
            line_edit.setText(baru)
            line_edit.blockSignals(False)
            line_edit.setCursorPosition(len(baru))

    line_edit.textChanged.connect(_on_text_changed)
    line_edit.setAlignment(Qt.AlignRight | Qt.AlignVCenter)


def _setup_responsive_scaling(window, content, base_width, base_height):
    """Capture the fixed UI geometry so it can scale with the dialog.

    CATATAN PENTING:
    Widget yang dibuat lewat kode (bukan dari .ui) WAJIB diberi setObjectName(),
    karena filter di bawah melewati widget tanpa objectName.
    """
    nodes = {content: (content, content.geometry())}
    for child in content.findChildren(QtWidgets.QWidget):
        if child.objectName() and not child.objectName().startswith('qt_'):
            nodes[child] = (child, child.geometry())
    window._responsive_content = content
    window._responsive_base_size = (base_width, base_height)
    window._responsive_nodes = nodes
    _apply_responsive_scaling(window)


def _apply_responsive_scaling(window):
    content = getattr(window, '_responsive_content', None)
    nodes = getattr(window, '_responsive_nodes', None)
    if content is None or nodes is None:
        return

    base_width, base_height = window._responsive_base_size
    scale = min(window.width() / base_width, window.height() / base_height)
    scale = max(scale, 0.25)
    window._responsive_scale = scale  # dipakai oleh _apply_custom_label_fonts
    content_width = max(1, round(base_width * scale))
    content_height = max(1, round(base_height * scale))
    content_x = max(0, (window.width() - content_width) // 2)
    content_y = max(0, (window.height() - content_height) // 2)

    content.setGeometry(content_x, content_y, content_width, content_height)
    ordered_nodes = sorted(
        (entry for widget, entry in nodes.items() if widget is not content),
        key=lambda entry: entry[0].parentWidget().objectName().count('_')
    )
    for widget, geometry in ordered_nodes:
        widget.setGeometry(
            round(geometry.x() * scale),
            round(geometry.y() * scale),
            max(1, round(geometry.width() * scale)),
            max(1, round(geometry.height() * scale)),
        )


def _apply_custom_label_fonts(window):
    """Skalakan ukuran font label judul tertentu (mis. 'Daftar Menu', 'Makanan',
    'Minuman', 'Keranjang Belanja') mengikuti faktor scale window, tanpa
    mengubah label lain. base_px adalah ukuran dasar sedikit lebih besar
    dari bawaan .ui, lalu ikut mengecil/membesar saat window di-resize."""
    fonts = getattr(window, '_custom_label_fonts', None)
    if not fonts:
        return
    scale = getattr(window, '_responsive_scale', 1.0)
    for widget, (base_px, color) in fonts.items():
        size = max(9, round(base_px * scale))
        widget.setStyleSheet(
            f"QLabel {{ color: {color}; font-size: {size}px; "
            f"font-weight: 700; background: transparent; }}"
        )


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
#  SELECT DATE EDIT  (VERSI PERBAIKAN)
#  Ganti seluruh class SelectDateEdit yang lama di kasir.py dengan ini.
# ─────────────────────────────────────────────
class SelectDateEdit(QDateEdit):
    """QDateEdit yang berperilaku seperti tombol select/combobox:
    klik di area mana pun langsung membuka kalender, teks tidak bisa diketik manual.

    CATATAN PERBAIKAN (kenapa versi lama tidak berfungsi):
    Versi sebelumnya menebak posisi tombol panah dropdown lewat
    style().subControlRect(CC_ComboBox / CC_SpinBox, ...) lalu mengirim
    "klik palsu" ke posisi tersebut. Pendekatan ini rapuh:
      1. Karena calendarPopup=True, tombol spin bawaan (SC_SpinBoxUp)
         disembunyikan Qt, jadi query CC_SpinBox selalu mengembalikan
         rect KOSONG -> fallback-nya tidak pernah berguna.
      2. QStyleOptionComboBox yang dibuat manual (initFrom + set field
         seadanya) sering tidak cocok dengan geometri yang benar-benar
         dipakai style/stylesheet aktif, terutama dengan QSS custom
         seperti punya kita -> rect yang didapat salah/ tidak valid.
    Akibatnya kedua rect tidak valid, klik jatuh ke super().mousePressEvent()
    dengan event asli, dan karena field readOnly, tidak terjadi apa-apa
    -> kalender tidak pernah muncul.

    SOLUSI: kelola sendiri popup kalendernya, tidak bergantung sama sekali
    pada hit-testing internal Qt. Setiap klik kiri langsung membuka
    QCalendarWidget kita sendiri di dalam frame Qt.Popup, diposisikan
    tepat di bawah field. Ini selalu berfungsi apa pun style/tema aktif.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCalendarPopup(True)   # tetap True supaya QSS ::drop-down / ::down-arrow tampil
        self.setReadOnly(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.setFocusPolicy(Qt.StrongFocus)

        # ── Popup kalender kita sendiri (tidak pakai mekanisme dropdown bawaan) ──
        self._popup = QtWidgets.QFrame(self, Qt.Popup)
        self._popup.setObjectName("calendarPopupFrame")
        self._popup.setStyleSheet(
            "QFrame#calendarPopupFrame { background-color: #ffffff; "
            "border: 1px solid #bfdbfe; border-radius: 10px; }"
        )
        popup_layout = QVBoxLayout(self._popup)
        popup_layout.setContentsMargins(6, 6, 6, 6)

        self._calendar = QtWidgets.QCalendarWidget(self._popup)
        self._calendar.setGridVisible(True)
        self._calendar.setVerticalHeaderFormat(QtWidgets.QCalendarWidget.NoVerticalHeader)
        self._calendar.clicked.connect(self._pilih_tanggal)
        popup_layout.addWidget(self._calendar)

    def _pilih_tanggal(self, date):
        self.setDate(date)
        self._popup.hide()
        self.dateChanged.emit(date)  # jaga-jaga kalau ada listener lain yang dengar sinyal ini

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setFocus()
            self._toggle_popup()
            event.accept()
            return
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        # Supaya bisa dibuka juga lewat keyboard (Enter/Space) saat sedang focus
        if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self._toggle_popup()
            return
        super().keyPressEvent(event)

    def _toggle_popup(self):
        if self._popup.isVisible():
            self._popup.hide()
            return
        self._calendar.setSelectedDate(self.date())
        pos = self.mapToGlobal(self.rect().bottomLeft())
        self._popup.move(pos)
        self._popup.resize(max(self.width(), 260), 260)
        self._popup.show()
        self._popup.raise_()
        self._popup.activateWindow()

STYLE_SELECT_DATE = """
QDateEdit {
    background-color: #f0f6ff;
    border: 1.5px solid #bfdbfe;
    border-radius: 8px;
    padding: 4px 10px;
    color: #1e293b;
    font-size: 13px;
}
QDateEdit:hover { border-color: #60a5fa; background-color: #ffffff; }
QDateEdit:focus, QDateEdit:on { border-color: #2563eb; background-color: #ffffff; }
QDateEdit::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: center right;
    border: none;
    width: 28px;
}
QDateEdit::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #2563eb;
    margin-right: 8px;
}
QCalendarWidget QWidget { background-color: #ffffff; }
QCalendarWidget QAbstractItemView:enabled {
    background-color: #ffffff;
    color: #1e293b;
    selection-background-color: #dbeafe;
    selection-color: #1e3a8a;
    outline: none;
}
QCalendarWidget QToolButton {
    background-color: #eff6ff;
    color: #1d4ed8;
    border: none;
    border-radius: 6px;
    padding: 4px 10px;
    font-weight: 600;
}
QCalendarWidget QToolButton:hover { background-color: #dbeafe; }
QCalendarWidget QMenu { background-color: #ffffff; color: #1e293b; }
QCalendarWidget QSpinBox {
    background-color: #ffffff;
    border: 1px solid #bfdbfe;
    border-radius: 4px;
    color: #1e293b;
}
"""


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
                background-color: #eef3fa;
                border: 1px solid #e0e7f2;
                border-radius: 14px;
            }
            QLabel#lbl_title {
                color: #14306b;
                font-size: 15px;
                font-weight: 700;
                background: transparent;
            }
            QLabel#lbl_sub {
                color: #6b7a90;
                font-size: 12px;
                background: transparent;
            }
            QLabel#lbl_field {
                color: #6b7a90;
                font-size: 12px;
                background: transparent;
            }
            QSpinBox {
                background-color: #ffffff;
                border: 1.5px solid #2563eb;
                border-radius: 8px;
                color: #1e293b;
                font-size: 18px;
                font-weight: 700;
                padding: 6px 10px;
                min-height: 38px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 0; border: none;
            }
            QPushButton#btn_minus, QPushButton#btn_plus {
                background-color: #f5f8fd;
                border: 1px solid #d5e0ef;
                border-radius: 8px;
                color: #2563eb;
                font-size: 20px;
                font-weight: 700;
                min-width: 38px;
                min-height: 38px;
                padding: 0;
            }
            QPushButton#btn_minus:hover, QPushButton#btn_plus:hover {
                background-color: #e7effb;
                border-color: #2563eb;
            }
            QPushButton#btn_minus:pressed, QPushButton#btn_plus:pressed {
                background-color: #d8e5f8;
            }
            QPushButton#btn_ok {
                background-color: #2563eb;
                border: none;
                border-radius: 8px;
                color: #ffffff;
                font-size: 13px;
                font-weight: 700;
                padding: 9px 0;
                min-height: 38px;
            }
            QPushButton#btn_ok:hover   { background-color: #1d4ed8; }
            QPushButton#btn_ok:pressed { background-color: #1b3fae; }
            QPushButton#btn_batal {
                background-color: #f4f6f9;
                border: 1px solid #dfe5ec;
                border-radius: 8px;
                color: #475569;
                font-size: 13px;
                font-weight: 600;
                padding: 9px 0;
                min-height: 38px;
            }
            QPushButton#btn_batal:hover { background-color: #e9edf3; color: #1e293b; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 20)
        layout.setSpacing(8)

        lbl_title = QLabel("✏  Edit Jumlah")
        lbl_title.setObjectName("lbl_title")

        lbl_sub = QLabel(f"Item: <b style='color:#14306b'>{nama_item}</b>")
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
        self.setWindowFlags(
            Qt.Window |
            Qt.WindowMinimizeButtonHint |
            Qt.WindowMaximizeButtonHint |
            Qt.WindowCloseButtonHint
        )
        self.center()
        self.masuk.clicked.connect(self.loginfungsion)
        self.toggle_password.clicked.connect(self.toggle_password_visibility)

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def loginfungsion(self):
        username = self.emailfield.text().strip()
        password = self.passwordfield.text()
        self.error.clear()

        if not username:
            self.error.setText("Username wajib diisi")
            self.emailfield.setFocus()
            return
        if not password:
            self.error.setText("Password wajib diisi")
            self.passwordfield.setFocus()
            return

        conn = get_connection()
        curr = conn.cursor()
        curr.execute("SELECT pass FROM auth WHERE username=%s", (username,))
        user = curr.fetchone()
        curr.close()
        conn.close()

        if user is None:
            self.error.setText("Username tidak ditemukan")
        elif user[0] != password:
            self.error.setText("Password salah")
            self.passwordfield.selectAll()
            self.passwordfield.setFocus()
        else:
            self.masukkasir()
            QMessageBox.information(self, 'Alert', 'Login berhasil')

    def toggle_password_visibility(self):
        if self.passwordfield.echoMode() == QtWidgets.QLineEdit.Password:
            self.passwordfield.setEchoMode(QtWidgets.QLineEdit.Normal)
            self.toggle_password.setText("Hide")
            self.toggle_password.setToolTip("Sembunyikan password")
        else:
            self.passwordfield.setEchoMode(QtWidgets.QLineEdit.Password)
            self.toggle_password.setText("Show")
            self.toggle_password.setToolTip("Tampilkan password")

    def masukkasir(self):
        self.openkasir = Pilihan()
        self.openkasir.show()
        self.close()


# ─────────────────────────────────────────────
#  PILIHAN — Checkout, Daftar Menu, Laporan
# ─────────────────────────────────────────────
class Pilihan(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("Pilihan.ui", self)
        self.setWindowFlags(
            Qt.Window |
            Qt.WindowMinimizeButtonHint |
            Qt.WindowMaximizeButtonHint |
            Qt.WindowCloseButtonHint
        )
        self.setMinimumSize(480, 640)
        self.center()
        self.tombol()
        self._resize_content()
        self.showMaximized()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._resize_content()

    def _resize_content(self):
        """Keep the dashboard content centered and widen it with the window."""
        if not hasattr(self, 'widget') or not hasattr(self, 'card'):
            return

        window_width = self.width()
        window_height = self.height()
        card_width = min(max(window_width - 56, 424), 720)
        card_height = min(max(window_height - 56, 584), 680)
        card_x = (window_width - card_width) // 2
        card_y = (window_height - card_height) // 2

        self.widget.setGeometry(0, 0, window_width, window_height)
        self.card.setGeometry(card_x, card_y, card_width, card_height)

        content_width = card_width - 48
        for name in ('divider', 'divider2', 'divider3', 'divider4',
                     'Checkout', 'Menu', 'Lprn', 'logout'):
            control = getattr(self, name, None)
            if control is not None:
                control.setGeometry(24, control.y(), content_width, control.height())

        for name in ('label_title', 'label_sub'):
            label = getattr(self, name, None)
            if label is not None:
                label.setGeometry(20, label.y(), card_width - 40, label.height())

        self.label_icon.move((card_width - self.label_icon.width()) // 2, self.label_icon.y())

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def tombol(self):
        self.Checkout.clicked.connect(self.BukaCheckout)
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
        self.setWindowFlags(
            Qt.Window |
            Qt.WindowMinimizeButtonHint |
            Qt.WindowMaximizeButtonHint |
            Qt.WindowCloseButtonHint
        )
        uic.loadUi("CheckOut.ui", self)
        available = QDesktopWidget().availableGeometry()
        self.resize(min(1734, available.width()), min(859, available.height()))
        _setup_responsive_scaling(self, self.widget, 1741, 851)
        self.center()
        self.setWindowTitle("Check Out — Kasir")

        # ── Judul "Daftar Menu" / "Keranjang Belanja" sedikit lebih besar,
        # dan tetap menyesuaikan (mengecil/membesar) saat window di-resize.
        self._custom_label_fonts = {
            self.label_7:      (16, '#1d4ed8'),   # 📋 Daftar Menu
            self.label_6:      (16, '#1d4ed8'),   # 🛍 Keranjang Belanja
            self.lbl_makanan:  (14, '#eb2525'),   # 🍽 Makanan
            self.lbl_minuman:  (14, '#0891b2'),   # 🥤 Minuman
        }
        _apply_custom_label_fonts(self)

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

        # ── Format currency otomatis saat mengetik uang tunai pembayaran ──
        pasang_format_uang(self.uangpembayaran)
        self.uangpembayaran.setPlaceholderText("0")

        self.activeText(False)
        self.tableWidgt()
        self.loaddata()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        _apply_responsive_scaling(self)
        _apply_custom_label_fonts(self)

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    # ── Kolom menyesuaikan isi supaya teks tidak terpotong ──
    def _setup_table(self, table, stretch_col=None):
        h = table.horizontalHeader()
        h.setSectionResizeMode(QHeaderView.ResizeToContents)
        if stretch_col is not None and stretch_col < table.columnCount():
            h.setSectionResizeMode(stretch_col, QHeaderView.Stretch)
        h.setMinimumSectionSize(70)
        h.setStretchLastSection(False)

        table.setWordWrap(False)
        table.setTextElideMode(Qt.ElideNone)
        table.setHorizontalScrollMode(QTableWidget.ScrollPerPixel)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)

    def tableWidgt(self):
        self._setup_table(self.table_makanan, stretch_col=2)  # kolom Nama
        self._setup_table(self.table_minuman, stretch_col=2)  # kolom Nama
        self._setup_table(self.table_2,       stretch_col=1)  # kolom Nama (keranjang)

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

    def _isi_tabel_menu(self, table, filtered):
        table.setRowCount(len(filtered))
        for i, item in enumerate(filtered):
            table.setItem(i, 0, QtWidgets.QTableWidgetItem(item[0]))
            table.setItem(i, 1, QtWidgets.QTableWidgetItem(item[1]))
            table.setItem(i, 2, QtWidgets.QTableWidgetItem(item[2]))
            table.setItem(i, 3, item_rp(item[3]))                 # HARGA -> Rp 15.000
            if table.columnCount() > 4:
                stok = QtWidgets.QTableWidgetItem(f"{item[4]:.0f}")
                stok.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                table.setItem(i, 4, stok)

    def filter_makanan(self, text):
        keyword = text.strip().lower()
        filtered = (
            [r for r in self._all_makanan if keyword in r[2].lower() or keyword in r[1].lower()]
            if keyword else self._all_makanan
        )
        self._isi_tabel_menu(self.table_makanan, filtered)

    def filter_minuman(self, text):
        keyword = text.strip().lower()
        filtered = (
            [r for r in self._all_minuman if keyword in r[2].lower() or keyword in r[1].lower()]
            if keyword else self._all_minuman
        )
        self._isi_tabel_menu(self.table_minuman, filtered)

    def getitem(self, table):
        row = table.currentRow()
        if row < 0:
            return
        id_item  = table.item(row, 0).text()
        kategori = table.item(row, 1).text()
        nama     = table.item(row, 2).text()
        harga    = parse_angka(table.item(row, 3).text())

        # Ambil stock terkini dari sumber data (bukan dari tabel, supaya selalu akurat)
        sumber = self._all_makanan if 'makanan' in kategori.lower() else self._all_minuman
        stock = next((r[4] for r in sumber if r[0] == id_item), 0.0)

        self.kategori.setText(kategori)
        self.pilihanmenu.setText(nama)
        self.harga.setText(fmt_rp(harga))
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
                return parse_angka(self.table_2.item(r, 3).text())
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

        nilai_jumlah = parse_angka(jumlah)
        nilai_harga  = parse_angka(harga)

        if nilai_jumlah <= 0:
            QMessageBox.warning(self, "Perhatian", "Jumlah harus lebih dari 0!")
            return
        if nilai_harga <= 0:
            QMessageBox.warning(self, "Perhatian", "Harga tidak valid!")
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
                jml_lama = parse_angka(self.table_2.item(r, 3).text())
                jml_baru = jml_lama + nilai_jumlah
                sub_baru = jml_baru * nilai_harga
                self.table_2.setItem(r, 3, self._item_jumlah(jml_baru))
                self.table_2.setItem(r, 4, item_rp(sub_baru))
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
        self.table_2.setItem(row, 2, item_rp(nilai_harga))        # HARGA
        self.table_2.setItem(row, 3, self._item_jumlah(nilai_jumlah))
        self.table_2.setItem(row, 4, item_rp(hitung))             # TOTAL

        self.jum()
        self.tot()
        self.clearform()

    @staticmethod
    def _item_jumlah(nilai):
        it = QtWidgets.QTableWidgetItem(f"{nilai:.0f}")
        it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        return it

    def edit_keranjang(self):
        row = self.table_2.currentRow()
        if row == -1:
            QMessageBox.information(self, "Info", "Pilih item di keranjang yang ingin diedit!")
            return

        nama_item  = self.table_2.item(row, 1).text()
        id_item    = self.table_2.item(row, 1).data(Qt.UserRole)
        harga_item = parse_angka(self.table_2.item(row, 2).text())
        jml_lama   = int(parse_angka(self.table_2.item(row, 3).text()))

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
            self.table_2.setItem(row, 3, self._item_jumlah(jumlah_baru))
            self.table_2.setItem(row, 4, item_rp(subtotal_baru))
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
                jml     = parse_angka(self.table_2.item(row, 3).text())
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

        total   = parse_angka(total_text)
        payment = parse_angka(uang_text)

        if total <= 0:
            QMessageBox.warning(self, "Perhatian", "Total bayar tidak valid!")
            return

        if payment >= total:
            change = payment - total
            self.kembalian.setText(fmt_rp(change))

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
                # (angka dikirim tanpa format supaya kolom DB tetap numerik)
                curr.execute(
                    "INSERT INTO laporan (nama, jumlah, total, tanggal) VALUES (%s, %s, %s, %s)",
                    (namapembeli,
                     f"{parse_angka(self.jumlah2.text()):.0f}",
                     f"{total:.0f}",
                     waktu_transaksi)
                )

                # Kurangi stock tiap item yang dibeli
                for row in range(self.table_2.rowCount()):
                    id_item = self.table_2.item(row, 1).data(Qt.UserRole)
                    jml     = parse_angka(self.table_2.item(row, 3).text())
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
                                f"Uang kurang {fmt_rp(kekurangan)}")

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

        margin = pt(14)
        avail  = pw - margin * 2
        lh     = pt(15)
        black  = QtGui.QColor("#000000")

        def make_font(size_pt, bold=False):
            f = QFont("Courier New", size_pt)
            f.setBold(bold)
            f.setPixelSize(pt(size_pt))
            return f

        def text_w(text, font):
            return QFontMetrics(font).horizontalAdvance(text)

        def draw_center(text, font, y):
            painter.setFont(font)
            painter.drawText((pw - text_w(text, font)) // 2, y, text)

        def draw_left(text, font, y, x=None):
            painter.setFont(font)
            painter.drawText(margin if x is None else x, y, text)

        def draw_right(text, font, y):
            painter.setFont(font)
            painter.drawText(pw - margin - text_w(text, font), y, text)

        def garis(y, inset=0.0):
            painter.setPen(QtGui.QPen(black, max(1, pt(0.8))))
            dx = int(avail * inset)
            painter.drawLine(margin + dx, y, pw - margin - dx, y)
            painter.setPen(black)

        def garis_ganda(y, inset=0.0):
            painter.setPen(QtGui.QPen(black, max(1, pt(0.8))))
            dx = int(avail * inset)
            painter.drawLine(margin + dx, y, pw - margin - dx, y)
            painter.drawLine(margin + dx, y + pt(3), pw - margin - dx, y + pt(3))
            painter.setPen(black)

        painter.setPen(black)

        # ── Data ──
        total_val   = self.hitung_total()
        bayar_val   = parse_angka(self.uangpembayaran.text())
        kembali_val = bayar_val - total_val

        waktu     = waktu_transaksi or datetime.now()
        waktu_str = waktu.strftime("%d-%m-%Y %H:%M")
        nama_pemesan = self.pemesan.text().strip() or "-"

        f_norm  = make_font(8)
        f_bold  = make_font(8, bold=True)

        y = pt(14)

        # ── Header ──
        draw_center("Gerai CerdasQ", make_font(11, bold=True), y);           y += lh
        draw_center("Kab. Malinau, Kalimantan Utara", make_font(8), y);      y += lh
        draw_center("STRUK BELANJA", make_font(9, bold=True), y);            y += int(lh * 0.8)
        garis(y, 0.02);                                                      y += int(lh * 1.6)

        # ── Tanggal & waktu ──
        draw_center(waktu_str, make_font(13, bold=True), y);                 y += int(lh * 1.4)

        draw_left(f"Pemesan : {nama_pemesan}", f_norm, y);                   y += int(lh * 0.7)
        garis(y, 0.05);                                                      y += int(lh * 1.4)

        # ── Item pesanan ──
        draw_left("Item Pesanan:", f_norm, y);                               y += int(lh * 1.3)

        gap = pt(8)
        for row in range(self.table_2.rowCount()):
            nama = self.table_2.item(row, 1).text()
            hrg  = parse_angka(self.table_2.item(row, 2).text())
            jml  = int(parse_angka(self.table_2.item(row, 3).text()))
            sub  = parse_angka(self.table_2.item(row, 4).text())

            detail = f"{fmt_rp(hrg)} x {jml}"
            kiri   = f"{nama} {detail}"
            kanan  = fmt_rp(sub)

            if text_w(kiri, f_norm) + gap + text_w(kanan, f_norm) <= avail:
                draw_left(kiri, f_norm, y)
                draw_right(kanan, f_norm, y)
                y += lh
            elif text_w(kiri, f_norm) <= avail:
                draw_left(kiri, f_norm, y);  y += lh
                draw_left(kanan, f_norm, y); y += lh
            else:
                draw_left(nama, f_norm, y);   y += lh
                draw_left(detail, f_norm, y)
                draw_right(kanan, f_norm, y); y += lh
            y += pt(3)

        y -= pt(3)
        y += int(lh * 0.2)
        garis(y, 0.02);                                                      y += int(lh * 1.5)

        # ── Total ──
        x_label = margin + pt(6)
        x_value = x_label + text_w("Total Belanja : ", f_bold)
        x_colon = x_value - text_w(": ", f_bold)

        def baris_total(label, nilai, font):
            draw_left(label, font, y_now[0], x=x_label)
            draw_left(":", font, y_now[0], x=x_colon)
            draw_left(nilai, font, y_now[0], x=x_value)
            y_now[0] += int(lh * 1.3)

        y_now = [y]
        baris_total("Total Belanja", fmt_rp(total_val),   f_bold)
        baris_total("Uang Bayar",    fmt_rp(bayar_val),   f_norm)
        baris_total("Kembalian",     fmt_rp(kembali_val), f_bold)
        y = y_now[0]

        y -= int(lh * 0.5)
        garis_ganda(y, 0.02);                                                y += int(lh * 2)

        # ── Footer ──
        draw_center("Terima Kasih Sudah Mampir!", make_font(9, bold=True), y); y += int(lh * 1.3)
        draw_center("Selamat Makan!", make_font(8), y)

        painter.end()

    def cetak_struk(self, waktu_transaksi=None):
        """Tampilkan dialog print. Keranjang TIDAK dikosongkan di sini —
        pengosongan keranjang & refresh data menu ditangani terpusat di bayarr()."""
        printer = self._buat_printer()
        dialog  = QPrintDialog(printer, self)
        if dialog.exec_() == QPrintDialog.Accepted:
            self._render_struk(printer, waktu_transaksi)

    def jum(self):
        jum = 0
        for row in range(self.table_2.rowCount()):
            item = self.table_2.item(row, 3)
            if item:
                jum += parse_angka(item.text())
        self.jumlah2.setText(f"{jum:.0f}")

    def hitung_total(self):
        total = 0
        for row in range(self.table_2.rowCount()):
            try:
                h = parse_angka(self.table_2.item(row, 2).text())
                j = parse_angka(self.table_2.item(row, 3).text())
                total += h * j
            except AttributeError:
                pass
        return total

    def tot(self):
        total = 0
        for row in range(self.table_2.rowCount()):
            item = self.table_2.item(row, 4)
            if item:
                total += parse_angka(item.text())
        self.totalbayar.setText(fmt_rp(total))

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
#  DAFTAR MENU  (search berdasarkan kode/ID Menu atau nama)
# ─────────────────────────────────────────────
class DftrMenu(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.Window |
            Qt.WindowMinimizeButtonHint |
            Qt.WindowMaximizeButtonHint |
            Qt.WindowCloseButtonHint
        )
        uic.loadUi("DaftarMenu.ui", self)
        available = QDesktopWidget().availableGeometry()
        self.resize(min(980, available.width()), min(660, available.height()))
        _setup_responsive_scaling(self, self.widget, 980, 660)
        self.center()
        self._simpan_mode = 'baru'
        self._edit_mode = 'view'
        self._all_data = []          # cache semua data menu untuk difilter
        self.tombol()
        self.tabelWidtg()
        # Input harga ikut berformat ribuan saat diketik
        pasang_format_uang(self.textHarga)
        self.loaddata()
        self.activeText(False)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        _apply_responsive_scaling(self)

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
        self.textSearchMenu.textChanged.connect(self.filter_data)

    def tabelWidtg(self):
        header = self.tableWidget.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        if self.tableWidget.columnCount() > 2:
            header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setMinimumSectionSize(70)
        header.setStretchLastSection(False)
        self.tableWidget.setWordWrap(False)
        self.tableWidget.setTextElideMode(Qt.ElideNone)

    def loaddata(self):
        conn = get_connection()
        curr = conn.cursor()
        curr.execute("SELECT idMenu, kategori, namaMenu, harga, stock FROM tbbarang ORDER BY harga DESC")
        result = curr.fetchall()
        curr.close()
        conn.close()

        self._all_data = result
        keyword = self.textSearchMenu.text() if hasattr(self, 'textSearchMenu') else ""
        self._render_table(self._filter_by_keyword(keyword))

    def _filter_by_keyword(self, keyword):
        """row = (idMenu, kategori, namaMenu, harga, stock)"""
        keyword = (keyword or "").strip().lower()
        if not keyword:
            return self._all_data
        return [
            row for row in self._all_data
            if keyword in str(row[0]).lower() or keyword in str(row[2]).lower()
        ]

    def _render_table(self, rows):
        self.tableWidget.setRowCount(len(rows))
        for row, item in enumerate(rows):
            self.tableWidget.setItem(row, 0, QtWidgets.QTableWidgetItem(str(item[0])))
            self.tableWidget.setItem(row, 1, QtWidgets.QTableWidgetItem(str(item[1])))
            self.tableWidget.setItem(row, 2, QtWidgets.QTableWidgetItem(str(item[2])))
            self.tableWidget.setItem(row, 3, item_rp(item[3]))     # HARGA -> Rp 15.000
            if self.tableWidget.columnCount() > 4:
                stok = QtWidgets.QTableWidgetItem(str(item[4]))
                stok.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.tableWidget.setItem(row, 4, stok)

    def filter_data(self, keyword):
        self._render_table(self._filter_by_keyword(keyword))

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
        # kolom sudah terformat -> kembalikan ke angka lalu biarkan formatter jalan
        self.textHarga.setText(f"{parse_angka(self.tableWidget.item(row, 3).text()):.0f}")
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
            hargaa   = int(parse_angka(self.textHarga.text()))   # simpan tanpa format
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
        conn = get_connection()
        curr = conn.cursor()
        curr.execute("SELECT idMenu FROM tbbarang")
        rows = curr.fetchall()
        curr.close()
        conn.close()

        max_num = 0
        prefix  = ''
        width   = 3

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

        if len(new_id) > 5:
            new_id = new_id[-5:]

        return new_id

    def simpandata(self):
        if self._simpan_mode == 'baru':
            self.activeText(True)
            self.clearform()
            self.textIdMenu.setText(self.generate_next_id())
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
            hargaa   = int(parse_angka(self.textHarga.text()))   # simpan tanpa format
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
        self.setWindowFlags(
            Qt.Window |
            Qt.WindowMinimizeButtonHint |
            Qt.WindowMaximizeButtonHint |
            Qt.WindowCloseButtonHint
        )
        available = QDesktopWidget().availableGeometry()
        self.resize(min(936, available.width()), min(668, available.height()))
        self.center()
        self._buat_filter_tanggal()
        self.tombol()
        self._chart_dari = None
        self._chart_sampai = None
        self._setup_chart()
        self.loaddata2()
        self.tabelWidtg()
        self.tot()
        self.cb_filter.setCursor(Qt.PointingHandCursor)
        self.cb_filter.view().setCursor(Qt.PointingHandCursor)
        self.cb_filter.currentTextChanged.connect(self._update_chart)
        self._update_chart()
        # Dipanggil TERAKHIR supaya semua widget (termasuk tombol Cetak) ikut terdaftar
        _setup_responsive_scaling(self, self.widget_2, 936, 668)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        _apply_responsive_scaling(self)

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def _setup_chart(self):
        self.figure = Figure(figsize=(4, 4), dpi=100)
        self.figure.patch.set_facecolor(CHART_BG)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setObjectName("chart_canvas")
        self.ax = self.figure.add_subplot(111)
        self._style_axes()
        layout = QVBoxLayout(self.frame_chart)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(self.canvas)

    def _style_axes(self):
        ax = self.ax
        ax.set_axis_on()
        ax.set_facecolor(CHART_BG)
        ax.tick_params(colors=CHART_TEXT, labelsize=8, length=0)
        for name, spine in ax.spines.items():
            if name in ('top', 'right'):
                spine.set_visible(False)
            else:
                spine.set_edgecolor(CHART_AXIS)
        ax.yaxis.grid(True, color=CHART_GRID, linewidth=1)
        ax.set_axisbelow(True)

    def _get_chart_data(self):
        conn = get_connection()
        curr = conn.cursor()
        try:
            if self._chart_dari and self._chart_sampai:
                curr.execute(
                    "SELECT tanggal, total FROM laporan WHERE tanggal BETWEEN %s AND %s ORDER BY tanggal ASC",
                    (self._chart_dari, self._chart_sampai)
                )
            else:
                curr.execute("SELECT tanggal, total FROM laporan ORDER BY tanggal ASC")
            return curr.fetchall()
        finally:
            curr.close()
            conn.close()

    def _update_chart(self):
        filter_type = self.cb_filter.currentText()
        data = self._get_chart_data()
        self.ax.clear()
        self._style_axes()

        if not data:
            self.ax.set_axis_off()
            self.ax.text(0.5, 0.5, 'Tidak ada data', transform=self.ax.transAxes,
                        ha='center', va='center', color='#94a3b8', fontsize=10)
            self.canvas.draw()
            return

        from collections import defaultdict
        groups = defaultdict(float)
        for tanggal, total in data:
            ada = hasattr(tanggal, 'strftime')
            if filter_type == "Harian":
                key = tanggal.strftime("%d-%m-%Y") if ada else str(tanggal)[:10]
            elif filter_type == "Mingguan":
                key = tanggal.strftime("Minggu %V, %Y") if ada else str(tanggal)[:10]
            else:
                key = str(tanggal.year) if hasattr(tanggal, 'year') else str(tanggal)[:4]
            groups[key] += parse_angka(total)

        labels = list(groups.keys())
        values = list(groups.values())

        judul = {"Harian": "Pendapatan Harian",
                "Mingguan": "Pendapatan Mingguan"}.get(filter_type, "Pendapatan Tahunan")

        self.ax.bar(labels, values, width=0.6,
                    color=CHART_COLOR.get(filter_type, '#818cf8'))
        self.ax.set_title(judul, fontsize=10, fontweight='bold', color=CHART_TITLE, pad=10)
        self.ax.set_ylabel("Total (Rp)", fontsize=9, color=CHART_TEXT)
        self.ax.yaxis.set_major_formatter(FuncFormatter(_fmt_singkat))

        if filter_type != "Tahunan":
            for lbl in self.ax.get_xticklabels():
                lbl.set_rotation(45)
                lbl.set_ha('right')
                lbl.set_fontsize(7 if filter_type == "Harian" else 8)

        self.figure.tight_layout()
        self.canvas.draw()

    def _buat_filter_tanggal(self):
        """Kontrol filter dibuat lewat kode, diletakkan di widget_2 (bukan di dialog)
        supaya posisinya mengikuti layout .ui dan ikut responsive scaling."""
        p = self.widget_2

        lbl_dari   = QLabel("Dari:", p)
        lbl_sampai = QLabel("Sampai:", p)
        self.dateDari   = SelectDateEdit(p)
        self.dateSampai = SelectDateEdit(p)
        self.btnFilter  = QPushButton("🔍 Filter", p)
        self.btnReset   = QPushButton("↩ Reset", p)
        self.btnCetak   = QPushButton("🖨  Cetak", p)

        # ── WAJIB: tanpa objectName, widget TIDAK ikut responsive scaling ──
        lbl_dari.setObjectName("lbl_dari")
        lbl_sampai.setObjectName("lbl_sampai")
        self.dateDari.setObjectName("dateDari")
        self.dateSampai.setObjectName("dateSampai")
        self.btnFilter.setObjectName("btnFilter")
        self.btnReset.setObjectName("btnReset")
        self.btnCetak.setObjectName("btnCetak")

        for d, tgl in ((self.dateDari, QDate.currentDate().addMonths(-1)),
                    (self.dateSampai, QDate.currentDate())):
            d.setDisplayFormat("dd-MM-yyyy")
            d.setDate(tgl)
            d.setStyleSheet(STYLE_SELECT_DATE)

        style_primary = """
            QPushButton { background-color: #2563eb; color: #ffffff; border: none;
                        border-radius: 8px; padding: 0px 6px; font-size: 12px; font-weight: 600; }
            QPushButton:hover { background-color: #1d4ed8; }
            QPushButton:pressed { background-color: #1e40af; }
        """
        style_soft = """
            QPushButton { background-color: #eff6ff; color: #1d4ed8; border: 1.5px solid #bfdbfe;
                        border-radius: 8px; padding: 0px 6px; font-size: 12px; font-weight: 600; }
            QPushButton:hover { border-color: #2563eb; background-color: #dbeafe; }
        """
        self.btnFilter.setStyleSheet(style_primary)
        self.btnReset.setStyleSheet(style_soft)
        self.btnCetak.setStyleSheet(style_soft.replace("font-size: 12px", "font-size: 13px"))

        lbl_dari.setGeometry(28, 76, 34, 34)
        self.dateDari.setGeometry(64, 76, 120, 34)
        lbl_sampai.setGeometry(192, 76, 46, 34)
        self.dateSampai.setGeometry(240, 76, 120, 34)
        self.btnFilter.setGeometry(370, 76, 78, 34)
        self.btnReset.setGeometry(450, 76, 78, 34)
        self.btnCetak.setGeometry(636, 604, 130, 40)

        for w in (lbl_dari, lbl_sampai, self.dateDari, self.dateSampai,
                self.btnFilter, self.btnReset, self.btnCetak):
            w.show()
        for b in (self.btnFilter, self.btnReset, self.btnCetak):
            b.setCursor(Qt.PointingHandCursor)

        self.btnFilter.clicked.connect(self.terapkan_filter)
        self.btnReset.clicked.connect(self.reset_filter)
        self.btnCetak.clicked.connect(self.cetak_pendapatan)

    def tabelWidtg(self):
        header = self.tableWidget_2.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        if self.tableWidget_2.columnCount() > 0:
            header.setSectionResizeMode(0, QHeaderView.Stretch)  # kolom Nama Pembeli
        header.setMinimumSectionSize(70)
        header.setStretchLastSection(False)
        self.tableWidget_2.setWordWrap(False)
        self.tableWidget_2.setTextElideMode(Qt.ElideNone)

    def tombol(self):
        self.keluar.clicked.connect(self.kembali)

    def terapkan_filter(self):
        dari, sampai = self._rentang_tanggal_aktif()
        self._chart_dari = dari
        self._chart_sampai = sampai
        self.loaddata2(dari, sampai)
        self.tot(dari, sampai)
        self._update_chart()

    def reset_filter(self):
        self.dateDari.setDate(QDate.currentDate().addMonths(-1))
        self.dateSampai.setDate(QDate.currentDate())
        self._chart_dari = None
        self._chart_sampai = None
        self.loaddata2()
        self.tot()
        self._update_chart()

    def _rentang_tanggal_aktif(self):
        dari = self.dateDari.date().toString("yyyy-MM-dd") + " 00:00:00"
        sampai = self.dateSampai.date().toString("yyyy-MM-dd") + " 23:59:59"
        return dari, sampai

    def _ambil_data_pendapatan(self):
        dari, sampai = self._rentang_tanggal_aktif()
        conn = get_connection()
        curr = conn.cursor()
        try:
            curr.execute(
                "SELECT nama, jumlah, total, tanggal FROM laporan "
                "WHERE tanggal BETWEEN %s AND %s ORDER BY tanggal ASC",
                (dari, sampai)
            )
            return curr.fetchall()
        finally:
            curr.close()
            conn.close()

    def _kelompokkan_pendapatan(self, rows):
        from collections import defaultdict

        groups = defaultdict(lambda: [0, 0.0, 0.0])
        filter_type = self.cb_filter.currentText()
        for nama, jumlah, total, tanggal in rows:
            if filter_type == "Harian":
                periode = tanggal.strftime("%d-%m-%Y")
            elif filter_type == "Mingguan":
                periode = tanggal.strftime("Minggu %V, %Y")
            else:
                periode = tanggal.strftime("%Y")
            groups[periode][0] += 1
            groups[periode][1] += parse_angka(jumlah)
            groups[periode][2] += parse_angka(total)
        return sorted(groups.items())

    def cetak_pendapatan(self):
        try:
            rows = self._ambil_data_pendapatan()
        except Exception as e:
            QMessageBox.critical(self, "Error DB", f"Gagal mengambil data pendapatan:\n{e}")
            return

        if not rows:
            QMessageBox.information(self, "Data Kosong", "Tidak ada pendapatan pada rentang tanggal tersebut.")
            return

        printer = QPrinter(QPrinter.HighResolution)
        printer.setPageSize(QPrinter.A4)
        printer.setOrientation(QPrinter.Landscape)
        dialog = QPrintDialog(printer, self)
        if dialog.exec_() != QPrintDialog.Accepted:
            return

        painter = QPainter()
        if not painter.begin(printer):
            QMessageBox.critical(self, "Error", "Gagal memulai proses cetak.")
            return

        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        # Semua ukuran dikonversi dari "poin" ke unit device sesuai DPI printer.
        dpi = printer.resolution()

        def pt(points):
            return int(points * dpi / 72)

        page = printer.pageRect()
        margin = pt(40)
        content_width = page.width() - (margin * 2)

        title_font  = QFont("Segoe UI", 16); title_font.setBold(True)
        sub_font    = QFont("Segoe UI", 10)
        bold_font   = QFont("Segoe UI", 10); bold_font.setBold(True)
        normal_font = QFont("Segoe UI", 10)
        small_font  = QFont("Segoe UI", 9)

        title_h  = pt(26)
        sub_h    = pt(20)
        gap_after_heading = pt(14)
        header_row_h = pt(30)
        row_h    = pt(26)
        row_pad  = pt(4)

        dari, sampai = self._rentang_tanggal_aktif()
        grouped_rows = self._kelompokkan_pendapatan(rows)
        total = sum(values[2] for _, values in grouped_rows)

        columns = (
            ("Periode", int(content_width * 0.38), Qt.AlignLeft),
            ("Transaksi", int(content_width * 0.16), Qt.AlignRight),
            ("Jumlah Item", int(content_width * 0.18), Qt.AlignRight),
            ("Pendapatan", 0, Qt.AlignRight),
        )
        columns = list(columns)
        columns[-1] = (columns[-1][0], content_width - sum(column[1] for column in columns[:-1]), columns[-1][2])

        cell_pad = pt(8)

        def draw_cell(text, x, width, alignment, font, row_top, row_height):
            painter.setFont(font)
            painter.drawText(x + cell_pad, row_top, width - cell_pad * 2, row_height,
                              alignment | Qt.AlignVCenter, str(text))

        def draw_table_header():
            nonlocal y
            painter.fillRect(margin, y, content_width, header_row_h, QtGui.QColor("#e8eefc"))
            painter.setPen(QtGui.QColor("#1e40af"))
            x = margin
            for title, width, alignment in columns:
                draw_cell(title, x, width, alignment, bold_font, y, header_row_h)
                x += width
            y += header_row_h
            painter.setPen(QtGui.QColor("#9ca3af"))
            painter.drawLine(margin, y, margin + content_width, y)
            y += pt(6)

        def draw_page_heading():
            nonlocal y
            y = margin
            painter.setPen(QtGui.QColor("#111827"))
            painter.setFont(title_font)
            painter.drawText(margin, y, content_width, title_h, Qt.AlignLeft | Qt.AlignVCenter, "LAPORAN PENDAPATAN")
            y += title_h
            painter.setFont(sub_font)
            painter.drawText(
                margin, y, content_width, sub_h, Qt.AlignLeft | Qt.AlignVCenter,
                f"Filter: {self.cb_filter.currentText()}    Periode: {dari[:10]} s/d {sampai[:10]}"
            )
            y += sub_h + gap_after_heading
            draw_table_header()

        def draw_data_row(periode, values):
            nonlocal y
            x = margin
            row_data = (periode, values[0], fmt_ribuan(values[1]), fmt_rp(values[2]))
            for text, (_, width, alignment) in zip(row_data, columns):
                draw_cell(text, x, width, alignment, normal_font, y, row_h)
                x += width
            y += row_h
            painter.setPen(QtGui.QColor("#d1d5db"))
            painter.drawLine(margin, y, margin + content_width, y)
            y += row_pad

        y = margin
        draw_page_heading()
        for periode, values in grouped_rows:
            if y + row_h > page.bottom() - margin:
                printer.newPage()
                page = printer.pageRect()
                draw_page_heading()
            draw_data_row(periode, values)

        footer_h = pt(50)
        if y + footer_h > page.bottom() - margin:
            printer.newPage()
            page = printer.pageRect()
            draw_page_heading()

        y += pt(10)
        painter.setFont(bold_font)
        painter.setPen(QtGui.QColor("#111827"))
        painter.drawText(
            margin, y, content_width, row_h,
            Qt.AlignRight | Qt.AlignVCenter,
            f"TOTAL PENDAPATAN: {fmt_rp(total)}"
        )

        painter.setFont(small_font)
        painter.setPen(QtGui.QColor("#6b7280"))
        painter.drawText(
            margin, page.bottom() - margin - pt(20), content_width, pt(20),
            Qt.AlignRight | Qt.AlignVCenter,
            "Dicetak dari aplikasi kasir"
        )
        painter.end()

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
        idx_nama = col_names.index('nama') if 'nama' in col_names else 1
        idx_jumlah = col_names.index('jumlah') if 'jumlah' in col_names else 2
        idx_total = col_names.index('total') if 'total' in col_names else 3

        self.tableWidget_2.setRowCount(len(result))
        for row, item in enumerate(result):
            self.tableWidget_2.setItem(row, 0, QtWidgets.QTableWidgetItem(str(item[idx_nama])))

            jml = QtWidgets.QTableWidgetItem(f"{parse_angka(item[idx_jumlah]):.0f}")
            jml.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tableWidget_2.setItem(row, 1, jml)

            self.tableWidget_2.setItem(row, 2, item_rp(item[idx_total]))   # TOTAL -> Rp ...

            waktu = item[idx_tanggal] if idx_tanggal is not None else None
            waktu_str = (
                waktu.strftime("%d-%m-%Y %H:%M")
                if hasattr(waktu, 'strftime') else str(waktu or "-")
            )
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
            tota += parse_angka(row[0])
        self.Total.setStyleSheet("font-size: 18px")
        self.Total.setText(fmt_rp(tota))

    def kembali(self):
        self.openkasir = Pilihan()
        self.openkasir.show()
        self.close()


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet("""
        QMessageBox {
            background-color: #eef3fa;
        }
        QMessageBox QLabel {
            color: #1e293b;
            font-size: 13px;
        }
        QMessageBox QPushButton {
            background-color: #2563eb;
            color: #ffffff;
            border-radius: 6px;
            padding: 6px 16px;
            min-width: 70px;
        }
        QMessageBox QPushButton:hover {
            background-color: #1d4ed8;
        }
    """)
    window = login()
    window.show()
    sys.exit(app.exec_())
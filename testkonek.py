import mysql.connector
from mysql.connector import Error

try:
    # Ganti dengan konfigurasi database Anda
    connection = mysql.connector.connect(user='root', password='', host='127.0.0.1', database='warungme')
    if connection.is_connected():
        print("Koneksi ke MySQL berhasil!")
        db_info = connection.get_server_info()
        print("Versi server MySQL:", db_info)

except Error as e:
    print("Terjadi kesalahan saat koneksi ke MySQL:", e)

finally:
    if 'connection' in locals() and connection.is_connected():
        curr = connection.cursor()
        curr.execute("SELECT * FROM auth")
        user = curr.fetchone()
        print(user)
        connection.close()
        print("Koneksi MySQL ditutup.")
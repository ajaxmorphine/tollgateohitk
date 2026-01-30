import sqlite3
from datetime import datetime

class TollDatabase:
    def __init__(self, db_name="toll_history.db"):
        self.db_name = db_name
        self.init_db()

    def init_db(self):
        """Membuat tabel jika belum ada."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS kendaraan_masuk (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                card_id TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def insert_data(self, card_id):
        """Menyimpan data kartu dan waktu masuk."""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("INSERT INTO kendaraan_masuk (timestamp, card_id) VALUES (?, ?)", 
                           (now, card_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Database Error: {e}")
            return False

    def get_last_id(self):
        """Mendapatkan ID terakhir untuk counter jika diperlukan."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM kendaraan_masuk")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def clear_table(self):
        """Menghapus semua data dari tabel kendaraan_masuk."""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM kendaraan_masuk")
            # Opsional: Reset hitungan ID auto-increment kembali ke 1
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='kendaraan_masuk'")
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Gagal menghapus database: {e}")
            return False
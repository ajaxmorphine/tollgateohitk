import serial
from tkinter import ttk
import tkinter as tk
import time
from tkinter import messagebox # Untuk notifikasi pop-up
from toll_database import TollDatabase
import webbrowser

GERBANG_DATA = {
    "Manggar Utama": "toll_manggar.db",        # Ini Manggar
    "Karang Joang": "toll_karangjoang.db",    # Ini Karang Joang
    "Samboja": "toll_samboja.db",   # Ini Samboja
    "Palaran": "toll_palaran.db"            # Ini Palaran
}

db = TollDatabase()

# --- INISIALISASI SERIAL ---
try:
    ser = serial.Serial('COM12', 9600, timeout=0.1) 
except Exception as e:
    print(f"Gagal koneksi: {e}")
    ser = None 

kendaraan_count = db.get_last_id()

last_serial_activity = 0

def update_connection_status():
    global ser, last_serial_activity
    
    # Logika: Jika port terbuka DAN ada aktivitas data dalam 3 detik terakhir
    is_connected = False
    if ser and ser.is_open:
        try:
            # Kirim sinyal kecil ke Arduino untuk cek apakah kabel masih 'hidup'
            ser.write(b'\0') 
            is_connected = True
        except:
            is_connected = False
            ser.close() # Paksa tutup jika kabel dicabut
            ser = None

    if is_connected:
        canvas_status.itemconfig(circle_status, fill="#2ecc71") # Hijau
    else:
        canvas_status.itemconfig(circle_status, fill="#e74c3c") # Merah
        # Coba sambung kembali secara otomatis
        try:
            ser = serial.Serial('COM12', 9600, timeout=0.1)
        except:
            pass

    root.after(2000, update_connection_status)
    
# --- FUNGSI LAINNYA --- 
def update_time():
    current_time = time.strftime('%H:%M:%S %d-%m-%Y')
    label_jam.config(text=current_time)
    label_jam.after(1000, update_time)

def emergency_exit():
    if ser: ser.write(b'E') 
    label_counter.config(text=f"Kendaraan Lewat: {kendaraan_count}")

def reset_all():
    global kendaraan_count
    if ser: ser.write(b'R') 
    kendaraan_count = 0 
    label_counter.config(text=f"Kendaraan Lewat: {kendaraan_count}")
    reset_to_idle()

def reset_to_idle():
    root.config(bg="#ffffff")
    label.config(text="Tap Kartu E-Toll", bg="#ffffff", fg="#223468")
    
def cctv_tol_balikpapan_samarinda():
    webbrowser.open("https://nataru.pu.go.id/cctv-tol?id_ruas=balikpapan-samarinda")

def update_label():
    global kendaraan_count
    if ser and ser.in_waiting > 0:
        try:
            raw_data = ser.readline().decode('utf-8').strip()
            if "Pesan : " in raw_data:
                msg = raw_data.split("Pesan : ")[1].strip()
                label.config(text=msg)
                if "Berhasil" in msg:
                    db.insert_data("E-TOLL-USER")
                    kendaraan_count += 1
                    label_counter.config(text=f"Kendaraan Lewat: {kendaraan_count}")
                    root.config(bg="#2ecc71")
                    label.config(bg="#2ecc71", fg="white")
                    refresh_table()
                    root.after(7000, reset_to_idle)
                elif "Gagal" in msg:
                    root.config(bg="#e74c3c")
                    label.config(bg="#e74c3c", fg="white")
                    root.after(7000, reset_to_idle)
                elif "Emergency" in msg:
                    root.config(bg="#f39c12")
                    label.config(bg="#f39c12", fg="white")
                    root.after(7000, reset_to_idle)
        except:
            pass
    root.after(50, update_label)

def refresh_table():
    # 1. Hapus data lama di tabel UI
    for item in tree.get_children():
        tree.delete(item)
    
    try:
        # 2. Ambil data dari database
        data = db.fetch_all_data() 
        
        # 3. Balik urutan (data terbaru di atas) dan ambil 5 teratas
        # row[0] = ID, row[1] = Timestamp/Jam, row[2] = Card_ID
        for row in reversed(data[-5:]): 
            tree.insert("", "end", values=(row[1], row[2]))
            
    except Exception as e:
        print(f"Gagal memuat data ke tabel: {e}")
        
def hapus_riwayat_db():
    # Menampilkan konfirmasi agar tidak terhapus tidak sengaja
    jawaban = messagebox.askyesno("Konfirmasi", "Apakah Anda yakin ingin menghapus semua riwayat kendaraan?")
    if jawaban:
        if db.clear_table():
            global kendaraan_count
            kendaraan_count = 0
            label_counter.config(text=f"Kendaraan Lewat: {kendaraan_count}")
            refresh_table()
            messagebox.showinfo("Berhasil", "Semua data riwayat telah dihapus!")
        else:
            messagebox.showerror("Error", "Gagal menghapus data dari database.")
            
def on_gate_change(event):
    global db, kendaraan_count
    selected_text = combo_gate.get()
    db_file = GERBANG_DATA[selected_text]
    db = TollDatabase(db_file)
    kendaraan_count = db.get_last_id()
    label_counter.config(text=f"Kendaraan Lewat: {kendaraan_count}")
    refresh_table()
    print(f"Sistem aktif di: {selected_text} ({db_file})")

# --- UI SETUP ---
root = tk.Tk()
root.title("Toll Gate Balikpapan Samarinda - #KonektivitasUntukNegeri")
root.iconbitmap("kemenpu.ico")
root.geometry("1000x700") # Sedikit lebih tinggi untuk tombol baru
root.config(bg="#ffffff")

frame_header = tk.Frame(root, bg="#223468", height=80)
frame_header.pack(side="top", fill="x")

Label_Proyek = tk.Label(frame_header, text="Toll Gate:", font=("Roboto", 20, "bold"), bg="#223468", fg="white")
Label_Proyek.pack(side="left", padx=0)

# Ambil daftar nama wilayah saja untuk isi dropdown
daftar_wilayah = list(GERBANG_DATA.keys()) 

combo_gate = ttk.Combobox(frame_header, values=list(GERBANG_DATA.keys()), state="readonly", font=("Roboto", 12, "bold"), width=20)
combo_gate.set("Manggar Utama") # Tampilan default awal
combo_gate.pack(side="left", padx=3)
combo_gate.bind("<<ComboboxSelected>>", on_gate_change)

label_jam = tk.Label(frame_header, text="", font=("Roboto", 18, "bold"), bg="#223468", fg="white", pady=5)
label_jam.pack(side="right", fill="x")

label = tk.Label(root, text="Tap Kartu E-Toll", font=("Roboto", 50, "bold"), bg="#ffffff", fg="#223468")
label.pack(expand=True, fill='both')

frame_tabel = tk.Frame(root, bg="#ffffff")
frame_tabel.place(x=25, y=470, width=280, height=150)

lbl_recent = tk.Label(frame_tabel, text="Riwayat Terakhir", font=("Roboto", 10, "bold"), bg="#ffffff", fg="#223468")
lbl_recent.pack(anchor="w")

columns = ("waktu", "id_kartu")
tree = ttk.Treeview(frame_tabel, columns=columns, show="headings", height=5)

tree.heading("waktu", text="Waktu")
tree.heading("id_kartu", text="ID Kartu")

tree.column("waktu", width=100, anchor="center")
tree.column("id_kartu", width=80, anchor="center")

tree.pack(fill="both", expand=True)

frame_tombol = tk.Frame(root, bg="#223468")
frame_tombol.pack(side="bottom", fill="x")

btn_clear_db = tk.Button(frame_tombol, text="CLEAR DATABASE", font=("Roboto", 11, "bold"), 
                         bg="#7f8c8d", fg="white", command=hapus_riwayat_db, padx=20, pady=10)
btn_clear_db.pack(side="left", padx=10, pady=10)

btn_reset = tk.Button(frame_tombol, text="RESET COUNTER", font=("Roboto", 11, "bold"), 
                      bg="#c0392b", fg="white", command=reset_all, padx=20, pady=10)
btn_reset.pack(side="left", padx=10, pady=10)

btn_emergency = tk.Button(frame_tombol, text="EMERGENCY EXIT", font=("Roboto", 11, "bold"), 
                          bg="#fcb717", fg="white", command=emergency_exit, padx=20, pady=10)
btn_emergency.pack(side="left", padx=10, pady=10)

btn_web = tk.Button(frame_tombol, text="CCTV TOL BALIKPAPAN SAMARINDA (TRAVOY)", font=("Roboto", 11, "bold"), 
                    bg="#2980b9", fg="white", command=cctv_tol_balikpapan_samarinda, padx=20, pady=10)
btn_web.pack(side="right", padx=10, pady=10)

label_counter = tk.Label(root, text="Kendaraan Lewat: 0", font=("Roboto", 24, "bold"), fg="white", padx=20, pady=10, bg="#3A3B3D")
label_counter.pack(side="right", padx=10, pady=10)

status_container = tk.Frame(root, bg="#1a2a44")
status_container.pack(anchor="e", pady=5)

status_container = tk.Frame(frame_header, bg="#223468")
status_container.pack(anchor="e")

label_status_text = tk.Label(status_container, text="Status Gerbang:", font=("Roboto", 9), fg="white", bg="#223468")
label_status_text.pack(side="left")

canvas_status = tk.Canvas(status_container, width=15, height=15, bg="#223468", highlightthickness=0)
canvas_status.pack(side="left", padx=5)
circle_status = canvas_status.create_oval(2, 2, 13, 13, fill="#e74c3c")


update_connection_status()
update_label()
update_time()
refresh_table()
root.mainloop()

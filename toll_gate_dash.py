import serial
from tkinter import ttk
import tkinter as tk
import time
from tkinter import messagebox # Untuk notifikasi pop-up
from toll_database import TollDatabase

db = TollDatabase()

# --- INISIALISASI SERIAL ---
try:
    ser = serial.Serial('COM12', 9600, timeout=1) 
except Exception as e:
    print(f"Gagal koneksi: {e}")
    ser = None 

kendaraan_count = db.get_last_id()

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
    root.after(100, update_label)

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

# --- UI SETUP ---
root = tk.Tk()
root.title("Toll Gate Karang Joang - #KonektivitasUntukNegeri")
root.iconbitmap("kemenpu.ico")
root.geometry("800x650") # Sedikit lebih tinggi untuk tombol baru
root.config(bg="#ffffff")

label_jam = tk.Label(root, text="", font=("Roboto", 18, "bold"), bg="#223468", fg="white", pady=5)
label_jam.pack(side="top", fill="x")

label = tk.Label(root, text="Tap Kartu E-Toll", font=("Roboto", 50, "bold"), bg="#ffffff", fg="#223468")
label.pack(expand=True, fill='both')

frame_tabel = tk.Frame(root, bg="#ffffff")
frame_tabel.place(x=25, y=420, width=280, height=150)

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

label_counter = tk.Label(root, text="Kendaraan Lewat: 0", font=("Roboto", 24, "bold"), fg="white", padx=20, pady=10, bg="#3A3B3D")
label_counter.pack(side="right", padx=10, pady=10)

update_label()
update_time()
refresh_table()
root.mainloop()

import serial
import tkinter as tk
import time
import csv # 1. Tambahkan modul CSV
from tkinter import messagebox # Untuk notifikasi pop-up

try:
    ser = serial.Serial('COM12', 9600, timeout=1) 
except Exception as e:
    print(f"Gagal koneksi: {e}")
    ser = None 

kendaraan_count = 0 

# --- FUNGSI EKSPOR CSV ---
def export_to_csv():
    global kendaraan_count
    nama_file = "laporan_tol.csv"
    timestamp_sekarang = time.strftime('%d/%m/%Y %H:%M:%S')
    
    try:
        # 'a' berarti append (menambah data ke baris baru tanpa menghapus data lama)
        with open(nama_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            # Tulis header jika file masih baru/kosong
            if file.tell() == 0:
                writer.writerow(["Tanggal & Waktu", "Jumlah Kendaraan Terakhir"])
            
            writer.writerow([timestamp_sekarang, kendaraan_count])
            
        messagebox.showinfo("Berhasil", f"Data berhasil diekspor ke {nama_file}")
    except Exception as e:
        messagebox.showerror("Error", f"Gagal mengekspor data: {e}")

# --- FUNGSI LAINNYA ---
def update_time():
    current_time = time.strftime('%d/%m/%Y  %H:%M:%S')
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
                    kendaraan_count += 1
                    label_counter.config(text=f"Kendaraan Lewat: {kendaraan_count}")
                    root.config(bg="#2ecc71")
                    label.config(bg="#2ecc71", fg="white")
                    root.after(5000, reset_to_idle)
                elif "Gagal" in msg:
                    root.config(bg="#e74c3c")
                    label.config(bg="#e74c3c", fg="white")
                    root.after(5000, reset_to_idle)
                elif "Emergency" in msg:
                    root.config(bg="#f39c12")
                    label.config(bg="#f39c12", fg="white")
                    root.after(5000, reset_to_idle)
        except:
            pass
    root.after(100, update_label)

# --- UI SETUP ---
root = tk.Tk()
root.title("Toll Gate System")
root.iconbitmap("kemenpu.ico")
root.geometry("800x650") # Sedikit lebih tinggi untuk tombol baru
root.config(bg="#ffffff")

label_jam = tk.Label(root, text="", font=("Courier New", 18, "bold"), bg="#223468", fg="white", pady=5)
label_jam.pack(side="top", fill="x")

label = tk.Label(root, text="Tap Kartu E-Toll", font=("Arial", 50, "bold"), bg="#ffffff", fg="#223468")
label.pack(expand=True, fill='both')

# Container Tombol Utama (Bawah)
frame_tombol = tk.Frame(root, bg="#223468")
frame_tombol.pack(side="bottom", fill="x")

# Tombol Emergency (Kiri)
btn_emergency = tk.Button(frame_tombol, text="EMERGENCY EXIT", font=("Arial", 12, "bold"), 
                          bg="#fcb717", fg="white", command=emergency_exit, padx=20, pady=10)
btn_emergency.pack(side="left", padx=10, pady=10)

# Tombol Ekspor (Tengah) - FITUR BARU
btn_export = tk.Button(frame_tombol, text="EXPORT CSV", font=("Arial", 12, "bold"), 
                       bg="#3498db", fg="white", command=export_to_csv, padx=20, pady=10)
btn_export.pack(side="left", padx=10, pady=10)

# Tombol Reset (Kanan)
btn_reset = tk.Button(frame_tombol, text="RESET COUNT", font=("Arial", 12, "bold"), 
                      bg="#c0392b", fg="white", command=reset_all, padx=20, pady=10)
btn_reset.pack(side="right", padx=10, pady=10)

label_counter = tk.Label(root, text="Kendaraan Lewat: 0", font=("Arial", 20, "bold"), bg="#223468", fg="white", pady=10)
label_counter.pack(side="bottom", fill="x")

update_label()
update_time()
root.mainloop()

import serial
import tkinter as tk
import time
from tkinter import messagebox # Untuk notifikasi pop-up

# --- INISIALISASI SERIAL ---
try:
    ser = serial.Serial('COM12', 9600, timeout=1) 
except Exception as e:
    print(f"Gagal koneksi: {e}")
    ser = None 

kendaraan_count = 0 

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
root.title("Toll Gate System - #KonektivitasUntukNegeri")
root.iconbitmap("kemenpu.ico")
root.geometry("800x650") # Sedikit lebih tinggi untuk tombol baru
root.config(bg="#ffffff")

label_jam = tk.Label(root, text="", font=("Roboto", 18, "bold"), bg="#223468", fg="white", pady=5)
label_jam.pack(side="top", fill="x")

label = tk.Label(root, text="Tap Kartu E-Toll", font=("Roboto", 50, "bold"), bg="#ffffff", fg="#223468")
label.pack(expand=True, fill='both')

# Container Tombol Utama (Bawah)
frame_tombol = tk.Frame(root, bg="#223468")
frame_tombol.pack(side="bottom", fill="x")

# Tombol Emergency (Kiri)
btn_emergency = tk.Button(frame_tombol, text="EMERGENCY EXIT", font=("Roboto", 11, "bold"), 
                          bg="#fcb717", fg="white", command=emergency_exit, padx=20, pady=10)
btn_emergency.pack(side="left", padx=10, pady=10)

# Tombol Reset (Kanan)
btn_reset = tk.Button(frame_tombol, text="RESET COUNT", font=("Roboto", 11, "bold"), 
                      bg="#c0392b", fg="white", command=reset_all, padx=20, pady=10)
btn_reset.pack(side="left", padx=10, pady=10)

label_counter = tk.Label(root, text="Kendaraan Lewat: 0", font=("Roboto", 24, "bold"), fg="white", padx=20, pady=10, bg="#3A3B3D")
label_counter.pack(side="right", padx=10, pady=10)

update_label()
update_time()
root.mainloop()

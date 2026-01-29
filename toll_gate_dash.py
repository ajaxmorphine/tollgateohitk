import serial
import tkinter as tk

try:
    # Sesuaikan COM port Anda
    ser = serial.Serial('COM12', 9600, timeout=1) 
except Exception as e:
    print(f"Gagal koneksi: {e}")
    exit()

kendaraan_count = 0 

def emergency_exit():
    ser.write(b'E') # Kirim sinyal E ke Arduino
    # Python juga menganggap ini kendaraan lewat (opsional)
    global kendaraan_count
    kendaraan_count += 0
    label_counter.config(text=f"Kendaraan Lewat: {kendaraan_count}")

def reset_all():
    global kendaraan_count
    ser.write(b'R') # Kirim sinyal R ke Arduino
    kendaraan_count = 0 # Reset hitungan di Python
    label_counter.config(text=f"Kendaraan Lewat: {kendaraan_count}")
    reset_to_idle()

def reset_to_idle():
    root.config(bg="#ffffff")
    label.config(text="Tap Kartu E-Toll", bg="#ffffff", fg="#223468")

def update_label():
    global kendaraan_count
    if ser.in_waiting > 0:
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
                
                elif "Gagal" in msg or "Peringatan" in msg:
                    root.config(bg="#e74c3c")
                    label.config(bg="#e74c3c", fg="white")
                    root.after(5000, reset_to_idle)
        except:
            pass
            
    root.after(100, update_label)
        
root = tk.Tk()
root.title("Toll Gate System")
#root.iconbitmap("kemenpu.ico") # Aktifkan jika file ada
root.geometry("800x600")
root.config(bg="#ffffff")

# Label Utama
label = tk.Label(root, text="Tap Kartu E-Toll", font=("Arial", 50, "bold"), bg="#ffffff", fg="#223468")
label.pack(expand=True, fill='both')

# Container Tombol
frame_tombol = tk.Frame(root, bg="#223468")
frame_tombol.pack(side="bottom", fill="x")

# Tombol Emergency
btn_emergency = tk.Button(frame_tombol, text="EMERGENCY EXIT", font=("Arial", 12, "bold"), 
                          bg="#fcb717", fg="white", command=emergency_exit, padx=20, pady=10)
btn_emergency.pack(side="left", padx=10, pady=10)

# Tombol Reset
btn_reset = tk.Button(frame_tombol, text="RESET COUNT & GATE", font=("Arial", 12, "bold"), 
                      bg="#c0392b", fg="white", command=reset_all, padx=20, pady=10)
btn_reset.pack(side="right", padx=10, pady=10)

# Label Counter (di atas tombol)
label_counter = tk.Label(root, text="Kendaraan Lewat: 0", font=("Arial", 20, "bold"), bg="#223468", fg="white", pady=10)
label_counter.pack(side="bottom", fill="x")

update_label()
root.mainloop()

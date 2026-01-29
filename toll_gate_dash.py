import serial
import tkinter as tk

try:
    ser = serial.Serial('COM12', 9600, timeout=1) 
except Exception as e:
    print(f"Gagal koneksi: {e}")
    exit()

# Variabel lokal Python untuk jaga-jaga jika Arduino tidak kirim angka
kendaraan_count = 0 

def reset_to_idle():
    root.config(bg="#ffffff")
    label.config(text="Tap Kartu E-Toll", bg="#ffffff", fg="#2c3e50")

def update_label():
    global kendaraan_count
    if ser.in_waiting > 0:
        try:
            raw_data = ser.readline().decode('utf-8').strip()
            if "Pesan : " in raw_data:
                msg = raw_data.split("Pesan : ")[1].strip()
                
                # Cek jika ada info Total dari Arduino
                if "|" in msg and "Total" in msg:
                    parts = msg.split("|")
                    status_text = parts[0].strip()
                    count_text = parts[1].replace("Total:", "").strip()
                    label.config(text=status_text)
                    label_counter.config(text=f"Kendaraan Lewat: {count_text}")
                else:
                    # Jika Arduino cuma kirim "Berhasil", Python hitung sendiri
                    label.config(text=msg)
                    if "Berhasil" in msg:
                        kendaraan_count += 1
                        label_counter.config(text=f"Kendaraan Lewat: {kendaraan_count}")

                # --- Logika Warna ---
                if "Berhasil" in msg:
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
root.title("Toll Gate Dash")
root.geometry("800x600")
root.config(bg="#ffffff")

label = tk.Label(root, text="Tap Kartu E-Toll", font=("Arial", 50, "bold"), bg="#ffffff", fg="#2c3e50")
label.pack(expand=True, fill='both')

label_counter = tk.Label(root, text="Kendaraan Lewat: 0", font=("Arial", 20, "bold"), bg="#2c3e50", fg="white", pady=10)
label_counter.pack(side="bottom", fill="x")

update_label()
root.mainloop()

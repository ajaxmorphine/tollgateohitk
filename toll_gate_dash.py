import serial
import tkinter as tk

try:
    ser = serial.Serial('COM12', 9600, timeout=1) 
except Exception as e:
    print(f"Gagal koneksi: {e}. Pastikan COM port benar!")
    exit()

def update_label():
    if ser.in_waiting > 0:
        try:
            raw_data = ser.readline().decode('utf-8').strip()
            if "Pesan : " in raw_data:
                msg = raw_data.split("Pesan : ")[1]
                label.config(text=msg)
                
                # Logika Warna Dashboard
                if "Berhasil" in msg:
                    root.config(bg="#2ecc71")
                    label.config(bg="#2ecc71", fg="white")
                elif "Gagal" in msg or "Peringatan" in msg:
                    root.config(bg="#e74c3c")
                    label.config(bg="#e74c3c", fg="white")
                elif "Tap Kartu E-Toll" in msg:
                    root.config(bg="#f1c40f") # Kuning cerah agar kontras saat idle
                    label.config(bg="#f1c40f", fg="#2c3e50")
        except:
            pass
            
    root.after(100, update_label)

root = tk.Tk()
root.title("DASHBOARD GERBANG TOL - WINDOWS MODE")
root.geometry("800x600")

label = tk.Label(root, text="Tap Kartu E-Toll", font=("Arial", 50, "bold"))
label.pack(expand=True, fill='both')

update_label()
root.mainloop()
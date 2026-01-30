import asyncio
import json
import serial
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from toll_database import TollDatabase

# Inisialisasi FastAPI dan Database
app = FastAPI()
db = TollDatabase()

# --- KONFIGURASI SERIAL (Diambil dari toll_gate_dash.py) ---
try:
    # Sesuaikan COM port dengan yang ada di toll_gate_dash.py
    ser = serial.Serial('COM12', 9600, timeout=0.1)
except Exception as e:
    print(f"Gagal koneksi Serial: {e}")
    ser = None

# Manager untuk mengelola koneksi browser (WebSocket)
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        # Kirim data awal saat browser baru dibuka
        await self.send_initial_data(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_initial_data(self, websocket: WebSocket):
        history = db.fetch_all_data()
        # Ambil 5 data terakhir, format untuk JSON
        formatted_history = [{"waktu": r[1], "id_kartu": r[2]} for r in reversed(history[-5:])]
        await websocket.send_text(json.dumps({
            "type": "init_data",
            "count": db.get_last_id(),
            "history": formatted_history
        }))

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                pass

manager = ConnectionManager()

# --- BACKGROUND TASK: MEMBACA SERIAL ARDUINO ---
async def read_serial_task():
    while True:
        if ser and ser.in_waiting > 0:
            try:
                raw_data = ser.readline().decode('utf-8').strip()
                if "Pesan : " in raw_data:
                    msg = raw_data.split("Pesan : ")[1].strip()
                    
                    # Logika simpan data (sama seperti di toll_gate_dash.py)
                    if "Berhasil" in msg:
                        db.insert_data("E-TOLL-USER")
                    
                    # Kirim notifikasi ke browser secara real-time
                    await manager.broadcast({
                        "type": "status_update",
                        "message": msg
                    })
            except Exception as e:
                print(f"Error pembacaan serial: {e}")
        await asyncio.sleep(0.1)

@app.on_event("startup")
async def startup_event():
    # Jalankan pembaca serial di latar belakang
    asyncio.create_task(read_serial_task())

# --- ROUTES API ---

@app.get("/")
async def get():
    # Menampilkan file index.html (Canvas)
    with open("index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@app.get("/data")
async def get_latest_data():
    # Endpoint untuk refresh data manual
    history = db.fetch_all_data()
    return {
        "count": db.get_last_id(),
        "history": [{"waktu": r[1], "id_kartu": r[2]} for r in reversed(history[-5:])]
    }

@app.post("/command/{cmd}")
async def send_command_to_arduino(cmd: str):
    # Mengirim perintah E (Emergency) atau R (Reset) ke Arduino
    if ser:
        ser.write(cmd.encode())
        return {"status": "success", "command": cmd}
    return {"status": "error", "message": "Serial not connected"}

@app.delete("/clear")
async def clear_database_records():
    # Menghapus riwayat di database
    if db.clear_table():
        return {"status": "success"}
    return {"status": "error"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Tetap jaga koneksi terbuka
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
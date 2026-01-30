import asyncio
import json
import serial
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from toll_database import TollDatabase

# Konfigurasi Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inisialisasi FastAPI dan Database
app = FastAPI()
db = TollDatabase()

# --- KONFIGURASI SERIAL ---
SERIAL_PORT = 'COM12' # Sesuaikan dengan port Arduino kamu
BAUD_RATE = 9600

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
    logger.info(f"Terhubung ke Arduino di {SERIAL_PORT}")
except Exception as e:
    logger.error(f"Gagal koneksi Serial: {e}")
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
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_initial_data(self, websocket: WebSocket):
        try:
            history = db.fetch_all_data() or []
            # Format: id=0, timestamp=1, card_id=2 sesuai toll_database.py
            formatted_history = [{"waktu": r[1], "id_kartu": r[2]} for r in reversed(history[-5:])]
            
            await websocket.send_text(json.dumps({
                "type": "init_data",
                "count": db.get_last_id(),
                "history": formatted_history
            }))
        except Exception as e:
            logger.error(f"Error sending init data: {e}")

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                pass

manager = ConnectionManager()

# --- BACKGROUND TASK: MEMBACA SERIAL ARDUINO ---
async def read_serial_task():
    while True:
        if ser and ser.is_open:
            try:
                if ser.in_waiting > 0:
                    raw_line = ser.readline().decode('utf-8', errors='ignore').strip()
                    if not raw_line:
                        continue
                        
                    logger.info(f"Arduino: {raw_line}")

                    # Logika deteksi pesan dari Arduino
                    # Contoh format: "Pesan : Akses Berhasil" atau "Pesan : Saldo Kurang"
                    if "Pesan : " in raw_line:
                        msg = raw_line.split("Pesan : ")[1].strip()
                        
                        # Jika berhasil, simpan ke database
                        if "berhasil" in msg.lower():
                            db.insert_data("E-TOLL-USER")
                            # Kirim update data terbaru (counter & tabel) setelah insert
                            history = db.fetch_all_data() or []
                            formatted_history = [{"waktu": r[1], "id_kartu": r[2]} for r in reversed(history[-5:])]
                            await manager.broadcast({
                                "type": "init_data",
                                "count": db.get_last_id(),
                                "history": formatted_history
                            })
                        
                        # Kirim status update untuk animasi (Layar Hijau/Merah)
                        await manager.broadcast({
                            "type": "status_update",
                            "message": msg
                        })
            except Exception as e:
                logger.error(f"Error reading serial: {e}")
        
        await asyncio.sleep(0.05) # Delay kecil agar tidak membebani CPU

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(read_serial_task())

# --- ROUTES API ---

@app.get("/")
async def get():
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    except FileNotFoundError:
        return HTMLResponse("File index.html tidak ditemukan.", status_code=404)

@app.get("/data")
async def get_latest_data():
    history = db.fetch_all_data() or []
    return {
        "count": db.get_last_id(),
        "history": [{"waktu": r[1], "id_kartu": r[2]} for r in reversed(history[-5:])]
    }

@app.post("/command/{cmd}")
async def send_command_to_arduino(cmd: str):
    if ser and ser.is_open:
        # Arduino biasanya butuh karakter tunggal seperti 'E' atau 'R'
        ser.write(cmd.encode())
        return {"status": "success", "command": cmd}
    return {"status": "error", "message": "Serial tidak terhubung"}

@app.delete("/clear")
async def clear_database_records():
    if db.clear_table():
        # Beritahu semua client bahwa data sudah kosong
        await manager.broadcast({
            "type": "init_data",
            "count": 0,
            "history": []
        })
        return {"status": "success"}
    return {"status": "error"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text() # Menjaga koneksi
    except WebSocketDisconnect:
        manager.disconnect(websocket)

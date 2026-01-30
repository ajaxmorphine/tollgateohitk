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

app = FastAPI()
db = TollDatabase()

# --- KONFIGURASI SERIAL ---
SERIAL_PORT = 'COM12' 
BAUD_RATE = 9600

try:
    # Timeout kecil agar pembacaan tidak memblokir loop async
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
    logger.info(f"Terhubung ke Arduino di {SERIAL_PORT}")
except Exception as e:
    logger.error(f"Gagal koneksi Serial: {e}")
    ser = None

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        await self.send_initial_data(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_initial_data(self, websocket: WebSocket):
        try:
            history = db.fetch_all_data() or []
            formatted_history = [{"waktu": r[1], "id_kartu": r[2]} for r in reversed(history[-5:])]
            await websocket.send_text(json.dumps({
                "type": "init_data",
                "count": db.get_last_id(),
                "history": formatted_history
            }))
        except Exception as e:
            logger.error(f"Error init data: {e}")

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                pass

manager = ConnectionManager()

# --- TASK: MEMBACA DATA DARI ARDUINO ---
async def read_serial_task():
    while True:
        if ser and ser.is_open:
            try:
                if ser.in_waiting > 0:
                    raw_line = ser.readline().decode('utf-8', errors='ignore').strip()
                    if not raw_line: continue
                    
                    logger.info(f"Arduino says: {raw_line}")

                    if "Pesan :" in raw_line:
                        msg = raw_line.split("Pesan :")[1].strip()
                        
                        # Trigger database simpan jika Arduino mengirim pesan Berhasil
                        if "Berhasil" in msg:
                            # Mengambil ID kartu dari baris sebelumnya jika perlu, 
                            # atau gunakan dummy user jika Arduino tidak mengirim UID spesifik di baris yang sama
                            db.insert_data("E-TOLL-USER") 
                            
                            history = db.fetch_all_data() or []
                            formatted_history = [{"waktu": r[1], "id_kartu": r[2]} for r in reversed(history[-5:])]
                            
                            await manager.broadcast({
                                "type": "init_data",
                                "count": db.get_last_id(),
                                "history": formatted_history
                            })
                        
                        # Kirim update status ke UI (Warna Hijau/Merah/Orange)
                        await manager.broadcast({
                            "type": "status_update",
                            "message": msg
                        })

            except Exception as e:
                logger.error(f"Serial Read Error: {e}")
        
        await asyncio.sleep(0.05)

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
        return HTMLResponse("index.html missing", status_code=404)

@app.post("/command/{cmd}")
async def send_command(cmd: str):
    if ser and ser.is_open:
        try:
            # Arduino menggunakan Serial.read() (char tunggal)
            # Kirim 'E' atau 'R' langsung tanpa \n agar buffer bersih
            ser.write(cmd.encode()) 
            ser.flush() 
            
            # Broadcast lokal agar UI langsung merespon tanpa nunggu feedback serial
            status_msg = "Emergency Mode" if cmd == 'E' else "System Reset"
            await manager.broadcast({
                "type": "status_update",
                "message": status_msg
            })

            return {"status": "success"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    return {"status": "error", "message": "Serial Disconnected"}

@app.delete("/clear")
async def clear_database():
    if db.clear_table():
        # Beritahu semua client bahwa data sudah nol
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
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

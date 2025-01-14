# serializers views look at some high level structure 
from fastapi import FastAPI, HTTPException, File, UploadFile, WebSocket, WebSocketDisconnect
from typing import List
from pydantic import BaseModel
import sqlite3
import jwt
#  some warning msg saying globally installed jwt which may cause conflict, create virtual environment?
#  why use virtual environments?
# this is a python issue so you need a virtual environment to avoid version confilcts
from datetime import datetime, timedelta
# can use bcrypt for hashing the password since its a good practice
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
import logging
from PIL import Image
from io import BytesIO
import base64

app = FastAPI()
# does this have to be app? its syntax

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Be cautious in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = "users.db"
FILES_DATABASE_URL = "files.db"
SECRET_KEY = "my_secret_key"
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 30

class User(BaseModel):
    username: str
    password: str

def init_db():
    conn= sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT NOT NULL,
            password TEXT NOT NULL
            )
        ''')
    conn.commit()
    conn.close()

def init_files_db():
    conn = sqlite3.connect(FILES_DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                content_type TEXT NOT NULL,
                data BLOB NOT NULL
                )
         ''')  
    conn.commit()
    conn.close()  

init_db()
# we have already initialized the database so later why open and close connections?
init_files_db()

# ----------------------------------------------------------------------------------------------
@app.post("/register")
async def register_user(user: User):
    # Connect to the database
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()

    # Check if the username already exists
    cursor.execute("SELECT * FROM users WHERE username = ?", (user.username,))
    existing_user = cursor.fetchone()

    if existing_user:
        conn.close()
        raise HTTPException(status_code=400, detail="Username already exists")

    # Insert the new user into the database
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (user.username, user.password))
    conn.commit()
    conn.close()

    return {"message": "User registered successfully"}
# --------------------------------------------------------------------------------------------------------

@app.post("/api/user/login")
async def login_user(user : User):
    conn= sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    # can i just keep the connection open why for both sides: good practice since sqlite is really bad with concurrency so if multiple 
    # connections try to access the database at the same time it the result is 

    # we have to also make sure that usernames (and passwords) do not repeat

    cursor.execute("SELECT password FROM users WHERE username = ?", (user.username,))
    existing_user = cursor.fetchone()

    if not existing_user:
        conn.close()
        raise HTTPException(status_code=404, detail="Username not found")

    if existing_user[0] != user.password:
        conn.close()
        raise HTTPException(status_code=401, detail="Invalid password")

    conn.close()
    message = "Correct password"

    payload_data = {
        "sub": user.username,
        "exp": datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    }

    token = jwt.encode(payload=payload_data, key=SECRET_KEY, algorithm=ALGORITHM)

    return {
        "message": message,
        "access_token": token,
        "token_type": "bearer"
    }
# --------------------------------------------------------------------------------------------------------

@app.post("/api/user/upload-files")
async def upload_files(files: List[UploadFile]=File(...)):
    conn = sqlite3.connect(FILES_DATABASE_URL)
    cursor = conn.cursor()

    for file in files:
        if not(file.filename.endswith("jpeg") or file.filename.endswith("jpg")):
            raise HTTPException(status_code=400, detail=f"{file.filename} is not a .jpeg or .jpg file")
        
        file_content = await file.read()   

        cursor.execute('''
            INSERT INTO files (filename, content_type, data)
            VALUES(?, ?, ?) 
            ''', (file.filename, file.content_type, file_content)) 
        conn.commit()  

    conn.close()
    return{"message": f"{len(files)} files(s) uploaded successfully"} 

# UploadFile has the following async methods. They all call the corresponding file methods underneath (using the internal SpooledTemporaryFile).

# write(data): Writes data (str or bytes) to the file.
# read(size): Reads size (int) bytes/characters of the file.
# seek(offset): Goes to the byte position offset (int) in the file.
#   E.g., await myfile.seek(0) would go to the start of the file.
#   This is especially useful if you run await myfile.read() once and then need to read the contents again. here how to determine where
#   it stopped reading.
# close(): Closes the file.
# remember advantages of using UploadFile over File.

# --------------------------------------------------------------------------------------------------------

@app.websocket("/api/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Server received: {data}")
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.close()

# --------------------------------------------------------------------------------------------------------

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# --------------------------------------------------------------------------------------------------------

# class ConnectionManager:
#     def __init__(self):
#         self.active_connections: List[WebSocket] = []

#     async def connect(self, websocket: WebSocket):
#         await websocket.accept()
#         self.active_connections.append(websocket)

#     def disconnect(self, websocket: WebSocket):
#         self.active_connections.remove(websocket)

#     async def broadcast(self, frame: bytes):
#         for connection in self.active_connections:
#             try:
#                 await connection.send_bytes(frame)
#             except:
#                 print("Error sending frame")

# manager = ConnectionManager()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        
    async def connect(self, websocket: WebSocket):
        try:
            await websocket.accept()
            self.active_connections.append(websocket)
            logging.info(f"New client connected. Total connections: {len(self.active_connections)}")
        except Exception as e:
            logging.error(f"Error during connection: {str(e)}")
            
    def disconnect(self, websocket: WebSocket):
        try:
            self.active_connections.remove(websocket)
            logging.info(f"Client disconnected. Remaining connections: {len(self.active_connections)}")
        except Exception as e:
            logging.error(f"Error during disconnection: {str(e)}")
            
    async def broadcast(self, frame: bytes):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_bytes(frame)
            except Exception as e:
                logging.error(f"Error broadcasting frame: {str(e)}")
                disconnected.append(connection)
                
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

# --------------------------------------------------------------------------------------------------------

# @app.websocket("/api/ws/video")
# async def websocket_endpoint(websocket: WebSocket):
#     await manager.connect(websocket)
#     try:
#         while True:
#             try:
#                 data = await websocket.receive_bytes()
#                 frame_size = len(data)
#                 logging.info(f"Received frame of size: {frame_size} bytes")
                
#                 # Send confirmation back to client
#                 response_message = f"Frame received: {frame_size} bytes"
#                 await websocket.send_text(response_message)
                
#                 # Broadcast frame to other clients if needed
#                 # await manager.broadcast(data)
                
#             except Exception as e:
#                 logging.error(f"Error processing frame: {str(e)}")
#                 break
                
#     except WebSocketDisconnect:
#         manager.disconnect(websocket)
#         logging.info("Client disconnected due to WebSocket disconnect")
#     except Exception as e:
#         logging.error(f"Unexpected error: {str(e)}")
#         manager.disconnect(websocket)

@app.websocket("/api/ws/video")
async def video_stream(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket connection opened")

    try:
        while True:
            # Receive the base64 encoded image data
            data = await websocket.receive_text()
            print("Received image data")

            # Decode the image from base64 string
            image_data = base64.b64decode(data)

            # Convert the binary image data to a Pillow Image object
            image = Image.open(BytesIO(image_data))

            # Optionally, save the image or process it
            # image.save("received_image.jpg")  # Save to disk for debugging

            # Send an acknowledgment message back to the client
            await websocket.send_text("Image received and processed")

    except WebSocketDisconnect:
        print("WebSocket connection closed")

# --------------------------------------------------------------------------------------------------------

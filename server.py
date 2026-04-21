import socket
import threading
import sqlite3
from datetime import datetime

HOST = '0.0.0.0'
PORT = 5050

clients = []

conn = sqlite3.connect('chat.db', check_same_thread=False)
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    message TEXT,
    time TEXT
)
''')
conn.commit()

def broadcast(message):
    for client in list(clients):
        try:
            client.send(message)
        except:
            if client in clients:
                clients.remove(client)

def handle_client(client):
    username = client.recv(1024).decode()
    print(f"{username} joined")

    c.execute("SELECT username, message, time FROM messages")
    rows = c.fetchall()

    for row in rows:
        old_msg = f"[{row[2]}] [{row[0]}] > {row[1]}"
        client.send((old_msg + "\n").encode())

    while True:
        try:
            msg = client.recv(1024).decode()

            if not msg:
                break

            time_now = datetime.now().strftime("%H:%M:%S")

            
            c.execute(
                "INSERT INTO messages (username, message, time) VALUES (?, ?, ?)",
                (username, msg, time_now)
            )
            conn.commit()

            full_msg = f"[{time_now}] [{username}] > {msg}"
            print(full_msg)

            
            broadcast((full_msg + "\n").encode())

        except:
            if client in clients:
                clients.remove(client)
            client.close()
            break

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()

    print(f"Server running on {HOST}:{PORT}")

    while True:
        client, addr = server.accept()
        print(f"Connected: {addr}")

        clients.append(client)

        thread = threading.Thread(target=handle_client, args=(client,))
        thread.start()

start_server()
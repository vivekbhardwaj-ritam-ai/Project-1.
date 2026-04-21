from flask import Flask, render_template, request
from flask_socketio import SocketIO, send
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*", max_http_buffer_size=100_000_000)

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

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def connect():
    username = request.args.get('username')
    print(f"User connected: {username}")
    c.execute("SELECT username, message, time FROM messages")
    rows = c.fetchall()
    for row in rows:
        old_msg = f"[{row[0]}] > {row[1]}"
        send(old_msg)
    
    if username:
        bot_msg = f"{username} joined the chat!"
        time_now = datetime.now().strftime("%H:%M:%S")
        c.execute(
            "INSERT INTO messages (username, message, time) VALUES (?, ?, ?)",
            ("Bot", bot_msg, time_now)
        )
        conn.commit()
        send(f"[Bot] > {bot_msg}", broadcast=True)

@socketio.on('message')
def handle_message(msg):
    username = request.args.get('username', 'Anonymous')
    time_now = datetime.now().strftime("%H:%M:%S")

    c.execute(
        "INSERT INTO messages (username, message, time) VALUES (?, ?, ?)",
        (username, msg, time_now)
    )
    conn.commit()

    full_msg = f"[{username}] > {msg}"
    print(full_msg)

    send(full_msg, broadcast=True)

    # Simple Bot AI Logic
    msg_lower = msg.lower().strip()
    bot_reply = None
    
    if msg_lower in ['hi', 'hello', 'hi bot', 'hello bot']:
        bot_reply = f"Hello {username}!"
    elif msg_lower == 'who are you?' or msg_lower == 'who are you':
        bot_reply = "I am a simple Bot here to help."
    elif msg_lower == 'help':
        bot_reply = "You can say 'hi', ask 'who are you?', or ask for the 'time'."
    elif 'time' in msg_lower:
        bot_reply = f"The current server time is {time_now}."

    if bot_reply:
        bot_time = datetime.now().strftime("%H:%M:%S")
        c.execute(
            "INSERT INTO messages (username, message, time) VALUES (?, ?, ?)",
            ("Bot", bot_reply, bot_time)
        )
        conn.commit()
        send(f"[Bot] > {bot_reply}", broadcast=True)

@socketio.on('image')
def handle_image(data):
    username = request.args.get('username', 'Anonymous')
    time_now = datetime.now().strftime("%H:%M:%S")

    # Handle both raw data (old format) and object with metadata (new format)
    if isinstance(data, dict):
        img_url = data.get('image')
        orig_size = data.get('originalSize', 0)
        comp_size = data.get('compressedSize', 0)
        lost_size = orig_size - comp_size
        reduction = round((1 - comp_size/orig_size)*100) if orig_size > 0 else 0
        
        # Format a richer message with reconstruction stats including lost data
        img_message = (
            f"<div class='image-rcvd'>"
            f"<img src='{img_url}' style='max-width: 280px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1);' />"
            f"<div style='font-size: 10px; color: #94a3b8; margin-top: 5px; font-family: monospace;'>"
            f"RECONSTRUCTION: {reduction}% reduction | Original: {orig_size}KB | Lost: {lost_size}KB"
            f"</div></div>"
        )
    else:
        # Fallback for old clients
        img_message = f"<br><img src='{data}' style='max-width: 200px; border-radius: 8px; margin-top: 5px;' />"
    
    c.execute(
        "INSERT INTO messages (username, message, time) VALUES (?, ?, ?)",
        (username, img_message, time_now)
    )
    conn.commit()

    full_msg = f"[{username}] > {img_message}"
    print(f"[{username}] sent an image ({'compressed' if isinstance(data, dict) else 'raw'}).")

    send(full_msg, broadcast=True)

@socketio.on('audio')
def handle_audio(data):
    username = request.args.get('username', 'Anonymous')
    time_now = datetime.now().strftime("%H:%M:%S")

    # Wrap audio in a styled player
    audio_message = (
        f"<div class='audio-rcvd'>"
        f"<div style='font-size: 11px; color: #94a3b8; margin-bottom: 5px;'>Voice Message</div>"
        f"<audio controls style='height: 35px; border-radius: 20px; outline: none;'>"
        f"<source src='{data}' type='audio/mpeg'>"
        f"Your browser does not support the audio element."
        f"</audio>"
        f"</div>"
    )
    
    c.execute(
        "INSERT INTO messages (username, message, time) VALUES (?, ?, ?)",
        (username, audio_message, time_now)
    )
    conn.commit()

    full_msg = f"[{username}] > {audio_message}"
    print(f"[{username}] sent an audio message.")

    send(full_msg, broadcast=True)

@socketio.on('clear_chat')
def handle_clear_chat():
    username = request.args.get('username', 'Anonymous')
    c.execute("DELETE FROM messages")
    conn.commit()
    print(f"[{username}] cleared the chat history.")
    socketio.emit('chat_cleared')

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=5050, debug=True, allow_unsafe_werkzeug=True)
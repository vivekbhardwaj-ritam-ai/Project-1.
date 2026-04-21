import socket
import threading

HOST = input("Enter server IP: ")
PORT = 5050

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

username = input("Enter your name: ")
client.send(username.encode())

def receive():
    while True:
        try:
            msg = client.recv(1024).decode()
            print(msg)
        except:
            break

def send():
    while True:
        msg = input()
        client.send(msg.encode())

threading.Thread(target=receive).start()
threading.Thread(target=send).start()
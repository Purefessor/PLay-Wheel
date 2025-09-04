import http.server
import socketserver
import json
import os
import threading
import socket
import requests
import time

# --- Configuration ---
PORT = 8000
DATA_FILE = os.environ.get("DATA_FILE_PATH", "data.json")

# Twitch Credentials from Environment Variables (set this up on Railway)
TWITCH_OAUTH_TOKEN = os.environ.get("TWITCH_OAUTH_TOKEN")
BOT_USERNAME = os.environ.get("BOT_USERNAME")
CHANNEL_NAME = os.environ.get("CHANNEL_NAME")

# --- Web Server Handler ---
class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/add_participant':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = json.loads(self.rfile.read(content_length))
                new_participant = post_data.get("name")
                
                if new_participant:
                    with open(DATA_FILE, 'r') as f:
                        data = json.load(f)
                    
                    if new_participant not in [p['name'] for p in data['participants']]:
                        data['participants'].append({"name": new_participant})
                        
                        with open(DATA_FILE, 'w') as f:
                            json.dump(data, f, indent=4)
                        
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(b'{"status": "success", "message": "Participant added"}')
                    else:
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(b'{"status": "info", "message": "Participant already on wheel"}')
                else:
                    self.send_response(400)
                    self.end_headers()
            except Exception as e:
                print(f"Error processing /add_participant: {e}")
                self.send_response(500)
                self.end_headers()
        
        elif self.path == '/update_participants':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                
                with open(DATA_FILE, 'wb') as f:
                    f.write(post_data)
                    
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"status": "success", "message": "Data updated"}')
            except Exception as e:
                print(f"Error processing /update_participants: {e}")
                self.send_response(500)
                self.end_headers()
        else:
            super().do_POST()

    def do_GET(self):
        super().do_GET()

# --- Chat Bot Logic ---
def chat_bot_thread():
    if not TWITCH_OAUTH_TOKEN or not BOT_USERNAME or not CHANNEL_NAME:
        print("Twitch credentials not set as environment variables. Chat bot disabled.")
        return

    SERVER_ADDR = "irc.chat.twitch.tv"
    PORT_ADDR = 6667
    
    def send_chat_message(sock, message):
        sock.send(f"PRIVMSG #{CHANNEL_NAME} :{message}\r\n".encode("utf-8"))

    def add_participant_to_wheel(name):
        print(f"Attempting to add {name} to the wheel...")
        payload = {"name": name}
        try:
            # We call our own server now
            requests.post(f"http://localhost:{PORT}/add_participant", json=payload)
            print(f"Successfully added {name} to the wheel.")
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to server: {e}")

    while True:
        try:
            sock = socket.socket()
            sock.connect((SERVER_ADDR, PORT_ADDR))
            
            sock.send(f"PASS {TWITCH_OAUTH_TOKEN}\r\n".encode("utf-8"))
            sock.send(f"NICK {BOT_USERNAME}\r\n".encode("utf-8"))
            sock.send(f"JOIN #{CHANNEL_NAME}\r\n".encode("utf-8"))
            
            print("Chat bot is connected and listening for !join commands.")
            
            while True:
                response = sock.recv(2048).decode("utf-8")
                
                if response.startswith("PING"):
                    sock.send("PONG\r\n".encode("utf-8"))
                    
                if "PRIVMSG" in response:
                    parts = response.split(":", 2)
                    if len(parts) < 3:
                        continue
                    
                    user = parts[1].split("!")[0]
                    message = parts[2].strip()
                    
                    if message.lower().startswith("!join"):
                        print(f"[{user}] wants to join!")
                        add_participant_to_wheel(user)
                        
        except socket.error as e:
            print(f"Socket error: {e}. Attempting to reconnect in 5 seconds...")
            time.sleep(5)
        except Exception as e:
            print(f"An error occurred: {e}. Attempting to reconnect in 5 seconds...")
            time.sleep(5)

# --- Main execution block ---
if __name__ == "__main__":
    # Ensure data.json exists to avoid initial errors
    if not os.path.exists(DATA_FILE):
        initial_data = {
            "participants": [],
            "prizeImageSrc": "https://placehold.co/300x300/10b981/ffffff?text=Prize"
        }
        with open(DATA_FILE, 'w') as f:
            json.dump(initial_data, f, indent=4)
            
    # Start the chat bot in a separate thread
    bot_thread = threading.Thread(target=chat_bot_thread)
    bot_thread.daemon = True  # Daemon threads exit when the main program exits
    bot_thread.start()
    
    # Start the web server in the main thread
    with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
        print(f"serving at port {PORT}")
        httpd.serve_forever()
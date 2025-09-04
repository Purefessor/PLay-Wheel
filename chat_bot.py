import socket
import time
import requests

# Fill in your details below
TWITCH_OAUTH_TOKEN = "oauth:i9dwbiwze16o810f5rx9fureeb7s6m"
BOT_USERNAME = "purefessorlive"
CHANNEL_NAME = "purefessorlive"

SERVER = "irc.chat.twitch.tv"
PORT = 6667

def send_chat_message(sock, message):
    sock.send(f"PRIVMSG #{CHANNEL_NAME} :{message}\r\n".encode("utf-8"))

def add_participant_to_wheel(name):
    print(f"Attempting to add {name} to the wheel...")
    payload = {"name": name}
    try:
        response = requests.post("http://localhost:8000/add_participant", json=payload)
        if response.status_code == 200:
            print(f"Successfully added {name} to the wheel.")
        else:
            print(f"Failed to add {name}. Server response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to server: {e}")

# This bot uses a separate library, so you'll need to install it first.
# Open a new terminal and run: pip install requests
try:
    import requests
except ImportError:
    print("The 'requests' library is not installed.")
    print("Please install it by running 'pip install requests' in your terminal.")
    exit()

if __name__ == "__main__":
    sock = socket.socket()
    sock.connect((SERVER, PORT))
    
    sock.send(f"PASS {TWITCH_OAUTH_TOKEN}\r\n".encode("utf-8"))
    sock.send(f"NICK {BOT_USERNAME}\r\n".encode("utf-8"))
    sock.send(f"JOIN #{CHANNEL_NAME}\r\n".encode("utf-8"))
    
    print("Bot is connected and listening for !join commands.")
    
    while True:
        try:
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
            print(f"Socket error: {e}")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            break
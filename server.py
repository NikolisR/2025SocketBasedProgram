import socket
import select
import random
import time
import threading

HOST = '0.0.0.0'
PORT = 5555

# ——— Setup listening socket ———
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen()
print(f"[+] Server listening on {HOST}:{PORT}")

clients = {}     # sock -> player name
host_sock = None # first connector becomes host

def broadcast(msg):
    for s in list(clients):
        try:
            s.sendall(msg.encode())
        except:
            remove_client(s)

def remove_client(s):
    name = clients.pop(s, None)
    try: s.close()
    except: pass
    if name:
        broadcast(f"LOBBY:{','.join(clients.values())}\n")

# ——— Lobby & Host Selection ———
while True:
    rlist, _, _ = select.select([server] + list(clients), [], [])
    for s in rlist:
        if s is server:
            conn, _ = server.accept()
            name = conn.recv(1024).decode().strip()
            clients[conn] = name
            print(f"[+] {name} joined")
            if not host_sock:
                host_sock = conn
                conn.sendall("HOST:You are the host. Type 'start' to begin.\n".encode())
            else:
                conn.sendall("WAIT:Waiting for host to start...\n".encode())
            broadcast(f"LOBBY:{','.join(clients.values())}\n")

        else:
            try:
                data = s.recv(1024).decode().strip().lower()
            except:
                remove_client(s)
                continue

            if not data:
                remove_client(s)
            elif s is host_sock and data == 'start':
                print("[*] Host started the game")
                goto_game = True
                break
    else:
        continue
    break  # exit when host typed 'start'

# ——— Per-Client Challenges ———
WORDS = ['PYTHON', 'SOCKET', 'ENCRYPT', 'BATTLE', 'GAMING']
client_challenges = {}  # sock -> correct word

for s in list(clients):
    word  = random.choice(WORDS)
    shift = random.randint(1, 25)
    cipher = ''.join(
        chr((ord(c) - 65 + shift) % 26 + 65) if c.isalpha() else c
        for c in word
    )
    try:
        s.sendall(f"CHALLENGE:{cipher}|HINT:Caesar shift {shift}\n".encode())
    except:
        remove_client(s)
        continue
    client_challenges[s] = word

# ——— Start the round timer display thread ———
ROUND_TIME = 20
start_time = time.time()

def print_timer():
    while True:
        elapsed = time.time() - start_time
        remaining = int(ROUND_TIME - elapsed)
        if remaining < 0:
            break
        print(f"[Timer] {remaining} seconds remaining")
        time.sleep(1)

threading.Thread(target=print_timer, daemon=True).start()

# ——— Collect & Process Answers Immediately ———
waiting = set(client_challenges.keys())
results = {}  # name -> bool

while waiting and (time.time() - start_time) < ROUND_TIME:
    timeout = ROUND_TIME - (time.time() - start_time)
    rlist, _, _ = select.select(list(waiting), [], [], timeout)
    for s in rlist:
        try:
            data = s.recv(1024)
        except:
            remove_client(s)
            waiting.discard(s)
            continue

        if not data:
            remove_client(s)
            waiting.discard(s)
            continue

        ans = data.decode().strip().upper()
        correct = (ans == client_challenges.get(s))
        results[clients[s]] = correct

        feedback = "FEEDBACK:Correct!\n" if correct else f"FEEDBACK:Wrong! It was {client_challenges[s]}\n"
        try:
            s.sendall(feedback.encode())
        except:
            pass

        waiting.discard(s)

# ——— Time’s Up for Remaining Clients ———
for s in list(waiting):
    word = client_challenges.get(s)
    results[clients[s]] = False
    try:
        s.sendall(f"FEEDBACK:Time's up! It was {word}\n".encode())
    except:
        pass

# ——— Broadcast Final Leaderboard ———
lb = "LEADERBOARD:" + ",".join(
    f"{name}:{1 if correct else 0}"
    for name, correct in results.items()
) + "\n"
broadcast(lb)

# ——— Grace Period: keep sockets alive 10s so clients receive messages ———
print("[*] Round ended, keeping sockets open for 10 more seconds to deliver messages…")
time.sleep(10)

# ——— Clean Shutdown ———
for s in list(clients):
    try:
        s.shutdown(socket.SHUT_RDWR)
        s.close()
    except:
        pass

server.close()

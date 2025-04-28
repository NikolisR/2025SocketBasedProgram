import socket  # socket library usage for TCP connections!
import select  # multiplexing incoming sockets!
import random  # random challenge generation!
import time  # timing functions!
import threading  # timer display thread!

HOST = '0.0.0.0'
PORT = 5555

# Setup listening socket!
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen()
server.setblocking(False)  # non-blocking accept!
print(f"[+] Server listening on {HOST}:{PORT}")

clients = {}  # sock → player name!
scores = {}   # sock → cumulative score!
host_sock = None  # will hold host socket!

def broadcast(msg: str):
    for s in list(clients):
        try:
            s.sendall(msg.encode())
        except:
            pass

def remove_client(s):
    if s in clients:
        del clients[s]
    if s in scores:
        del scores[s]
    try:
        s.close()
    except:
        pass
    broadcast("LOBBY:" + ",".join(clients.values()) + "\n")

# — Lobby & manual start —
game_started = False
while not game_started:
    read_list, _, _ = select.select([server] + list(clients), [], [])
    for s in read_list:
        if s is server:
            try:
                conn, _ = server.accept()
            except BlockingIOError:
                continue
            name = conn.recv(1024).decode().strip()
            clients[conn] = name
            scores[conn] = 0
            conn.setblocking(False)
            print(f"[+] {name} joined (lobby)")
            if host_sock is None:
                host_sock = conn
                conn.sendall("HOST:You are the host. Type 'start' to begin.\n".encode())
            else:
                conn.sendall("WAIT:Waiting for host to start...\n".encode())
            broadcast("LOBBY:" + ",".join(clients.values()) + "\n")
        else:
            try:
                data = s.recv(1024).decode().strip().lower()
            except:
                remove_client(s)
                continue
            if not data:
                remove_client(s)
            elif s is host_sock and data == 'start':
                print("[*] Host typed start — beginning game")
                game_started = True
                break
    if game_started:
        break

# — Game loop: allow join mid-game & manual next —
NUM_ROUNDS = 5
ROUND_TIME = 20

for rnd in range(1, NUM_ROUNDS + 1):
    print(f"\n=== Round {rnd}/{NUM_ROUNDS} ===")

    # Inform clients of current lobby (including new joins)!
    broadcast("LOBBY:" + ",".join(clients.values()) + "\n")
    # 0) Inform clients of the round number!
    broadcast(f"ROUND:{rnd}\n")

    # 1) Send each existing player a unique cipher challenge!
    WORDS = ['PYTHON','SOCKET','ENCRYPT','BATTLE','GAMING']
    client_challenges = {}
    for s in list(clients):
        word = random.choice(WORDS)
        shift = random.randint(1, 25)
        cipher = ''.join(
            chr((ord(c) - 65 + shift) % 26 + 65) if c.isalpha() else c
            for c in word
        )
        try:
            s.sendall(f"CHALLENGE:{cipher}|HINT:Caesar shift {shift}\n".encode())
            client_challenges[s] = word
        except:
            remove_client(s)

    # 2) Start timer display thread!
    stop_evt = threading.Event()
    start_time = time.time()
    def timer():
        while not stop_evt.is_set():
            rem = ROUND_TIME - (time.time() - start_time)
            if rem <= 0:
                break
            print(f"[Timer] {int(rem)} seconds remaining")
            if stop_evt.wait(timeout=1):
                break
    threading.Thread(target=timer, daemon=True).start()

    # 3) Collect one answer per client, allow new joins in this window!
    responses = {}
    deadline = start_time + ROUND_TIME
    for s in client_challenges:
        s.setblocking(False)

    while time.time() < deadline and len(responses) < len(client_challenges):
        ready, _, _ = select.select([server] + list(client_challenges), [], [], deadline - time.time())
        for s in ready:
            if s is server:
                try:
                    conn, _ = server.accept()
                except BlockingIOError:
                    continue
                name = conn.recv(1024).decode().strip()
                clients[conn] = name
                scores[conn] = 0
                conn.setblocking(False)
                print(f"[+] {name} joined (mid-game)")
                conn.sendall("WAIT:Waiting for next round...\n".encode())
                broadcast("LOBBY:" + ",".join(clients.values()) + "\n")
            else:
                try:
                    data = s.recv(1024)
                except:
                    responses[s] = None
                else:
                    if data:
                        responses[s] = data.decode().strip().upper()
                    else:
                        responses[s] = None

    # 4) Mark any non-responders as None!
    for s in client_challenges:
        if s not in responses:
            responses[s] = None

    # 5) Stop timer!
    stop_evt.set()

    # 6) Send feedback & update scores!
    for s, word in client_challenges.items():
        ans = responses[s]
        if ans is None:
            msg = f"FEEDBACK:Time's up! It was {word}\n"
        elif ans == word:
            scores[s] += 1
            msg = "FEEDBACK:Correct!\n"
        else:
            msg = f"FEEDBACK:Wrong! It was {word}\n"
        try:
            s.sendall(msg.encode())
        except:
            pass

    # 7) Broadcast updated leaderboard!
    lb = "LEADERBOARD:" + ",".join(f"{clients[s]}:{scores[s]}" for s in clients) + "\n"
    broadcast(lb)

    # 8) Wait host for next round if any remain!
    if rnd < NUM_ROUNDS:
        host_sock.sendall("HOST:Type 'start' to begin next round\n".encode())
        host_sock.setblocking(True)
        while True:
            cmd = host_sock.recv(1024).decode().strip().lower()
            if cmd == 'start':
                break
        host_sock.setblocking(False)

# Final GAME OVER broadcast!
broadcast("GAME OVER! Thanks for playing!\n")
time.sleep(5)

# Clean shutdown!
for s in list(clients):
    try:
        s.close()
    except:
        pass
server.close()

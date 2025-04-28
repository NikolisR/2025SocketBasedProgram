import socket  # socket library usage for TCP connections!
import select  # multiplexing socket events!
import random  # random challenge generation!
import time    # timing functions!
import threading  # timer display thread!

HOST = '0.0.0.0'
PORT = 5555

NUM_ROUNDS = 5
ROUND_TIME = 20  # seconds per round!

def broadcast(clients, msg: str):
    """Send msg to every client in the dict."""
    for s in list(clients):
        try:
            s.sendall(msg.encode())
        except:
            pass

def remove_client(s, clients, scores):
    """Cleanup a disconnected client."""
    if s in clients:    del clients[s]
    if s in scores:     del scores[s]
    try:                s.close()
    except:             pass

# ——— Setup listening socket ———
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen()
server.setblocking(False)
print(f"[+] Server listening on {HOST}:{PORT}")

clients   = {}  # sock -> name
scores    = {}  # sock -> score
host_sock = None

while True:
    # reset scores each session
    for s in list(clients):
        scores[s] = 0
    game_started = False

    # — Lobby: wait for host to type 'start' —
    while not game_started:
        read_list, _, _ = select.select([server] + list(clients), [], [])
        for s in read_list:
            if s is server:
                # new connection
                try:
                    conn, _ = server.accept()
                except BlockingIOError:
                    continue
                name = conn.recv(1024).decode().strip()
                clients[conn] = name
                scores[conn] = 0
                conn.setblocking(False)
                print(f"[+] {name} joined lobby")

                if host_sock is None:
                    host_sock = conn
                    conn.sendall("HOST:You are the host. Type 'start' to begin.\n".encode())
                else:
                    conn.sendall("WAIT:Waiting for host to start...\n".encode())

                broadcast(clients, "LOBBY:" + ",".join(clients.values()) + "\n")

            else:
                # existing client typed something
                try:
                    data = s.recv(1024).decode().strip().lower()
                except:
                    remove_client(s, clients, scores)
                    continue

                if not data:
                    remove_client(s, clients, scores)
                elif s is host_sock and data == 'start':
                    print("[*] Host started the game")
                    game_started = True
                    break
        if game_started:
            break

    # — Game rounds —
    for rnd in range(1, NUM_ROUNDS + 1):
        print(f"=== Round {rnd}/{NUM_ROUNDS} ===")

        # broadcast lobby & round #
        broadcast(clients, "LOBBY:" + ",".join(clients.values()) + "\n")
        broadcast(clients, f"ROUND:{rnd}\n")

        # generate & send challenges
        WORDS = ['PYTHON','SOCKET','ENCRYPT','BATTLE','GAMING']
        client_challenges = {}
        for s in list(clients):
            word  = random.choice(WORDS)
            shift = random.randint(1,25)
            cipher = ''.join(
                chr((ord(c)-65 + shift) % 26 + 65) if c.isalpha() else c
                for c in word
            )
            try:
                s.sendall(f"CHALLENGE:{cipher}|HINT:Caesar shift {shift}\n".encode())
                client_challenges[s] = word
            except:
                remove_client(s, clients, scores)

        # start timer thread (for logs)
        stop_evt  = threading.Event()
        start_time = time.time()
        def timer():
            while not stop_evt.is_set():
                rem = ROUND_TIME - (time.time() - start_time)
                if rem <= 0:
                    break
                print(f"[Timer] {int(rem)}s remaining")
                if stop_evt.wait(timeout=1):
                    break
        threading.Thread(target=timer, daemon=True).start()

        # collect answers until timeout
        responses = {}
        deadline  = start_time + ROUND_TIME
        for s in client_challenges:
            s.setblocking(False)

        while time.time() < deadline and len(responses) < len(client_challenges):
            wait_list = [server] + list(client_challenges)
            ready, _, _ = select.select(wait_list, [], [], max(0, deadline - time.time()))
            for s in ready:
                if s is server:
                    # mid-game join
                    try:
                        conn, _ = server.accept()
                    except:
                        continue
                    name = conn.recv(1024).decode().strip()
                    clients[conn] = name
                    scores[conn] = 0
                    conn.setblocking(False)
                    conn.sendall("WAIT:Waiting for next round...\n".encode())
                    broadcast(clients, "LOBBY:" + ",".join(clients.values()) + "\n")
                else:
                    try:
                        data = s.recv(1024)
                    except:
                        responses[s] = None
                    else:
                        responses[s] = data.decode().strip().upper() if data else None

        # any who didn’t answer
        for s in client_challenges:
            if s not in responses:
                responses[s] = None
        stop_evt.set()

        # send feedback & update scores
        for s, word in client_challenges.items():
            ans = responses[s]
            if ans == word:
                scores[s] += 1
                msg = "FEEDBACK:Correct!\n"
            elif ans is None:
                msg = f"FEEDBACK:Time's up! It was {word}\n"
            else:
                msg = f"FEEDBACK:Wrong! It was {word}\n"
            try:
                s.sendall(msg.encode())
            except:
                pass

        # broadcast the leaderboard
        lb_msg = "LEADERBOARD:" + ",".join(f"{clients[s]}:{scores[s]}" for s in clients) + "\n"
        broadcast(clients, lb_msg)

        # ——— Two‐step host handshake ———
        # 1) Show the leaderboard
        host_sock.sendall("HOST:Type 'next' to show leaderboard\n".encode())
        host_sock.setblocking(True)
        while True:
            try:
                data = host_sock.recv(1024)
            except:
                continue
            if data and data.strip().lower() == b'next':
                break
        host_sock.setblocking(False)

        # broadcast NEXT to all clients
        broadcast(clients, "NEXT\n")

        # 2) If more rounds remain, wait for start
        if rnd < NUM_ROUNDS:
            host_sock.sendall("HOST:Type 'start' to begin next round\n".encode())
            host_sock.setblocking(True)
            while True:
                try:
                    data = host_sock.recv(1024)
                except:
                    continue
                if data and data.strip().lower() == b'start':
                    break
            host_sock.setblocking(False)

    # — Final Game Over —
    broadcast(clients, "HOST:Game over! Thanks for playing!\n")
    print("[*] Session ended, returning to lobby…")
    time.sleep(1)

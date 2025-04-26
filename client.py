import socket
import threading
import sys
import time

# msvcrt is Windows-only; for other OS you'd need a different timed-input approach
import msvcrt

HOST = input("Server IP (blank for localhost): ").strip() or "localhost"
PORT = 5555

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))

# 1) Send your name
name = input("Enter your name: ").strip()
sock.sendall(name.encode())

# ——— Shared state & Events ———
is_host            = False
first_lobby_seen   = threading.Event()
challenge_received = threading.Event()
leaderboard_recv   = threading.Event()
challenge_data     = {}

def recv_thread():
    global is_host, challenge_data
    buf = ""
    while True:
        try:
            data = sock.recv(4096).decode()
        except:
            print("\nConnection lost.")
            sys.exit()
        if not data:
            print("\nServer closed connection.")
            sys.exit()

        buf += data
        while "\n" in buf:
            line, buf = buf.split("\n", 1)
            line = line.strip()
            if not line:
                continue

            if line.startswith("HOST:"):
                is_host = True
                print("[HOST]", line.split("HOST:",1)[1].strip())

            elif line.startswith("WAIT:"):
                print("[WAIT]", line.split("WAIT:",1)[1].strip())

            elif line.startswith("LOBBY:"):
                players = line.split("LOBBY:",1)[1].split(",")
                print("\n*** Lobby Players ***")
                for p in players:
                    print(" •", p)
                print("*********************\n")
                first_lobby_seen.set()

            elif "CHALLENGE:" in line:
                part = line.split("CHALLENGE:",1)[1]
                if "|" in part:
                    ciph, hint_part = part.split("|",1)
                    challenge_data['cipher'] = ciph.strip()
                    challenge_data['hint']   = hint_part.split("HINT:",1)[1].strip()
                else:
                    challenge_data['cipher'] = part.strip()
                    challenge_data['hint']   = ""
                challenge_received.set()

            elif line.startswith("FEEDBACK:") or line.startswith("Time's up!"):
                # immediate feedback
                print("\n" + line.replace("FEEDBACK:", "").strip())

            elif line.startswith("LEADERBOARD:"):
                entries = line.split("LEADERBOARD:",1)[1].split(",")
                print("\n*** Leaderboard ***")
                for e in entries:
                    n,s = e.split(":")
                    print(f" • {n}: {s} point{'s' if s!='1' else ''}")
                print("*******************\n")
                leaderboard_recv.set()

            # ignore any other lines

def input_thread():
    # wait until lobby is first shown
    first_lobby_seen.wait()
    if is_host:
        print("You are the host. Type 'start' and press Enter to begin.")
        while not challenge_received.is_set():
            cmd = input().strip().lower()
            if cmd == "start":
                sock.sendall(cmd.encode())
                break
    else:
        first_lobby_seen.wait()
        print("Waiting for the host to start...\n")

# ——— Start background threads ———
threading.Thread(target=recv_thread, daemon=True).start()
threading.Thread(target=input_thread, daemon=True).start()

# ——— Wait for challenge ———
challenge_received.wait()
cipher = challenge_data['cipher']
hint   = challenge_data['hint']

# ——— Timed input for answer ———
print(f"\nCipher text: {cipher}")
print(f"Hint:        {hint}")
print("Your decryption (20s): ", end="", flush=True)

answer = ""
end_time = time.time() + 20
while time.time() < end_time:
    if msvcrt.kbhit():
        ch = msvcrt.getwch()
        if ch in ('\r','\n'):
            break
        answer += ch
        print(ch, end="", flush=True)
    time.sleep(0.01)

print()  # newline after input or timeout

# Send answer if any
if answer.strip():
    sock.sendall(answer.strip().upper().encode())

# ——— Wait for leaderboard (and you’ll have seen your FEEDBACK already) ———
leaderboard_recv.wait()

sock.close()
sys.exit()

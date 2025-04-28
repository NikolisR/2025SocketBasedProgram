import select, random, time, threading
from serverUtils import displayGUI, leaveEarlyHandler
from serverConstants import TOTALROUNDS, TIMER, WORDS

def runner(server):
    clients = {}
    scores = {}
    isHost = None

    while True:
        # Create a lobby and wait for join (Check game state)
        for s in list(clients):
            scores[s] = 0
        gameStatus = False

        # While the game states is not TRUE,
        # This lobby will accept connections and create a host. It will then display
        # the users who have joined the lobby
        while not gameStatus:
            read_list, _, _ = select.select([server] + list(clients), [], [])
            for s in read_list:
                if s is server:
                    # try to join the lobby
                    try:
                        conn, _ = server.accept()
                        name = conn.recv(1024).decode().strip()
                        clients[conn] = name
                        scores[conn] = 0
                        conn.setblocking(False)
                        print(f"[+] {name} joined lobby")

                        # if there is no host, make the first connection a host
                        if isHost is None:
                            isHost = conn
                            conn.sendall("HOST:You are the host. Type 'start' to begin.\n".encode())
                        else:
                            conn.sendall("WAIT:Waiting for host to start...\n".encode())
                        displayGUI(clients, "LOBBY:" + ",".join(clients.values()) + "\n")
                    except BlockingIOError:
                        continue

                # this handles if a player has disconnected
                else:
                    try:
                        raw = s.recv(1024)
                    except:
                        raw = b''
                    if not raw or raw.strip().lower() == b'quit':                                                       # checks if they closed there connection or quit
                        leaveEarlyHandler(s, clients, scores)
                        displayGUI(clients, "LOBBY:" + ",".join(clients.values()) + "\n")
                        continue
                    data = raw.decode().strip().lower()
                    if s is isHost and data == 'start':
                        print("[*] Host started the game")
                        gameStatus = True
                        break

        # Establish the rounds aand how they increment
        for currentRound in range(1, TOTALROUNDS + 1):
            print(f"=== Round {currentRound}/{TOTALROUNDS} ===")
            displayGUI(clients, "ROUND:" + f"{currentRound}/{TOTALROUNDS}\n")

            stop_evt = threading.Event()

            # When my round starts, make sure that a timer contdown starts
            def timerCountdown():
                for remaining in range(TIMER, -1, -1):
                    if stop_evt.is_set():
                        break
                    displayGUI(clients, f"TIME:{remaining}\n")
                    time.sleep(1)
            threading.Thread(target=timerCountdown, daemon=True).start()

            createdCipher = {}                                                                                          # create a cipher dictionary of the constant words in serverConstants
            for s in list(clients):
                word = random.choice(WORDS)
                shift = random.randint(1, 25)
                cipher = ''.join(
                    chr((ord(c)-65 + shift) % 26 + 65) if c.isalpha() else c
                    for c in word
                )
                try:
                    s.sendall(f"CHALLENGE:{cipher}|HINT:Caesar shift {shift}\n".encode())
                    createdCipher[s] = word
                except:
                    leaveEarlyHandler(s, clients, scores)


            # take in responses
            responses = {}
            deadline = time.time() + TIMER
            for s in createdCipher:
                s.setblocking(False)

            # while the round timer didn't finish or all answers haven't been recieved
            while time.time() < deadline and len(responses) < len(createdCipher):
                wait_list = [server] + list(createdCipher)                                                              # make a waitlist based on whom hasn't answered
                ready, _, _ = select.select(wait_list, [], [], max(0, deadline - time.time()))

                # this basically allows for new players and notifies the console that a player has joined.
                for s in ready:
                    if s is server:
                        try:
                            conn, _ = server.accept()
                            name = conn.recv(1024).decode().strip()
                            clients[conn] = name
                            scores[conn] = 0
                            conn.setblocking(False)
                            conn.sendall("WAIT:Waiting for next round...\n".encode())
                            displayGUI(clients, "LOBBY:" + ",".join(clients.values()) + "\n")
                        except:
                            continue
                    else:
                        try:
                            raw = s.recv(1024)
                        except:
                            raw = b''
                        if not raw or raw.strip().lower() == b'quit':
                            leaveEarlyHandler(s, clients, scores)
                            displayGUI(clients, "LOBBY:" + ",".join(clients.values()) + "\n")
                            responses[s] = None
                        else:
                            responses[s] = raw.decode().strip().upper()

            stop_evt.set()

            # if there are no reposes, make them none
            for s in createdCipher:
                if s not in responses:
                    responses[s] = None

            # When the earlier time is up, it will give Feedback on if the answer is correct or now
            for s, word in createdCipher.items():
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

            sortedSockets = sorted(clients, key=lambda sock: scores[sock], reverse=True)
            leaderboard = [f"{clients[sock]}:{scores[sock]}" for sock in sortedSockets]                                 # create a leaderboard via score
            displayGUI(clients, "LEADERBOARD:" + ",".join(leaderboard) + "\n")

            isHost.sendall("HOST:Type 'next' to show leaderboard\n".encode())
            isHost.setblocking(True)
            while isHost.recv(1024).strip().lower() != b'next':                                                         # wait for next to continue
                pass
            isHost.setblocking(False)

            displayGUI(clients, "NEXT\n")

            # if there is round remaining, wait for the host to start
            if currentRound < TOTALROUNDS:
                isHost.sendall("HOST:Type 'start' to begin next round\n".encode())
                isHost.setblocking(True)
                while isHost.recv(1024).strip().lower() != b'start':
                    pass
                isHost.setblocking(False)

        displayGUI(clients, "GG! Credits to Niko yea?!\n")
        time.sleep(1)

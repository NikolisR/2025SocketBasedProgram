def serverMessages(client, line):


    # This checks if the server needs to wait for anything.
    if line.startswith("WAIT:"):
        waitingMessage = line.split("WAIT:",1)[1].strip()
        client.frame_q.pack_forget()
        client.frame_lb.pack_forget()
        client.frame_lobby.pack(fill="both", expand=True, padx=20, pady=20)
        client.waitHost.set(waitingMessage)

    # If the server pings back HOST, then we are the host
    elif line.startswith("HOST:"):
        client.is_host = True
        client.start_btn.pack(pady=10)

    # If it pings back LOBBY, Update the lobby list and make sure the names are formatted correctly for splicing
    elif line.startswith("LOBBY:"):
        lobbyNames = line.split("LOBBY:",1)[1]
        client.lobbyPlayers.set(lobbyNames.replace(',', '\n'))
    # If it pings back ROUND, display what it is out of what in this format {X/Y}
    elif line.startswith("ROUND:"):
        currentRound, totalRounds = map(int, line.split(":",1)[1].split("/"))
        client.current_round = currentRound
        client.total_rounds  = totalRounds
        client.rndPlaceholder.set(f"Round {currentRound}/{totalRounds}")
    # If pings back TIME, Display the time (update the countdown)
    elif line.startswith("TIME:"):
        secondsRemaining = int(line.split("TIME:",1)[1])
        client.timerDisplay.set(f"Timer: {secondsRemaining}s")


    # If it pings back CHALLENGE, strip and create a new challenge with a little extra goodies
    elif line.startswith("CHALLENGE:"):
        _, challengePayload = line.split("CHALLENGE:",1)
        cipher, hint = challengePayload.split("|",1)
        client.frame_lobby.pack_forget()
        client.frame_lb.pack_forget()

        client.feedbackDisplay.set("")
        client.leaderboardDisplay.set("")
        client.waitHost.set("")
        client.lastSubmittion.set("")                                                                                   # remove old text in text box

        client.cipherDisplay.set(cipher.strip())                                                                        # Show new Cipher
        client.histDisplay.set(hint.split("HINT:",1)[1].strip())                                                        # show hint in shifts
        client.answer_entry.configure(state='normal')
        client.submit_btn.configure(state='normal')
        client.frame_q.pack(fill="both", expand=True, padx=20, pady=20)


    # If FEEDBACK Ping, send feedback if you got it right, wrong, etc
    elif line.startswith("FEEDBACK:") or line.startswith("Time's up!"):
        feedbackText = line.replace("FEEDBACK:", "").strip()
        client.feedbackDisplay.set(feedbackText)
        client.waitHost.set("")

        if client.is_host:
            client.feedback_next_btn.pack(pady=10)


    # This updates the leaderboards
    elif line.startswith("LEADERBOARD:"):
        leaderboardEntries = line.split("LEADERBOARD:",1)[1].split(",")
        client.leaderboardDisplay.set("\n".join(leaderboardEntries))

    elif line == "NEXT":
        client.displayLeaderboard()

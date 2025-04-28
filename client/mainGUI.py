import customtkinter as ctk

# Creates intial lobby frames and displays
def mainLobbyFrame(parent, lobbyPlayers, waitHost, startGame):
    frame = ctk.CTkFrame(parent)
    ctk.CTkLabel(frame, text="🛋️ Lobby Players", font=(None, 18)).pack(pady=(0,10))
    ctk.CTkLabel(frame, textvariable=lobbyPlayers, justify="left").pack(pady=(0,5))
    ctk.CTkLabel(frame, textvariable=waitHost, font=(None, 14), text_color="gray").pack(pady=(0,10))
    start_btn = ctk.CTkButton(frame, text="Start Game", command=startGame)
    return frame, start_btn


# Creates Challenge Frames
def questionFrame(parent, rndPlaceholder, cipherDisplay, histDisplay, timerDisplay, submit_command, waitHost, lastSubmittion, feedbackDisplay):
    frame = ctk.CTkFrame(parent)
    
    ctk.CTkLabel(frame, textvariable=rndPlaceholder, font=(None, 16)).pack(pady=(10,5))
    ctk.CTkLabel(frame, textvariable=cipherDisplay, font=(None, 24, 'bold')).pack(pady=5)
    ctk.CTkLabel(frame, textvariable=histDisplay, font=(None, 14)).pack(pady=5)
    ctk.CTkLabel(frame, textvariable=timerDisplay, font=(None, 14)).pack(pady=5)
    
    entry = ctk.CTkEntry(frame, placeholder_text="Type your answer here...")
    entry.pack(pady=10)
    
    submit_btn = ctk.CTkButton(frame, text="Submit", command=submit_command)
    submit_btn.pack(pady=5)
    
    ctk.CTkLabel(frame, textvariable=lastSubmittion, font=(None, 12), text_color="#00aaff").pack(pady=5)
    ctk.CTkLabel(frame, textvariable=feedbackDisplay, font=(None, 14)).pack(pady=5)
    ctk.CTkLabel(frame, textvariable=waitHost, font=(None, 12), text_color="gray").pack(pady=5)
    return frame, entry, submit_btn

# Creates Leaderboard final frame
def leaderboardFrame(parent, endDisplay, leaderboardDisplay, onNextCom, onQuitCom):
    frame = ctk.CTkFrame(parent)
    ctk.CTkLabel(frame, textvariable=endDisplay, font=(None, 20)).pack(pady=(10,5))
    ctk.CTkLabel(frame, text="🏆 Leaderboard", font=(None, 18)).pack(pady=(5,5))
    ctk.CTkLabel(frame, textvariable=leaderboardDisplay, justify="left").pack(pady=5)
    next_btn = ctk.CTkButton(frame, text="Next Round", command=onNextCom)
    quit_btn = ctk.CTkButton(frame, text="Quit", command=onQuitCom)
    return frame, next_btn, quit_btn

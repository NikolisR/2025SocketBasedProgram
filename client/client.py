import threading
import customtkinter as ctk
import sys
from tkinter import simpledialog, messagebox
from socketHandling import serverConnection, BUFFER_SIZE
from mainGUI import mainLobbyFrame, questionFrame, leaderboardFrame
from messageHandlers import serverMessages



# this creates my whole frame
class EGameClient(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("DECIPHER ME PLEASE OH GOD PLEASE")
        self.geometry("600x600")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

        # Establish my inittialy connection when users join
        self.sock = None
        self.is_host = False
        self.current_round = 0
        self.total_rounds = 0

        # my self variables to send back and fourth
        self.lobbyPlayers = ctk.StringVar()
        self.rndPlaceholder = ctk.StringVar(value="Round 0/0")
        self.cipherDisplay = ctk.StringVar()
        self.histDisplay = ctk.StringVar()
        self.timerDisplay = ctk.StringVar(value="Timer: 0s")
        self.feedbackDisplay = ctk.StringVar()
        self.waitHost = ctk.StringVar()
        self.lastSubmittion = ctk.StringVar()
        self.leaderboardDisplay = ctk.StringVar()
        self.endDisplay = ctk.StringVar()


        # Prompts the user for the name, ipaddress, and estabishes a connection via that ip address
        ipAddress = simpledialog.askstring("Server IP", "Enter server IP (blank=localhost):", parent=self) or 'localhost'
        self.name = simpledialog.askstring("Name", "Enter your player name:", parent=self)
        self.sock = serverConnection(ipAddress, self.name)

        # Realistiaclly all this does is create the main lobby frame "FORMATTING MY FRAMES"
        self.frame_lobby, self.start_btn = mainLobbyFrame(self, self.lobbyPlayers, self.waitHost, self.sendStart)
        self.frame_lobby.pack(fill="both", expand=True, padx=20, pady=20)

        self.frame_q, self.answer_entry, self.submit_btn = questionFrame(
            self,
            self.rndPlaceholder,
            self.cipherDisplay,
            self.histDisplay,
            self.timerDisplay,
            self.ohGodPleaseSubmitItPlease,
            self.waitHost,
            self.lastSubmittion,
            self.feedbackDisplay
        )
        self.feedback_next_btn = ctk.CTkButton(self.frame_q, text="Next", command=self.sendNext)

        self.frame_lb, self.next_btn, self.quitGame_btn = leaderboardFrame(
            self,
            self.endDisplay,
            self.leaderboardDisplay,
            self.sendStart,
            self.quitGame
        )

        threading.Thread(target=self.messageHandler, daemon=True).start()

    # Sends my start command to start the game
    def sendStart(self):
        self.sock.sendall(b"start")

        # Hides all the buttons to get to the next challenge
        self.start_btn.pack_forget()
        self.next_btn.pack_forget()
        self.quitGame_btn.pack_forget()
        self.frame_lb.pack_forget()

    def sendNext(self):
        self.sock.sendall(b"next")                                                                                      # sends my next


    # displays me leaderboard
    def displayLeaderboard(self):
        self.frame_q.pack_forget()
        self.feedback_next_btn.pack_forget()
        self.frame_lb.pack(fill="both", expand=True, padx=20, pady=20)

        # if round is less than total, show without end display
        if self.current_round < self.total_rounds:
            self.endDisplay.set("")
            if self.is_host:
                self.next_btn.pack(pady=10)


        # else, show game over congrats
        else:
            first = self.leaderboardDisplay.get().split("\n")[0]
            top = first.split(":")[0]
            self.endDisplay.set(f"Game Over! Congratulations {top}!")
            self.quitGame_btn.pack(pady=10)

    # when you quit, destroy the frame/ window
    def quitGame(self):
        try:
            self.sock.sendall(b"quit\n")
            self.sock.close()
        except:
            pass
        self.destroy()
        sys.exit(0)                                                                                                     # When you quit, it wont crash my application


    # please don't mind the naming convention. This block was hard to do.
    # Waits for you to submit the answer
    def ohGodPleaseSubmitItPlease(self):
        ans = self.answer_entry.get().strip().upper()
        if not ans:                                                                                                     # this santizes my input so that you can't submit just nothing
            messagebox.showwarning("Invalid", "Please submit a valid response.")
            return

        # this locks the answer block and waits for other responses
        self.sock.sendall(ans.encode())
        self.answer_entry.delete(0, ctk.END)
        self.lastSubmittion.set(f"You submitted: {ans}")
        self.answer_entry.configure(state='disabled')
        self.submit_btn.configure(state='disabled')
        self.waitHost.set("Waiting for other players' responses...")


    # Splits over to a new thread, waits for any new incoming communication from the server
    def messageHandler(self):
        buffer = ""
        while True:
            try:
                data = self.sock.recv(BUFFER_SIZE).decode()
            except:
                break
            if not data:
                break
            buffer += data
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if not line:
                    continue
                serverMessages(self, line)

if __name__ == '__main__':
    app = EGameClient()
    app.mainloop()

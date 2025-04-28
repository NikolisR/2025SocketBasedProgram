import socket  # socket library usage for TCP connections!
import threading  # threading for background receive loop!
import time  # timing functions!
import customtkinter as ctk  # modern Tkinter UI!
from tkinter import simpledialog, messagebox  # dialogs!

# Appearance configuration!
ctk.set_appearance_mode("dark")  # modes: "light", "dark"!
ctk.set_default_color_theme("blue")  # themes: "blue", "green", "dark-blue"!

# Configuration!
SERVER_PORT = 5555
NUM_ROUNDS = 5
ROUND_TIME = 20  # seconds per round!

class EncryptionClientApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Encryption Battle")  # window title!
        self.geometry("600x600")  # window size!

        # Networking!
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_ip = simpledialog.askstring("Server IP", "Enter server IP (blank=localhost):", parent=self) or 'localhost'
        self.name = simpledialog.askstring("Name", "Enter your player name:", parent=self)
        self.sock.connect((server_ip, SERVER_PORT))  # connect to server!
        self.sock.sendall(self.name.encode())  # send username!

        # State!
        self.is_host = False
        self.current_round = 0
        self.timer_running = False
        self.timer_count = ROUND_TIME

        # UI variables!
        self.lobby_var = ctk.StringVar()
        self.round_var = ctk.StringVar(value=f"Round 0/{NUM_ROUNDS}")
        self.cipher_var = ctk.StringVar()
        self.hint_var = ctk.StringVar()
        self.timer_var = ctk.StringVar(value=f"Timer: {ROUND_TIME}s")
        self.feedback_var = ctk.StringVar()
        self.waiting_var = ctk.StringVar()
        self.last_submit_var = ctk.StringVar()
        self.leaderboard_var = ctk.StringVar()

        # ----- Lobby Frame -----
        self.frame_lobby = ctk.CTkFrame(self)
        self.frame_lobby.pack(fill="both", expand=True, padx=20, pady=20)
        ctk.CTkLabel(self.frame_lobby, text="🛋️ Lobby Players", font=(None, 18)).pack(pady=(0,10))
        ctk.CTkLabel(self.frame_lobby, textvariable=self.lobby_var, justify="left").pack(pady=(0,20))
        self.start_btn = ctk.CTkButton(self.frame_lobby, text="Start Game", command=self.send_start)
        # only host will pack this!

        # ----- Question Frame -----
        self.frame_q = ctk.CTkFrame(self)
        ctk.CTkLabel(self.frame_q, textvariable=self.round_var, font=(None, 16)).pack(pady=(10,5))
        ctk.CTkLabel(self.frame_q, textvariable=self.cipher_var, font=(None, 24, 'bold')).pack(pady=5)
        ctk.CTkLabel(self.frame_q, textvariable=self.hint_var, font=(None, 14)).pack(pady=5)
        ctk.CTkLabel(self.frame_q, textvariable=self.timer_var, font=(None, 14)).pack(pady=5)
        self.answer_entry = ctk.CTkEntry(self.frame_q, placeholder_text="Type your answer here...")
        self.answer_entry.pack(pady=10)
        self.submit_btn = ctk.CTkButton(self.frame_q, text="Submit", command=self.submit_answer)
        self.submit_btn.pack(pady=5)
        ctk.CTkLabel(self.frame_q, textvariable=self.last_submit_var, font=(None, 12), text_color="#00aaff").pack(pady=5)
        ctk.CTkLabel(self.frame_q, textvariable=self.feedback_var, font=(None, 14)).pack(pady=5)
        ctk.CTkLabel(self.frame_q, textvariable=self.waiting_var, font=(None, 12), text_color="gray").pack(pady=5)
        self.feedback_next_btn = ctk.CTkButton(self.frame_q, text="Next", command=self.show_leaderboard)
        # only shown after feedback!

        # ----- Leaderboard Frame -----
        self.frame_lb = ctk.CTkFrame(self)
        ctk.CTkLabel(self.frame_lb, text="🏆 Leaderboard", font=(None, 18)).pack(pady=(10,5))
        ctk.CTkLabel(self.frame_lb, textvariable=self.leaderboard_var, justify="left").pack(pady=5)
        # host-only Next Round for non-final rounds
        self.next_btn = ctk.CTkButton(self.frame_lb, text="Next Round", command=self.send_start)
        # final-round buttons
        self.play_again_btn = ctk.CTkButton(self.frame_lb, text="Play Again", command=self.play_again)
        self.end_game_btn = ctk.CTkButton(self.frame_lb, text="End Game", command=self.end_game)

        # Start receive loop!
        threading.Thread(target=self.recv_loop, daemon=True).start()

    def send_start(self):
        self.sock.sendall(b"start")  # notify server!
        # hide lobby and leaderboard controls!
        self.start_btn.pack_forget()
        self.next_btn.pack_forget()
        self.play_again_btn.pack_forget()
        self.end_game_btn.pack_forget()
        self.frame_lb.pack_forget()

    def show_leaderboard(self):
        # hide question frame and feedback next!
        self.frame_q.pack_forget()
        self.feedback_next_btn.pack_forget()
        # display leaderboard frame!
        self.frame_lb.pack(fill="both", expand=True, padx=20, pady=20)
        # show appropriate buttons
        if self.current_round < NUM_ROUNDS:
            if self.is_host:
                self.next_btn.pack(pady=10)
        else:
            # final round: show Play Again and End Game
            self.play_again_btn.pack(pady=10)
            self.end_game_btn.pack(pady=10)

    def play_again(self):
        # reset to lobby UI!
        self.frame_lb.pack_forget()
        self.frame_q.pack_forget()
        self.lobby_var.set("")
        self.leaderboard_var.set("")
        self.current_round = 0
        self.round_var.set(f"Round 0/{NUM_ROUNDS}")
        self.frame_lobby.pack(fill="both", expand=True, padx=20, pady=20)
        if self.is_host:
            self.start_btn.pack(pady=10)

    def end_game(self):
        self.quit()  # close application!

    def submit_answer(self):
        ans = self.answer_entry.get().strip().upper()
        if not ans:
            messagebox.showwarning("Invalid", "Please submit a valid response.")  # input validation!
            return
        self.sock.sendall(ans.encode())  # send answer!
        self.answer_entry.delete(0, ctk.END)  # clear input!
        self.last_submit_var.set(f"You submitted: {ans}")  # show last!
        self.answer_entry.configure(state='disabled')  # disable entry!
        self.submit_btn.configure(state='disabled')  # disable submit!
        self.waiting_var.set("Waiting for other players' responses...")  # waiting!

    def start_timer(self):
        self.timer_count = ROUND_TIME  # reset timer!
        self.timer_running = True
        self.update_timer()

    def update_timer(self):
        if not self.timer_running:
            return
        self.timer_var.set(f"Timer: {self.timer_count}s")
        if self.timer_count > 0:
            self.timer_count -= 1
            self.after(1000, self.update_timer)  # countdown!
        else:
            self.answer_entry.configure(state='disabled')
            self.submit_btn.configure(state='disabled')
            self.timer_running = False

    def recv_loop(self):
        buffer = ""
        while True:
            try:
                data = self.sock.recv(4096).decode()  # receive!
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
                if line.startswith("HOST:"):
                    self.is_host = True
                    self.start_btn.pack(pady=10)  # show start for host!
                elif line.startswith("LOBBY:"):
                    names = line.split("LOBBY:",1)[1]
                    self.lobby_var.set(names.replace(',', '\n'))  # update lobby!
                elif line.startswith("ROUND:"):
                    num = int(line.split(':',1)[1])
                    self.current_round = num
                    self.round_var.set(f"Round {num}/{NUM_ROUNDS}")  # update round!
                elif line.startswith("CHALLENGE:"):
                    _, payload = line.split("CHALLENGE:",1)
                    cipher, hint = payload.split("|",1)
                    self.feedback_var.set("")
                    self.leaderboard_var.set("")
                    self.waiting_var.set("")
                    self.last_submit_var.set("")
                    self.answer_entry.configure(state='normal')
                    self.submit_btn.configure(state='normal')
                    self.answer_entry.delete(0, ctk.END)
                    self.cipher_var.set(cipher.strip())
                    self.hint_var.set(hint.split("HINT:",1)[1].strip())
                    self.frame_lobby.pack_forget()
                    self.frame_lb.pack_forget()
                    self.frame_q.pack(fill="both", expand=True, padx=20, pady=20)  # show question!
                    self.start_timer()
                elif line.startswith("FEEDBACK:") or line.startswith("Time's up!"):
                    self.timer_running = False  # stop timer!
                    fb = line.replace("FEEDBACK:", "").strip()
                    self.feedback_var.set(fb)
                    self.waiting_var.set("")
                    self.feedback_next_btn.pack(pady=10)  # show feedback next!
                elif line.startswith("LEADERBOARD:"):
                    lb = line.split("LEADERBOARD:",1)[1]
                    self.leaderboard_var.set(lb.replace(',', '\n'))  # set leaderboard!
                elif "GAME OVER" in line:
                    messagebox.showinfo("Game Over", line)
                    try:
                        self.sock.close()
                    except:
                        pass
                    self.quit()  # close application!

if __name__ == '__main__':
    app = EncryptionClientApp()
    app.mainloop()

import tkinter as tk
from tkinter import font as tkfont

GRID_SIZE = 16

class BoardApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("16x16 Five-in-a-Row (X/O) with Proximity Rule")

        # Fonts
        self.font_cell = tkfont.Font(family="Consolas", size=16, weight="bold")
        self.font_win  = tkfont.Font(family="Consolas", size=16, weight="bold", overstrike=1)

        # State
        self.current_player = "X"
        self.buttons = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.scores = {"X": 0, "O": 0}

        # Top bar
        topbar = tk.Frame(self, padx=8, pady=8)
        topbar.pack(side="top", fill="x")

        self.turn_label = tk.Label(topbar, text=f"Turn: {self.current_player}", font=("Consolas", 14))
        self.turn_label.pack(side="left")

        self.score_label = tk.Label(topbar, text=self.score_text(), font=("Consolas", 14))
        self.score_label.pack(side="left", padx=20)

        reset_btn = tk.Button(topbar, text="Reset Board", command=self.reset_board, font=("Consolas", 12))
        reset_btn.pack(side="right", padx=6)

        reset_all_btn = tk.Button(topbar, text="Reset All (incl. scores)", command=self.reset_all, font=("Consolas", 12))
        reset_all_btn.pack(side="right", padx=6)

        # Grid
        grid = tk.Frame(self)
        grid.pack(padx=8, pady=8)

        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                btn = tk.Button(
                    grid,
                    text="",
                    width=3,
                    height=1,
                    font=self.font_cell,
                    command=lambda rr=r, cc=c: self.handle_click(rr, cc)
                )
                btn.grid(row=r, column=c, padx=1, pady=1)
                self.buttons[r][c] = btn

    def score_text(self):
        return f"Score  X: {self.scores['X']}   O: {self.scores['O']}"

    # ---------------- Moves ----------------

    def handle_click(self, r, c):
        btn = self.buttons[r][c]
        if btn["text"] != "":
            return  # can't overwrite

        # Enforce proximity rule (except for very first move)
        if not self.any_filled_on_board() or self.is_legal_proximity(r, c):
            # Place mark
            btn.config(text=self.current_player)

            # Check win from this move
            win_line = self.find_any_five(r, c, self.current_player)
            if win_line:
                self.mark_winning_line(win_line)
                self.scores[self.current_player] += 1
                self.score_label.config(text=self.score_text())
                self.turn_label.config(text=f"{self.current_player} wins! Resetting...")
                self.disable_board()
                self.after(800, self.reset_board)
                return

            # Switch turn
            self.current_player = "O" if self.current_player == "X" else "X"
            self.turn_label.config(text=f"Turn: {self.current_player}")
        else:
            # Illegal by proximity rule → flash the cell
            self.flash_illegal(r, c)

    def any_filled_on_board(self):
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if self.buttons[r][c]["text"] != "":
                    return True
        return False

    def is_legal_proximity(self, r, c):
        """
        After the first move, a move is legal iff:
          - There's an already-filled cell in any of 8 directions at distance 1, OR
          - There's an already-filled cell at distance 2 in any of 8 directions AND
            the between cell is empty. (=> at most one empty between filled fields)
        """
        dirs = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]

        # distance 1 neighbor
        for dr, dc in dirs:
            r1, c1 = r + dr, c + dc
            if self.in_bounds(r1, c1) and self.buttons[r1][c1]["text"] != "":
                return True

        # distance 2 neighbor with exactly one empty between
        for dr, dc in dirs:
            r_mid, c_mid = r + dr, c + dc
            r2, c2 = r + 2*dr, c + 2*dc
            if self.in_bounds(r2, c2):
                if self.buttons[r2][c2]["text"] != "" and self.buttons[r_mid][c_mid]["text"] == "":
                    return True

        return False

    def flash_illegal(self, r, c):
        btn = self.buttons[r][c]
        orig = btn.cget("bg")
        btn.config(bg="#ffcccc")
        self.after(150, lambda: btn.config(bg=orig))

    # ---------------- Win detection ----------------

    def find_any_five(self, r, c, player):
        """Return 5 cells forming a win that includes (r,c), else None."""
        for dr, dc in ((0,1), (1,0), (1,1), (1,-1)):
            line = self.check_direction_for_five(r, c, player, dr, dc)
            if line:
                return line
        return None

    def check_direction_for_five(self, r, c, player, dr, dc):
        segment = [(r, c)]

        # backward
        rr, cc = r - dr, c - dc
        while self.in_bounds(rr, cc) and self.buttons[rr][cc]["text"] == player:
            segment.insert(0, (rr, cc))
            rr, cc = rr - dr, cc - dc

        # forward
        rr, cc = r + dr, c + dc
        while self.in_bounds(rr, cc) and self.buttons[rr][cc]["text"] == player:
            segment.append((rr, cc))
            rr, cc = rr + dr, cc + dc

        if len(segment) < 5:
            return None

        pivot = segment.index((r, c))
        start = max(0, min(pivot - 2, len(segment) - 5))
        return segment[start:start + 5]

    def in_bounds(self, r, c):
        return 0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE

    def mark_winning_line(self, cells):
        for (r, c) in cells:
            self.buttons[r][c].config(font=self.font_win, bg="#FFD966")

    def disable_board(self):
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                self.buttons[r][c]["state"] = "disabled"

    def enable_board(self):
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                self.buttons[r][c]["state"] = "normal"

    # ---------------- Reset ----------------

    def reset_board(self):
        self.current_player = "X"
        self.turn_label.config(text=f"Turn: {self.current_player}")
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                self.buttons[r][c].config(text="", font=self.font_cell, bg=self.cget("bg"), state="normal")

    def reset_all(self):
        self.scores = {"X": 0, "O": 0}
        self.score_label.config(text=self.score_text())
        self.reset_board()

if __name__ == "__main__":
    app = BoardApp()
    app.mainloop()

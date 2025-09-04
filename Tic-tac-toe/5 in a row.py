import random
from math import inf
import tkinter as tk
from tkinter import font as tkfont

# konstante
N = 16  # 16x16 tabla
EMPTY, X, O = 0, 1, -1 #moguce pozicije za svako polje u tabli
DIRS = [(1,0),(0,1),(1,1),(1,-1)] #smer

# Parametri
AI_PLAYER = O
HUMAN_PLAYER = X
AI_DEPTH = 2          # 2 = brzo, 3 = jace ali sporije, dubina u koju ce agent ici
MOVE_LIMIT = 12       # maksimalan broj mogucih poteza koji ce agent uzeti u obzir
CAND_RADIUS = 2       # dozvoljen razmak, odnosno radijus izmedju vec odigranih poteza
OPPONENT_WEIGHT = 1.1 # vrednovanje blokiranja (da ne bi AI 'glavom kroz zid' samo igrao ono sto mu moze pobedu doneti)

def new_board():
    return [[EMPTY]*N for _ in range(N)] #Pravljenje nove tabele

def inside(r,c):
    return 0 <= r < N and 0 <= c < N

def has_any_stone(board):
    return any(board[r][c] != EMPTY for r in range(N) for c in range(N)) #Proverava da li je polje prazno

def legal(board, r, c):  #proverava da li je legalan potez (da li je prazno mesto i da li je potez dovoljno blizu odnosno u istom kvadratu)
    if not inside(r,c) or board[r][c] != EMPTY:
        return False
    if not has_any_stone(board):
        return True
    for rr in range(max(0,r-2), min(N-1,r+2)+1):
        for cc in range(max(0,c-2), min(N-1,c+2)+1):
            if board[rr][cc] != EMPTY:
                return True
    return False

def apply_move(board, r, c, player): #odigrati potez
    board[r][c] = player

def is_win_at(board, r, c):  #Zbog ove funkcije AI ce, ukoliko ima priliku, uvek igrati da pobedi i u tom slucaju nece vrednovati blokiranje
                             # Ova funkcija se koristi u winning_move()
    player = board[r][c]
    if player == EMPTY:
        return False
    for dr,dc in DIRS:
        cnt = 1
        rr, cc = r+dr, c+dc
        while inside(rr,cc) and board[rr][cc] == player:
            cnt += 1; rr += dr; cc += dc
        rr, cc = r-dr, c-dc
        while inside(rr,cc) and board[rr][cc] == player:
            cnt += 1; rr -= dr; cc -= dc
        if cnt >= 5:
            return True
    return False

def full(board):
    return all(board[r][c] != EMPTY for r in range(N) for c in range(N)) #Proverava da li je citava tabla ispunjena

def candidate_moves(board, radius=CAND_RADIUS):  #Ova funkcija obezbedjuje da agent uzima u obzir prazna polja koja moze odigrati
    if not has_any_stone(board):
        return [(N//2, N//2)]
    cand = set()
    for r in range(N):
        for c in range(N):
            if board[r][c] != EMPTY:
                for rr in range(max(0, r - radius), min(N-1, r + radius) + 1):
                    for cc in range(max(0, c - radius), min(N-1, c + radius) + 1):
                        if board[rr][cc] == EMPTY:
                            cand.add((rr, cc))
    if not cand:
        for r in range(N):
            for c in range(N):
                if board[r][c] == EMPTY:
                    cand.add((r, c))
    return [m for m in cand if legal(board, *m)]

def winning_move(board, player):
    for (r, c) in candidate_moves(board):
        board[r][c] = player
        won = is_win_at(board, r, c) #Ukoliko je vrednost ove funkcije True, ovaj ce se potez odigrati.
        board[r][c] = EMPTY
        if won:
            return (r, c)
    return None

# Heuristika; ovde se boduju potezi - 5 ili vise u nizu su ubedljivo najbolje bodovani
# kod 4 u nizu (itd.) bodovanje zavisi od toga koliko im je strana otvoreno
def run_score(run_len, open_ends):
    if run_len >= 5:
        return 1_000_000
    if run_len == 4:
        return 100_000 if open_ends == 2 else 10_000 if open_ends == 1 else 0
    if run_len == 3:
        return 5_000 if open_ends == 2 else 500 if open_ends == 1 else 0
    if run_len == 2:
        return 200 if open_ends == 2 else 50 if open_ends == 1 else 0
    if run_len == 1:
        return 10 if open_ends == 2 else 1 if open_ends == 1 else 0
    return 0

def score_line(arr, player):  #Funkcija preko koje se dobijaju 'open_ends'
    total = 0                  #total ce biti taj broj
    i = 0
    L = len(arr)
    while i < L:
        if arr[i] != player:
            i += 1
            continue
        j = i
        while j < L and arr[j] == player:
            j += 1
        run_len = j - i
        left_open = 1 if i-1 >= 0 and arr[i-1] == EMPTY else 0
        right_open = 1 if j < L and arr[j] == EMPTY else 0
        total += run_score(run_len, left_open + right_open)
        i = j
    return total

def score_line_with_gaps(arr, player):  #Bodovanje koje uzima u obzir i razmake izmedju odigranih poteza
    base = score_line(arr, player)      # 'extra' ce da sadrzi to bodovanje
    extra = 0
    L = len(arr)

    def cnt(vals):  return sum(1 for v in vals if v == player)
    def zeros(vals): return sum(1 for v in vals if v == EMPTY)

    for s in range(L-4):
        w = arr[s:s+5]
        if cnt(w) == 4 and zeros(w) == 1:
            extra += 25000
        elif cnt(w) == 3 and zeros(w) == 2:
            extra += 1200

    for s in range(L-5):
        w = arr[s:s+6]
        if cnt(w) == 4 and zeros(w) == 2:
            extra += 4000
        if cnt(w) == 5 and zeros(w) == 1:
            extra += 60000

    return base + extra

def all_lines(board):
    # horizontalno
    for r in range(N):
        yield [board[r][c] for c in range(N)]
    # vertikalno
    for c in range(N):
        yield [board[r][c] for r in range(N)]
    # dijagonala "\"
    for r in range(N):
        arr, rr, cc = [], r, 0
        while rr < N and cc < N:
            arr.append(board[rr][cc]); rr += 1; cc += 1
        yield arr
    for c in range(1, N):
        arr, rr, cc = [], 0, c
        while rr < N and cc < N:
            arr.append(board[rr][cc]); rr += 1; cc += 1
        yield arr
    # dijagonala "/"
    for r in range(N):
        arr, rr, cc = [], r, N-1
        while rr < N and cc >= 0:
            arr.append(board[rr][cc]); rr += 1; cc -= 1
        yield arr
    for c in range(N-2, -1, -1):
        arr, rr, cc = [], 0, c
        while rr < N and cc >= 0:
            arr.append(board[rr][cc]); rr += 1; cc -= 1
        yield arr

def score_for(board, player): #vraca score
    return sum(score_line_with_gaps(line, player) for line in all_lines(board))

def evaluate(board):  #Evaluacija poteza
    my  = score_for(board, AI_PLAYER)
    opp = score_for(board, -AI_PLAYER)
    return my - OPPONENT_WEIGHT * opp
#Redosled poteza (ko igra)
def ordered_moves(board, player, limit=MOVE_LIMIT):
    moves = candidate_moves(board)
    scored = []
    for (r,c) in moves:
        board[r][c] = player
        if is_win_at(board, r, c):
            val = inf if player == AI_PLAYER else -inf #Ako funkcija vrati TRUE AI_PLAYER ce odigrati taj potez
        else:
            val = evaluate(board) #Ako ta funkcija ne vrati true, onda se vraca na svu do sada navedenu logiku
        board[r][c] = EMPTY
        scored.append(((r,c), val))
    #AI zeli veci eval, protivnik manji -> sortiranje
    reverse = True if player == AI_PLAYER else False
    scored.sort(key=lambda x: x[1], reverse=reverse)
    if limit is not None and len(scored) > limit:
        scored = scored[:limit]
    return [m for (m,_) in scored]

#Minimax + alpha-beta
def minimax(board, depth, alpha, beta, maximizing, last_move):
    if last_move is not None and is_win_at(board, *last_move): ##Proverava da li je doslo do pobede
        winner = board[last_move[0]][last_move[1]]             ##Odmah proverava da li smo na kraju
        if winner == AI_PLAYER:
            return 1_000_000 - (10 * (AI_DEPTH - depth))
        else:
            return -1_000_000 + (10 * (AI_DEPTH - depth))
    if depth == 0 or full(board):
        return evaluate(board)

    player = AI_PLAYER if maximizing else -AI_PLAYER
    best = -inf if maximizing else inf         #alfa: minus beskonacno, beta plus beskonacno
    for (r,c) in ordered_moves(board, player):
        board[r][c] = player
        val = minimax(board, depth-1, alpha, beta, not maximizing, (r,c))
        board[r][c] = EMPTY
        if maximizing:                          ##Alfa beta secenje
            if val > best: best = val
            if val > alpha: alpha = val
        else:
            if val < best: best = val
            if val < beta: beta = val
        if beta <= alpha:
            break
    return best
#Funkcija kojom agent igra
def ai_best_move(board, depth=AI_DEPTH):
    #Odmah proverava da li je potez pobednicki
    win_now = winning_move(board, AI_PLAYER)
    if win_now:
        return win_now
    #Blokira protivnika ako on ima pobedu
    block = winning_move(board, -AI_PLAYER)
    if block:
        return block
    #Minimax
    best_val = -inf
    best_moves = []
    for (r,c) in ordered_moves(board, AI_PLAYER):
        board[r][c] = AI_PLAYER
        val = minimax(board, depth-1, -inf, inf, False, (r,c))
        board[r][c] = EMPTY
        if val > best_val:  #Gleda vrednost poteza i apdejtuje ako je vece (najvece ostane na kraju i taj potez bira)
            best_val = val
            best_moves = [(r,c)]
        elif val == best_val:
            best_moves.append((r,c))
    return random.choice(best_moves) if best_moves else random.choice(candidate_moves(board))  #Ako vise poteza ima istu nagradu, nasumicno ce odabrati potez

# Funkcija koju cemo koristiti kasnije da obelezimo pobedu (5 za redom)
def winning_five_cells(board, r, c):

    player = board[r][c]
    if player == EMPTY:
        return None
    for dr, dc in DIRS:
        seg = [(r, c)]
        rr, cc = r+dr, c+dc
        while inside(rr,cc) and board[rr][cc] == player:
            seg.append((rr,cc)); rr += dr; cc += dc
        rr, cc = r-dr, c-dc
        while inside(rr,cc) and board[rr][cc] == player:
            seg.insert(0,(rr,cc)); rr -= dr; cc -= dc
        if len(seg) >= 5:

            pivot = seg.index((r,c))
            start = max(0, min(pivot-2, len(seg)-5))
            return seg[start:start+5]
    return None

# TKINTER UI
CELL_FONT = ("Consolas", 14)
STATUS_FONT = ("Consolas", 12)

HUMAN_LAST_BG = "#CFF6D1"  # pale green
AI_LAST_BG    = "#D6E6FF"  # pale blue

class GomokuUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Iks-oks (16x16) — Igrač X protiv Agenta O")
        self.geometry("700x750")
        self.resizable(False, False)

        self.board = new_board()
        self.current = HUMAN_PLAYER
        self.game_over = False
        self.last_move = None  # track last played cell
        self.default_bg = self.cget("bg")

        # Fonts for normal/winning cells
        self.font_cell = tkfont.Font(family="Consolas", size=14, weight="bold")
        self.font_win  = tkfont.Font(family="Consolas", size=14, weight="bold", overstrike=1)

        # Top bar
        top = tk.Frame(self, padx=8, pady=6)
        top.pack(fill="x")
        self.status = tk.Label(top, text="Tvoj potez (X)", font=STATUS_FONT,  width=60, anchor="w")
        self.status.pack(side="left")
        tk.Button(top, text="Nova igra", command=self.reset, font=STATUS_FONT).pack(side="right")

        # Grid
        grid = tk.Frame(self, padx=6, pady=6)
        grid.pack()

        self.btns = [[None]*N for _ in range(N)]
        for r in range(N):
            for c in range(N):
                b = tk.Button(grid, text="", width=2, height=1, font=self.font_cell,
                              command=lambda rr=r, cc=c: self.on_click(rr, cc))
                b.grid(row=r, column=c, padx=1, pady=1)
                self.btns[r][c] = b

    #UI helpers
    def set_cell(self, r, c, val):
        if val == X:
            self.btns[r][c].config(text="X", fg="#1a1a1a")
        elif val == O:
            self.btns[r][c].config(text="O", fg="#1a4b9a")
        else:
            self.btns[r][c].config(text="", fg="black")

    def highlight_last(self, r, c, player):
        # remove previous last-move highlight if any (and if game not finished)
        if self.last_move and not self.game_over:
            pr, pc = self.last_move
            # don't touch cells already gold-marked after a win
            self.btns[pr][pc].config(bg=self.default_bg, font=self.font_cell)
        # set new highlight color
        color = HUMAN_LAST_BG if player == HUMAN_PLAYER else AI_LAST_BG
        self.btns[r][c].config(bg=color)
        self.last_move = (r, c)



    def flash_illegal(self, r, c):
        btn = self.btns[r][c]
        orig = btn.cget("bg")
        btn.config(bg="#ffcccc")
        self.after(120, lambda: btn.config(bg=orig))

    def disable_all(self):
        for r in range(N):
            for c in range(N):
                self.btns[r][c]["state"] = "disabled"

    def enable_all(self):
        for r in range(N):
            for c in range(N):
                self.btns[r][c]["state"] = "normal"

    # Game flow
    def on_click(self, r, c):
        if self.game_over:
            return
        if self.board[r][c] != EMPTY:
            return
        if not legal(self.board, r, c):
            self.status.config(text="Nelegalan potez, potez mora biti blizu vec popunjenih polja.")
            self.flash_illegal(r, c)
            return

        # Human move
        apply_move(self.board, r, c, HUMAN_PLAYER)
        self.set_cell(r, c, HUMAN_PLAYER)
        self.highlight_last(r, c, HUMAN_PLAYER)

        # Check human win/draw
        if is_win_at(self.board, r, c):
            self.finish_game(winner=HUMAN_PLAYER, last=(r,c))
            return
        if full(self.board):
            self.finish_game(winner=None, last=None)
            return

        # AI turn
        self.status.config(text="Agent razmišlja…")
        # Let UI update before heavy compute
        self.after(10, self.ai_move)

    def ai_move(self):
        if self.game_over:
            return
        r, c = ai_best_move(self.board, AI_DEPTH)
        apply_move(self.board, r, c, AI_PLAYER)
        self.set_cell(r, c, AI_PLAYER)
        self.highlight_last(r, c, AI_PLAYER)

        if is_win_at(self.board, r, c):
            self.finish_game(winner=AI_PLAYER, last=(r,c))
            return
        if full(self.board):
            self.finish_game(winner=None, last=None)
            return

        self.status.config(text="Tvoj potez (X)")

    def finish_game(self, winner, last):
        self.game_over = True
        if winner is None:
            self.status.config(text="Nerešeno! (Tabla je puna)")
        else:
            line = winning_five_cells(self.board, *last) if last else None
            if line:
                for (rr, cc) in line:
                    self.btns[rr][cc].config(font=self.font_win, bg="#FFD966")
            self.status.config(text=f"Pobednik: {'X' if winner==X else 'O'}")
        self.disable_all()

    def reset(self):
        self.board = new_board()
        self.game_over = False
        self.status.config(text="Tvoj potez (X)")
        for r in range(N):
            for c in range(N):
                self.btns[r][c].config(text="", font=self.font_cell, bg=self.cget("bg"), state="normal")

if __name__ == "__main__":
    app = GomokuUI()
    app.mainloop()

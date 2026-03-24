"""
mapp_card_gui.py
Interface graphique tkinter pour visualiser une partie de Mapp-Card.
Placer ce fichier dans le même répertoire que mapp_card.py, puis lancer :
    python mapp_card_gui.py

Contrôles :
  - Bouton "Coup suivant"  : joue la prochaine carte
  - Bouton "Pli suivant"   : joue tout le pli d'un coup
  - Bouton "Partie auto"   : joue toute la partie avec délai réglable
  - Slider vitesse         : délai entre les coups en mode auto (ms)
"""

import tkinter as tk
from tkinter import ttk, font as tkfont
import time, threading, random
from mapp_card import (
    Card, Rules, Random_Player,
    deal_cards, setup_players, determine_winner,
    BELOTE_RULES, BRIDGE_RULES, TAROT_RULES
)

# ─────────────────────────────────────────────
#  Palette & constantes visuelles
# ─────────────────────────────────────────────
BG          = "#1a4a2e"   # tapis vert foncé
BG_LIGHT    = "#256340"   # zones légèrement plus claires
FELT        = "#1f5c38"   # couleur pli central
CARD_BG     = "#fdf6e3"   # fond carte (ivoire)
CARD_BORDER = "#c8a96e"   # bordure carte (or pâle)
TRUMP_COLOR = "#e8c84a"   # surbrillance atout
TEXT_LIGHT  = "#f0e6c8"   # texte clair
TEXT_DARK   = "#2c1810"   # texte sombre sur carte
ACCENT      = "#e85d3a"   # accent rouge
SCORE_BG    = "#0f3020"   # fond scores
BTN_BG      = "#2d7a4f"
BTN_ACTIVE  = "#3a9e66"

SUIT_SYMBOLS = {1: "♠", 2: "♥", 3: "♦", 4: "♣"}
SUIT_COLORS  = {1: "#2c2c2c", 2: "#cc2222", 3: "#cc2222", 4: "#2c2c2c"}

# Positions (cx, cy) relatives à la table pour chaque joueur (N=4)
PLAYER_POSITIONS = {
    0: ("bottom", 0.5, 0.88),   # bas
    1: ("left",   0.05, 0.5),   # gauche
    2: ("top",    0.5, 0.12),   # haut
    3: ("right",  0.95, 0.5),   # droite
}

# Position des cartes jouées dans le pli central
TRICK_POSITIONS = {
    0: (0, +1),   # bas  → décalage y positif
    1: (-1, 0),   # gauche
    2: (0, -1),   # haut
    3: (+1, 0),   # droite
}

CARD_W, CARD_H = 54, 76
CARD_SMALL_W, CARD_SMALL_H = 38, 54


# ─────────────────────────────────────────────
#  Moteur de jeu (générateur pas-à-pas)
# ─────────────────────────────────────────────
class GameEngine:
    def __init__(self, rules: Rules):
        self.rules = rules
        self.players = setup_players(rules, use_human=False)
        deal_cards(rules, self.players)
        self.trump_suit = random.randint(1, rules.S) if rules.alpha else 1
        self.leader_index = 0
        self.current_trick = []
        self.trick_history = []       # liste de plis terminés
        self.trick_count = 0
        self.game_over = False
        self._init_trick()

    def _init_trick(self):
        self.current_trick = []
        self.ordered = [
            self.players[(self.leader_index + i) % self.rules.N]
            for i in range(self.rules.N)
        ]
        self.play_index = 0           # prochain joueur à jouer dans le pli

    def step(self):
        """Joue une carte. Retourne ('card', player, card) ou ('trick_end', winner, points)."""
        if self.game_over:
            return None

        if self.play_index < self.rules.N:
            j = self.ordered[self.play_index]
            legals = j.filter_legal_cards(self.current_trick, self.rules, self.trump_suit)
            card = j.decide(legals)
            self.current_trick.append((j, card))
            self.play_index += 1
            return ("card", j, card)

        # Fin du pli
        idx_v = determine_winner(self.current_trick, self.trump_suit)
        winner = self.current_trick[idx_v][0]
        pts = sum(c.get_points() for _, c in self.current_trick)
        winner.score += pts
        self.trick_history.append(list(self.current_trick))
        self.trick_count += 1
        self.leader_index = self.players.index(winner)

        if len(self.players[0].hand) == 0:
            self.game_over = True
            return ("game_over", winner, pts)

        self._init_trick()
        return ("trick_end", winner, pts)

    def play_full_trick(self):
        """Joue tous les coups du pli courant + résolution."""
        events = []
        while self.play_index < self.rules.N:
            events.append(self.step())
        events.append(self.step())   # trick_end / game_over
        return events


# ─────────────────────────────────────────────
#  Widget carte tkinter
# ─────────────────────────────────────────────
def draw_card(canvas, x, y, card, trump_suit, small=False, highlight=False, angle=0):
    """Dessine une carte sur un canvas. Retourne l'id du rectangle principal."""
    w = CARD_SMALL_W if small else CARD_W
    h = CARD_SMALL_H if small else CARD_H
    x0, y0 = x - w//2, y - h//2
    x1, y1 = x + w//2, y + h//2

    border = TRUMP_COLOR if card.suit == trump_suit else CARD_BORDER
    width  = 3 if highlight else 1

    # Ombre
    canvas.create_rectangle(x0+3, y0+3, x1+3, y1+3, fill="#0a2a18", outline="", tags="card")
    # Corps
    rid = canvas.create_rectangle(x0, y0, x1, y1,
                                   fill=CARD_BG, outline=border,
                                   width=width, tags="card")
    # Symbole couleur
    sym = SUIT_SYMBOLS.get(card.suit, f"S{card.suit}")
    col = SUIT_COLORS.get(card.suit, TEXT_DARK)
    fs  = 11 if small else 15
    canvas.create_text(x, y - (4 if small else 6),
                        text=sym, fill=col,
                        font=("Georgia", fs, "bold"), tags="card")
    # Valeur
    fv = 8 if small else 11
    canvas.create_text(x, y + (8 if small else 12),
                        text=str(card.value), fill=TEXT_DARK,
                        font=("Courier", fv, "bold"), tags="card")
    return rid


def draw_card_back(canvas, x, y, small=False):
    w = CARD_SMALL_W if small else CARD_W
    h = CARD_SMALL_H if small else CARD_H
    x0, y0 = x - w//2, y - h//2
    x1, y1 = x + w//2, y + h//2
    canvas.create_rectangle(x0+3, y0+3, x1+3, y1+3, fill="#0a2a18", outline="", tags="card")
    canvas.create_rectangle(x0, y0, x1, y1,
                             fill="#2d5a8e", outline=CARD_BORDER, width=1, tags="card")
    canvas.create_rectangle(x0+4, y0+4, x1-4, y1-4,
                             fill="#1e3f63", outline="#4a7ab5", width=1, tags="card")


def draw_card_sideways(canvas, x, y, card, trump_suit):
    """Carte en format paysage pour joueurs gauche/droite."""
    w, h = CARD_SMALL_H, CARD_SMALL_W   # inversé : plus large que haut
    x0, y0 = x - w//2, y - h//2
    x1, y1 = x + w//2, y + h//2
    border = TRUMP_COLOR if card.suit == trump_suit else CARD_BORDER
    canvas.create_rectangle(x0+3, y0+3, x1+3, y1+3, fill="#0a2a18", outline="", tags="card")
    canvas.create_rectangle(x0, y0, x1, y1, fill=CARD_BG, outline=border, width=1, tags="card")
    sym = SUIT_SYMBOLS.get(card.suit, f"S{card.suit}")
    col = SUIT_COLORS.get(card.suit, TEXT_DARK)
    canvas.create_text(x - 10, y, text=sym, fill=col,
                       font=("Georgia", 11, "bold"), tags="card")
    canvas.create_text(x + 12, y, text=str(card.value), fill=TEXT_DARK,
                       font=("Courier", 10, "bold"), tags="card")


# ─────────────────────────────────────────────
#  Application principale
# ─────────────────────────────────────────────
class MappCardGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Mapp-Card — Visualiseur")
        self.root.configure(bg=SCORE_BG)
        self.root.resizable(True, True)

        self.engine   = None
        self.auto_running = False
        self.last_events  = []   # événements du dernier step

        self._build_ui()
        self._start_new_game(BELOTE_RULES)

    # ── Construction de l'UI ──────────────────
    def _build_ui(self):
        # Barre supérieure : choix de règles
        top = tk.Frame(self.root, bg=SCORE_BG, pady=6)
        top.pack(fill=tk.X)

        tk.Label(top, text="MAPP-CARD", bg=SCORE_BG, fg=TRUMP_COLOR,
                 font=("Georgia", 18, "bold italic")).pack(side=tk.LEFT, padx=16)

        tk.Label(top, text="Règles :", bg=SCORE_BG, fg=TEXT_LIGHT,
                 font=("Courier", 10)).pack(side=tk.LEFT, padx=(20,4))

        self.rules_var = tk.StringVar(value="Belote")
        for name in ["Belote", "Bridge", "Tarot"]:
            tk.Radiobutton(top, text=name, variable=self.rules_var, value=name,
                           bg=SCORE_BG, fg=TEXT_LIGHT, selectcolor=BTN_BG,
                           activebackground=SCORE_BG, activeforeground=TRUMP_COLOR,
                           font=("Courier", 10),
                           command=self._on_rules_change).pack(side=tk.LEFT, padx=4)

        tk.Button(top, text="↺  Nouvelle partie", bg=BTN_BG, fg=TEXT_DARK,
                  font=("Courier", 10, "bold"), relief=tk.FLAT, padx=10,
                  activebackground=BTN_ACTIVE,
                  command=self._restart).pack(side=tk.RIGHT, padx=12)

        # Zone principale : table + scores
        main = tk.Frame(self.root, bg=SCORE_BG)
        main.pack(fill=tk.BOTH, expand=True)

        # Canvas table (gauche)
        self.canvas = tk.Canvas(main, bg=BG, highlightthickness=0, width=680, height=520)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.canvas.bind("<Configure>", lambda e: self._redraw())

        # Panneau droit : scores + log
        right = tk.Frame(main, bg=SCORE_BG, width=220)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=(0,8), pady=8)
        right.pack_propagate(False)

        tk.Label(right, text="SCORES", bg=SCORE_BG, fg=TRUMP_COLOR,
                 font=("Courier", 12, "bold")).pack(pady=(8,4))

        self.score_frame = tk.Frame(right, bg=SCORE_BG)
        self.score_frame.pack(fill=tk.X, padx=8)

        tk.Label(right, text="JOURNAL", bg=SCORE_BG, fg=TRUMP_COLOR,
                 font=("Courier", 12, "bold")).pack(pady=(16,4))

        log_frame = tk.Frame(right, bg=SCORE_BG)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=8)
        self.log_text = tk.Text(log_frame, bg="#0a2010", fg="#a0d8a0",
                                font=("Courier", 9), relief=tk.FLAT,
                                state=tk.DISABLED, wrap=tk.WORD)
        scroll = tk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Barre de contrôle en bas
        bot = tk.Frame(self.root, bg=SCORE_BG, pady=8)
        bot.pack(fill=tk.X)

        self.btn_step = tk.Button(bot, text="▶  Coup suivant",
                                   bg=BTN_BG, fg=TEXT_DARK,
                                   font=("Courier", 11, "bold"), relief=tk.FLAT,
                                   padx=14, activebackground=BTN_ACTIVE,
                                   command=self._do_step)
        self.btn_step.pack(side=tk.LEFT, padx=8)

        self.btn_trick = tk.Button(bot, text="⏩  Pli suivant",
                                    bg=BTN_BG, fg=TEXT_DARK,
                                    font=("Courier", 11, "bold"), relief=tk.FLAT,
                                    padx=14, activebackground=BTN_ACTIVE,
                                    command=self._do_trick)
        self.btn_trick.pack(side=tk.LEFT, padx=4)

        self.btn_auto = tk.Button(bot, text="⏭  Partie auto",
                                   bg="#5a3060", fg=TEXT_DARK,
                                   font=("Courier", 11, "bold"), relief=tk.FLAT,
                                   padx=14, activebackground="#7a4080",
                                   command=self._toggle_auto)
        self.btn_auto.pack(side=tk.LEFT, padx=4)

        tk.Label(bot, text="Vitesse :", bg=SCORE_BG, fg=TEXT_LIGHT,
                 font=("Courier", 10)).pack(side=tk.LEFT, padx=(20,4))
        self.speed_var = tk.IntVar(value=600)
        tk.Scale(bot, from_=50, to=2000, orient=tk.HORIZONTAL,
                 variable=self.speed_var, bg=SCORE_BG, fg=TEXT_LIGHT,
                 troughcolor=BTN_BG, highlightthickness=0,
                 length=160, showvalue=False).pack(side=tk.LEFT)
        tk.Label(bot, text="← rapide  lent →", bg=SCORE_BG, fg="#688",
                 font=("Courier", 8)).pack(side=tk.LEFT, padx=4)

        # Label infos atout
        self.info_label = tk.Label(bot, text="", bg=SCORE_BG, fg=TRUMP_COLOR,
                                    font=("Courier", 11, "bold"))
        self.info_label.pack(side=tk.RIGHT, padx=16)

    # ── Gestion des parties ───────────────────
    def _on_rules_change(self):
        pass  # déclenché au clic, la vraie action est dans _restart

    def _restart(self):
        self.auto_running = False
        self.btn_auto.config(text="⏭  Partie auto", bg="#5a3060")
        rules = {"Belote": BELOTE_RULES, "Bridge": BRIDGE_RULES, "Tarot": TAROT_RULES}
        self._start_new_game(rules[self.rules_var.get()])

    def _start_new_game(self, rules):
        self.engine = GameEngine(rules)
        self.highlighted_player = None
        self.last_trick_display  = []   # cartes du pli précédent à afficher brièvement
        self._clear_log()
        self._log(f"=== Nouvelle partie ({self.rules_var.get()}) ===")
        sym = SUIT_SYMBOLS.get(self.engine.trump_suit, f"S{self.engine.trump_suit}")
        self._log(f"Atout : {sym} (couleur {self.engine.trump_suit})")
        self.info_label.config(
            text=f"Atout : {sym}  —  {len(self.engine.players[0].hand)} cartes/joueur"
        )
        self._build_score_panel()
        self._redraw()
        self._set_buttons_state(True)

    # ── Contrôles ────────────────────────────
    def _do_step(self):
        if not self.engine or self.engine.game_over:
            return
        ev = self.engine.step()
        self._process_event(ev)
        self._redraw()

    def _do_trick(self):
        if not self.engine or self.engine.game_over:
            return
        evs = self.engine.play_full_trick()
        for ev in evs:
            self._process_event(ev)
        self._redraw()

    def _toggle_auto(self):
        if self.engine and self.engine.game_over:
            return
        self.auto_running = not self.auto_running
        if self.auto_running:
            self.btn_auto.config(text="⏸  Pause", bg="#8a2020")
            self._auto_loop()
        else:
            self.btn_auto.config(text="⏭  Partie auto", bg="#5a3060")

    def _auto_loop(self):
        if not self.auto_running or not self.engine:
            return
        if self.engine.game_over:
            self.auto_running = False
            self.btn_auto.config(text="⏭  Partie auto", bg="#5a3060")
            return
        self._do_step()
        delay = self.speed_var.get()
        self.root.after(delay, self._auto_loop)

    def _set_buttons_state(self, active):
        state = tk.NORMAL if active else tk.DISABLED
        self.btn_step.config(state=state)
        self.btn_trick.config(state=state)
        self.btn_auto.config(state=state)

    # ── Traitement des événements moteur ─────
    def _process_event(self, ev):
        if ev is None:
            return
        kind = ev[0]

        if kind == "card":
            _, player, card = ev
            sym = SUIT_SYMBOLS.get(card.suit, f"S{card.suit}")
            self._log(f"  {player.name:12s} → {sym}{card.value}")
            self.highlighted_player = player

        elif kind == "trick_end":
            _, winner, pts = ev
            self._log(f"┗ {winner.name} remporte le pli (+{pts} pts)")
            self._update_scores()

        elif kind == "game_over":
            _, winner, pts = ev
            self._log(f"┗ {winner.name} remporte le dernier pli (+{pts} pts)")
            self._update_scores()
            self._log("\n═══ FIN DE PARTIE ═══")
            self._show_final_scores()
            self._set_buttons_state(False)
            self.btn_auto.config(state=tk.DISABLED)

    def _show_final_scores(self):
        ranking = sorted(self.engine.players, key=lambda p: p.score, reverse=True)
        for p in ranking:
            self._log(f"  {p.name:12s} : {p.score} pts")

    # ── Dessin ───────────────────────────────
    def _redraw(self):
        c = self.canvas
        c.delete("all")
        W = c.winfo_width()  or 680
        H = c.winfo_height() or 520

        self._draw_table(c, W, H)
        self._draw_trick_zone(c, W, H)
        self._draw_players(c, W, H)
        self._draw_trick(c, W, H)
        self._draw_trump_indicator(c, W, H)
        self._draw_pli_counter(c, W, H)

    def _draw_table(self, c, W, H):
        # Fond tapis avec motif légèrement texturé via dégradé simulé
        c.create_rectangle(0, 0, W, H, fill=BG, outline="")
        # Ellipse centrale tapis
        mx, my = W//2, H//2
        c.create_oval(mx-220, my-170, mx+220, my+170,
                      fill=FELT, outline="#2d8050", width=2)
        # Lignes décoratives
        c.create_oval(mx-200, my-150, mx+200, my+150,
                      fill="", outline="#2a6040", width=1)

    def _draw_trump_indicator(self, c, W, H):
        if not self.engine:
            return
        sym = SUIT_SYMBOLS.get(self.engine.trump_suit, "?")
        col = SUIT_COLORS.get(self.engine.trump_suit, TEXT_DARK)
        cx, cy = W//2, H//2
        # Petit badge atout au centre
        c.create_oval(cx-22, cy-22, cx+22, cy+22,
                      fill=TRUMP_COLOR, outline="#c8a030", width=2)
        c.create_text(cx, cy, text=sym, fill=col,
                      font=("Georgia", 18, "bold"))

    def _draw_pli_counter(self, c, W, H):
        if not self.engine:
            return
        c.create_text(W-12, H-10,
                      text=f"Pli {self.engine.trick_count}",
                      fill="#6a9a6a", font=("Courier", 9),
                      anchor=tk.SE)

    def _draw_players(self, c, W, H):
        if not self.engine:
            return
        for idx, player in enumerate(self.engine.players):
            side, rx, ry = PLAYER_POSITIONS[idx]
            px, py = int(rx * W), int(ry * H)
            is_highlighted = (player == self.highlighted_player)
            is_next = (not self.engine.game_over and
                       self.engine.play_index < self.engine.rules.N and
                       player == self.engine.ordered[self.engine.play_index])
            self._draw_player_zone(c, player, px, py, side, is_highlighted, is_next)

    def _draw_player_zone(self, c, player, cx, cy, side, highlighted, is_next):
        # Nom + équipe
        team_colors = ["#4a90d9", "#e85d3a", "#50c878", "#f0c040"]
        tc = team_colors[player.team % len(team_colors)]

        # Indicateur "prochain à jouer"
        if is_next:
            c.create_oval(cx-32, cy-32, cx+32, cy+32,
                          fill="", outline=TRUMP_COLOR, width=2, dash=(4,3))

        bg_col = "#1a5535" if highlighted else BG_LIGHT
        # Badge nom
        c.create_rectangle(cx-38, cy-12, cx+38, cy+12,
                            fill=bg_col, outline=tc, width=2 if highlighted else 1,
                            tags="player")
        c.create_text(cx, cy, text=player.name, fill=TEXT_LIGHT,
                      font=("Courier", 9, "bold"), tags="player")

        # Cartes en main
        hand = player.hand
        n = len(hand)
        if n == 0:
            return

        if side == "bottom":
            self._draw_hand_horizontal(c, hand, cx, cy + 52, flip=False)
        elif side == "top":
            self._draw_hand_horizontal(c, hand, cx, cy - 52, flip=False)
        elif side == "left":
            self._draw_hand_vertical(c, hand, cx + 52, cy, flip=False)
        elif side == "right":
            self._draw_hand_vertical(c, hand, cx - 52, cy, flip=False)

    def _draw_hand_horizontal(self, c, hand, cx, cy, flip):
        n = len(hand)
        spacing = min(CARD_SMALL_W + 4, 260 // max(n, 1))
        total = spacing * (n - 1)
        start_x = cx - total // 2
        for i, card in enumerate(hand):
            x = start_x + i * spacing
            if flip:
                draw_card_back(c, x, cy, small=True)
            else:
                draw_card(c, x, cy, card, self.engine.trump_suit, small=True)

    def _draw_hand_vertical(self, c, hand, cx, cy, flip):
        n = len(hand)
        spacing = min(CARD_SMALL_W + 4, 300 // max(n, 1))
        total = spacing * (n - 1)
        start_y = cy - total // 2
        for i, card in enumerate(hand):
            y = start_y + i * spacing
            if flip:
                draw_card_back(c, cx, y, small=True)
            else:
                draw_card_sideways(c, cx, y, card, self.engine.trump_suit)

    def _draw_trick_zone(self, c, W, H):
        pass  # Le fond est déjà le tapis

    def _draw_trick(self, c, W, H):
        if not self.engine:
            return
        trick = self.engine.current_trick
        if not trick:
            return

        cx, cy = W // 2, H // 2
        offset = 52  # écart du centre

        for play_order, (player, card) in enumerate(trick):
            player_idx = self.engine.players.index(player)
            dx, dy = TRICK_POSITIONS[player_idx]
            tx = cx + dx * offset
            ty = cy + dy * offset
            draw_card(c, tx, ty, card, self.engine.trump_suit, small=False, highlight=True)

    # ── Scores ───────────────────────────────
    def _build_score_panel(self):
        for w in self.score_frame.winfo_children():
            w.destroy()
        if not self.engine:
            return
        team_colors = ["#4a90d9", "#e85d3a", "#50c878", "#f0c040"]
        for p in self.engine.players:
            row = tk.Frame(self.score_frame, bg=SCORE_BG)
            row.pack(fill=tk.X, pady=2)
            tc = team_colors[p.team % len(team_colors)]
            tk.Label(row, text="●", bg=SCORE_BG, fg=tc,
                     font=("Courier", 12)).pack(side=tk.LEFT)
            tk.Label(row, text=f"{p.name}", bg=SCORE_BG, fg=TEXT_LIGHT,
                     font=("Courier", 10), width=10, anchor=tk.W).pack(side=tk.LEFT)
            lbl = tk.Label(row, text="0", bg=SCORE_BG, fg=TRUMP_COLOR,
                           font=("Courier", 11, "bold"), width=5, anchor=tk.E)
            lbl.pack(side=tk.RIGHT)
            p._score_label = lbl   # on attache le label au joueur

    def _update_scores(self):
        if not self.engine:
            return
        for p in self.engine.players:
            if hasattr(p, "_score_label"):
                p._score_label.config(text=str(p.score))

    # ── Log ──────────────────────────────────
    def _log(self, msg):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def _clear_log(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state=tk.DISABLED)


# ─────────────────────────────────────────────
#  Point d'entrée
# ─────────────────────────────────────────────
def main():
    root = tk.Tk()
    root.geometry("920x640")
    root.minsize(720, 520)
    app = MappCardGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()

#==========================================

# Authors : A-C Caron, E Claeyssen, P Mathieu
# SMAC Team, CRISTAL Lab, Lille University
# Date : 2026-02-02
# URL : https://www.cristal.univ-lille.fr/equipes/smac/

# Ce code a été réalisé pour étudier la possibilité d'apprendre à une
# IA à jouer aux jeux de cartes. Ce code ne contient pas d'IA, mais
# permet de mettre en oeuvre des joueurs humains ou artificiels
# (avatars à améliorer avec une éventuelle IA).  Pour permettre de
# simuler un grand nombre de jeux de plis. les règles du jeu ont été
# abstraites au maximum.

#==========================================


import random
from abc import ABC, abstractmethod      # pour faire explicitement des classes abstraites
from dataclasses import dataclass        # sorte de Lombok pour python (evite le boilerplate code)
from typing import List, Tuple           # permet d'indiquer les types de données attendus



# TRADUCTION (voir source LaTex)
# Pli -> trick
# couper -> to trump
# atout -> trump
# couleur -> suit
# main -> hand
# entameur -> leader



# --- Structures de base ---

@dataclass
class Rules:
    # AC : on suppose qu'on fournit la couleur demandée, si on en a
    gamma: bool = False  # Obligation de monter sur la couleur demandée (pas seulement de fournir la couleur)
    kappa: bool = True   # Obligation de couper
    mu: bool = True      # Obligation de surcouper
    alpha: bool = True   # Atout dynamique
    epsilon: bool = False # Équipe fixe (0) ou dynamique (1)
    
    S: int = 4 # nombre de couleurs
    V: int = 8 # nombre de valeurs
    N: int = 4 # nombre de joueurs

@dataclass
class Card:
    suit: int
    value: int
    def __repr__(self): return f"S{self.suit}:V{self.value}"

    def get_points(self) -> int:
        """Définit la valeur de la carte (Reward)."""
        # Exemple simple : les cartes au-dessus de 10 valent leur valeur, les autres 2
        # A revoir !!
        return self.value if self.value > 10 else 2


# --- Constantes Globales (Presets) ---
# On les définit après les classes pour pouvoir instancier Rules

BELOTE_RULES = Rules(gamma=False, kappa=True, mu=True, alpha=True, epsilon=False, V=8, S=4, N=4)
BRIDGE_RULES = Rules(gamma=True, kappa=False, mu=False, alpha=True, epsilon=False, V=13, S=4, N=4)
TAROT_RULES  = Rules(gamma=True, kappa=True, mu=True, alpha=False, epsilon=True, V=14, S=4, N=4) # AC : pourquoi pas S=5 et N=5?

# --- Classes des Joueurs ---

class Player(ABC):
    def __init__(self, name: str, team: int):
        self.name = name
        self.team = team
        self.hand: List[Card] = []
        self.score = 0  # Attribut pour accumuler la récompense

    def set_team(self, new_team: int):
        """Permet de changer l'équipe dynamiquement (ex: Tarot)."""
        self.team = new_team

        # La méthode décrite dans l'article : celle qui "respecte les rules"
        # A VERIFIER DANS LE DETAIL ... PAS CERTAIN QUE TOUT SOIT CORRECT
        # trick : ce que les autres joueurs ont déjà joué
        # rules : the rules you have to respect
        # trump_suit : couleur de l'atout
    def filter_legal_cards(self, trick: List[Tuple['Player', Card]], rules: Rules, trump_suit: int) -> List[Card]:
        if not trick: return self.hand[:] # personne n'a joué avant
        suit_led = trick[0][1].suit # couleur de la carte jouée par le 1er joueur
        
        # Référence de la carte la plus forte pour monter/couper
        trick_cards = [t[1] for t in trick] # les cartes jouées par les autres
        trumps_in_trick = [c for c in trick_cards if c.suit == trump_suit] # les atouts joués par les autres
        
        if trumps_in_trick: # un joueur précédent a joué de l'atout
            highest_ref = max(trumps_in_trick, key=lambda x: x.value)  # valeur du plus grand atout joué
        else:
            # valeur de la plus grande carte de la couleur demandée
            # Attention au cas où aucun joueur précédent n'a joué cette couleur, dans ce cas pas de highest_ref
            followed = [c for c in trick_cards if c.suit == suit_led]
            highest_ref = max(followed, key=lambda x: x.value) if followed else None            

        cards_in_suit = [c for c in self.hand if c.suit == suit_led] # mes cartes de la couleur demandée
        trumps_in_hand = [c for c in self.hand if c.suit == trump_suit] # mes atouts de la couleur demandée
        # Remarque : si le 1er joueur a joué de l'atout, alors cards_in_suit et trumps_in_hand contiennent les mêmes cartes.

        if cards_in_suit:
            res = cards_in_suit
            # obligation de monter (AC : ajout 2nde condition)
            if rules.gamma or (suit_led == trump_suit and rules.mu) : 
                if highest_ref is not None:
                    higher = [c for c in cards_in_suit if c.value > highest_ref.value]
                    if higher: res = higher
            return res
        # sinon, est-ce que j'ai de l'atout ?
        elif trumps_in_hand and rules.kappa: # Obligation de couper
            res = trumps_in_hand
            # Obligation de surcouper (AC : ici on ne s'intéresse pas au partenaire ?)
            if rules.mu and trumps_in_trick:
                if highest_ref is not None:
                    higher_t = [c for c in trumps_in_hand if c.value > highest_ref.value]
                    if higher_t: res = higher_t
            return res
        # si on n'a pas appliqué de filtre
        return self.hand[:] # copie de self.hand

    @abstractmethod
    # Methode restant à implémenter.
    # Pour l'instant : aléatoire (pour l'avatar) ou lecture clavier (pour l'humain)
    def decide(self, legal_cards: List[Card]) -> Card: pass


    
class Random_Player(Player):
    def decide(self, legal_cards: List[Card]):
        # on choisit 1 carte aléatoirement parmi celles qui respectent les règles
        chosen = random.choice(legal_cards)
        self.hand.remove(chosen)
        return chosen


class Human_Player(Player):
    def decide(self, legal_cards: List[Card]):
        print(f"\n[VOTRE SCORE : {self.score}] - [VOTRE MAIN] : {self.hand}")
        # on propose les cartes qui respectent les règles
        for i, c in enumerate(legal_cards): print(f"{i}: {c} ({c.get_points()} pts)")
        while True:
            try:
                idx = int(input(f"Jouez une carte (0-{len(legal_cards)-1}) : "))
                chosen = legal_cards[idx]
                self.hand.remove(chosen)
                return chosen
            except: print("Choix invalide.")


# --- Logique de Jeu ---

def determine_winner(trick: List[Tuple[Player, Card]], trump_suit: int) -> int:
    suit_led = trick[0][1].suit # couleur de la 1ère carte jouée
    trumps = [(i, t[1]) for i, t in enumerate(trick) if t[1].suit == trump_suit]
    if trumps:
        return max(trumps, key=lambda x: x[1].value)[0] # Indice i, c'est le ième joueur dans ce tour qui a mis le meilleur atout (i n'est pas le nom du joueur)
    else:
        followed_suit = [(i, t[1]) for i, t in enumerate(trick) if t[1].suit == suit_led] # idem
        return max(followed_suit, key=lambda x: x[1].value)[0] # indice du joueur qui a mis la meilleure carte de la couleur demandée

def setup_players(rules: Rules, use_human=False) -> List[Player]:
    players = []
    for i in range(rules.N):
        # Par défaut, on peut dire que l'équipe est l'indice du joueur
        # Si epsilon=False (équipe fixe), on écrasera cela juste après
        initial_team = i 
        
        if i == 0 and use_human:
            player = Human_Player(name=f"Humain_{i}", team=initial_team)
        else:
            player = Random_Player(name=f"Ordi_{i}", team=initial_team)
        players.append(player)
    
    # CAS 1 : Équipes fixes (Belote, Bridge...)
    if not rules.epsilon:
        for i, p in enumerate(players):
            p.set_team(i % 2) # On force le 0-2 et 1-3
            
    return players


# pour simplifier, on suppose que le nb de cartes est divisible par le nombre de joueurs
def deal_cards(rules: Rules, players: List[Player]):
    """Distribue l'intégralité du deck aux joueurs."""
    # deck = produit cartésien Couleur * Valeur
    deck = [Card(suit=s, value=v) for s in range(1, rules.S + 1) for v in range(1, rules.V + 1)]
    # on mélange
    random.shuffle(deck)
    
    cards_per_player = len(deck) // rules.N
    for i, player in enumerate(players):
        start = i * cards_per_player
        end = start + cards_per_player
        player.hand = deck[start:end]

def determine_dynamic_teams(rules: Rules, players: List[Player], called_card: Card, taker: Player):
    """
    Réorganise les équipes en fonction d'une carte appelée (Règle epsilon=True).
    """
    print(f"\n--- Phase d'Appel : Le preneur {taker.name} appelle le {called_card} ---")

    # Pour l'instant, chaque joueur i est dans l'équipe i
    # Si on trouve un joueur qui a la carte appelée, il prendra le numero d'équipe du preneur.
    for j in players:
        # Si le joueur possède la carte dans sa main
        # On compare la valeur et la couleur
        if any(c.value == called_card.value and c.suit == called_card.suit for c in j.hand):
            j.set_team(taker.team)
            print(f"INFO : {j.name} est identifié comme le partenaire (détient la carte appelée).")
            return j # On retourne le partenaire trouvé
            
    print("INFO : Le preneur s'est appelé lui-même (jeu en solitaire).")
    return taker



def simulate_game(rules: Rules, use_human=False):
    # 1. Initialisation
    players = setup_players(rules, use_human) # par défaut, équipe des joueurs pairs et des joueurs impairs
    deal_cards(rules, players) # on distribue les cartes

    # 2. Gestion de l'équipe dynamique (Tarot / Epsilon=True)
    if rules.epsilon:
        # Exemple : Le joueur 0 est le preneur et appelle le Roi de Coeur (V=13, C=1)
        # Dans un vrai jeu, cela viendrait d'une phase d'enchères.
        king_hearts = Card(suit=1, value=13)
        determine_dynamic_teams(rules, players, king_hearts, players[0])

    # 3. Choix de l'atout    # Si atout fixe, on prend la couleur 0 -- AC : j'ai remplacé 1 par 0 ici
    # A REVOIR (je ne suis pas certain, revoir les regles des jeux pour les atouts dynamiques)
    trump_suit = 0 if not rules.alpha else random.randint(1, rules.S)
    
    print(f"--- DÉBUT DE LA PARTIE (Atout : couleur {trump_suit}) ---")

    leader_index = 0
    
    # 4. Boucle de jeu
    # On joue autant de plis qu'il y a de cartes par joueur
    while len(players[0].hand) > 0:
        current_trick = []
        # L'ordre change à chaque pli selon l'entameur
        ordered_players = [players[(leader_index + i) % rules.N] for i in range(rules.N)]

        # Pour chaque joueur dans l'ordre du pli
        for j in ordered_players:
            legals = j.filter_legal_cards(current_trick, rules, trump_suit)
            card = j.decide(legals)
            current_trick.append((j, card))
            print(f"{j.name} joue {card}")

        # Détermination du gagnant et Calcul des points du pli
        idx_v = determine_winner(current_trick, trump_suit)
        winner = current_trick[idx_v][0]
        trick_value = sum(c.get_points() for _, c in current_trick)
        
        # Attribution de la récompense
        winner.score += trick_value
        print(f"*** {winner.name} remporte le pli (+{trick_value} pts) ***\n")
        
        leader_index = players.index(winner)

    # 5. Résultat final
    print("\n" + "="*30)
    print("      TABLEAU DES SCORES")
    print("="*30)
    ranking = sorted(players, key=lambda x: x.score, reverse=True)
    for j in ranking:
        print(f"{j.name.ljust(15)} : {j.score} points")
    print("="*30)




# Lancement
if __name__ == "__main__":
    # On peut tester avec BELOTE_RULES, BRIDGE_RULES ou TAROT_RULES
    simulate_game(BELOTE_RULES, use_human=False)

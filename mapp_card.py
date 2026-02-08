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



# --- Structures de base ---

@dataclass
class Rules:
    gamma: bool = False  # Obligation de fournir la couleur
    kappa: bool = True   # Obligation de couper
    mu: bool = True      # Obligation de surcouper
    alpha: bool = True   # Atout dynamique
    epsilon: bool = False # Équipe fixe (0) ou dynamique (1)
    
    C: int = 4
    V: int = 8
    N: int = 4

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

BELOTE_RULES = Rules(gamma=False, kappa=True, mu=True, alpha=True, epsilon=False, V=8, C=4, N=4)
BRIDGE_RULES = Rules(gamma=True, kappa=False, mu=False, alpha=True, epsilon=False, V=13, C=4, N=4)
TAROT_RULES  = Rules(gamma=True, kappa=True, mu=True, alpha=False, epsilon=True, V=14, C=4, N=4)



# --- Classes des Joueurs ---

class Joueur(ABC):
    def __init__(self, nom: str, team: int):
        self.nom = nom
        self.team = team
        self.main: List[Card] = []
        self.score = 0  # Attribut pour accumuler la récompense

        # La méthode décrite dans l'article : celle qui "respecte les rules"
        # A VERIFIER DANS LE DETAIL ... PAS CERTAIN QUE TOUT SOIT CORRECT
    def filter_legal_cards(self, trick: List[Tuple['Joueur', Card]], rules: Rules, trump_suit: int) -> List[Card]:
        if not trick: return self.main[:]
        suit_led = trick[0][1].suit
        
        # Référence de la carte la plus forte pour monter/couper
        trick_cards = [t[1] for t in trick]
        trumps_in_trick = [c for c in trick_cards if c.suit == trump_suit]
        
        if trumps_in_trick:
            highest_ref = max(trumps_in_trick, key=lambda x: x.value)
        else:
            highest_ref = max([c for c in trick_cards if c.suit == suit_led], key=lambda x: x.value)

        cards_in_suit = [c for c in self.main if c.suit == suit_led]
        trumps_in_hand = [c for c in self.main if c.suit == trump_suit]

        if cards_in_suit:
            res = cards_in_suit
            if rules.gamma:
                higher = [c for c in cards_in_suit if c.value > highest_ref.value]
                if higher: res = higher
            return res
        elif trumps_in_hand and rules.kappa:
            res = trumps_in_hand
            if rules.mu and trumps_in_trick:
                higher_t = [c for c in trumps_in_hand if c.value > highest_ref.value]
                if higher_t: res = higher_t
            return res
        return self.main[:]

    @abstractmethod
    # Methode restant à implémenter.
    # Pour l'instant : aléatoire (pour l'avatar) ou lecture clavier (pour l'humain)
    def decide(self, legal_cards: List[Card]) -> Card: pass


    
class JoueurIA(Joueur):
    def decide(self, legal_cards: List[Card]):
        chosen = random.choice(legal_cards)
        self.main.remove(chosen)
        return chosen


class JoueurHumain(Joueur):
    def decide(self, legal_cards: List[Card]):
        print(f"\n[VOTRE SCORE : {self.score}] - [VOTRE MAIN] : {self.main}")
        for i, c in enumerate(legal_cards): print(f"{i}: {c} ({c.get_points()} pts)")
        while True:
            try:
                idx = int(input(f"Jouez une carte (0-{len(legal_cards)-1}) : "))
                chosen = legal_cards[idx]
                self.main.remove(chosen)
                return chosen
            except: print("Choix invalide.")


# --- Logique de Jeu ---

def determiner_vainqueur(pli: List[Tuple[Joueur, Card]], trump_suit: int) -> int:
    suit_led = pli[0][1].suit
    trumps = [(i, t[1]) for i, t in enumerate(pli) if t[1].suit == trump_suit]
    if trumps:
        return max(trumps, key=lambda x: x[1].value)[0]
    else:
        followed_suit = [(i, t[1]) for i, t in enumerate(pli) if t[1].suit == suit_led]
        return max(followed_suit, key=lambda x: x[1].value)[0]


def setup_players(rules: Rules, use_human=False) -> List[Joueur]:
    """Crée la liste des joueurs (objets IA ou Humain)."""
    players = []
    for i in range(rules.N):
        if i == 0 and use_human:
            player = JoueurHumain(nom=f"Humain_{i}", team=(i % 2))
        else:
            player = JoueurIA(nom=f"AI_{i}", team=(i % 2))
        players.append(player)
    return players


def deal_cards(rules: Rules, players: List[Joueur]):
    """Distribue l'intégralité du deck aux joueurs."""
    deck = [Card(suit=c, value=v) for c in range(1, rules.C + 1) for v in range(1, rules.V + 1)]
    random.shuffle(deck)
    
    cards_per_player = len(deck) // rules.N
    for i, player in enumerate(players):
        start = i * cards_per_player
        end = start + cards_per_player
        player.main = deck[start:end]



def simulate_game(rules: Rules, use_human=False):
    # 1. Initialisation
    joueurs = setup_players(rules, use_human) 
    deal_cards(rules, joueurs)

    # Si atout fixe, on prend la couleur 1
    # A REVOIR (je ne suis pas certain, revoir les regles des jeux pour les atouts dynamiques)
    trump_suit = 1 if not rules.alpha else random.randint(1, rules.C)
    
    print(f"--- DÉBUT DE LA PARTIE (Atout : couleur {trump_suit}) ---")

    entameur_index = 0 
    
    # 2. Boucle de jeu
    # On joue autant de plis qu'il y a de cartes par joueur
    while len(joueurs[0].main) > 0:
        pli_actuel = []
        # L'ordre change à chaque pli selon l'entameur
        ordre = [joueurs[(entameur_index + i) % rules.N] for i in range(rules.N)]

        # Pour chaque joueur dans l'ordre du pli
        for j in ordre:
            legales = j.filter_legal_cards(pli_actuel, rules, trump_suit)
            carte = j.decide(legales)
            pli_actuel.append((j, carte))
            print(f"{j.nom} joue {carte}")

        # Calcul des points du pli
        idx_v = determiner_vainqueur(pli_actuel, trump_suit)
        vainqueur = pli_actuel[idx_v][0]
        points_du_pli = sum(c.get_points() for _, c in pli_actuel)
        
        # Attribution de la récompense
        vainqueur.score += points_du_pli
        print(f"*** {vainqueur.nom} remporte le pli (+{points_du_pli} pts) ***\n")
        
        entameur_index = joueurs.index(vainqueur)

    # 3. Résultat final
    print("\n" + "="*30)
    print("      TABLEAU DES SCORES")
    print("="*30)
    joueurs_classes = sorted(joueurs, key=lambda x: x.score, reverse=True)
    for j in joueurs_classes:
        print(f"{j.nom.ljust(15)} : {j.score} points")
    print("="*30)




# Lancement
if __name__ == "__main__":
    # On peut tester avec BELOTE_RULES, BRIDGE_RULES ou TAROT_RULES
    simulate_game(BELOTE_RULES, use_human=False)

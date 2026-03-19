"""
Tests simples de filter_legal_cards
Jeu réduit : 2 couleurs (1=normale, 2=atout), valeurs 1 à 5
"""

from mapp_card import Card, Rules, Random_Player

# --- Helpers ---

def make_player(cards):
    """Crée un joueur Random avec une main fixée."""
    p = Random_Player(name="Test", team=0)
    p.hand = cards
    return p

def make_trick(cards_with_suits_values):
    """
    Crée un pli factice (liste de tuples (joueur_fictif, carte)).
    cards_with_suits_values : liste de (suit, value)
    """
    dummy = Random_Player(name="Dummy", team=1)
    dummy.hand = []
    return [(dummy, Card(suit=s, value=v)) for s, v in cards_with_suits_values]

def show_test(title, player, trick, rules, trump_suit):
    """Affiche proprement le résultat d'un test."""
    print(f"\n{'='*55}")
    print(f"  {title}")
    print(f"{'='*55}")
    print(f"  Main          : {player.hand}")
    trick_str = [f"S{s}:V{v}" for _, c in trick for s, v in [(c.suit, c.value)]]
    print(f"  Pli en cours  : {trick_str}")
    print(f"  Atout         : couleur {trump_suit}")
    print(f"  Règles        : gamma={rules.gamma} kappa={rules.kappa} mu={rules.mu}")
    result = player.filter_legal_cards(trick, rules, trump_suit)
    print(f"  --> Cartes légales : {result}")

# --- Règles utilisées dans les tests ---

RULES_STANDARD = Rules(gamma=False, kappa=True,  mu=True,  S=2, V=5, N=4)
RULES_GAMMA    = Rules(gamma=True,  kappa=True,  mu=True,  S=2, V=5, N=4)
RULES_NO_KAPPA = Rules(gamma=False, kappa=False, mu=False, S=2, V=5, N=4)

TRUMP = 2  # couleur 2 = atout dans tous les tests

# ================================================================
# CAS 1 : Pli vide -> toutes les cartes sont légales
# ================================================================
show_test(
    "CAS 1 : Pli vide -> toute la main",
    make_player([Card(1,3), Card(1,5), Card(2,2)]),
    trick=[],
    rules=RULES_STANDARD,
    trump_suit=TRUMP
)

# ================================================================
# CAS 2 : J'ai la couleur demandée, pas d'obligation de monter
# ================================================================
show_test(
    "CAS 2 : Couleur demandée, gamma=False -> fournir la couleur",
    make_player([Card(1,2), Card(1,4), Card(2,3)]),
    trick=make_trick([(1,3)]),        # quelqu'un a joué S1:V3
    rules=RULES_STANDARD,
    trump_suit=TRUMP
)

# ================================================================
# CAS 3 : J'ai la couleur demandée, obligation de monter (gamma)
# ================================================================
show_test(
    "CAS 3 : Couleur demandée, gamma=True -> seulement les cartes > V3",
    make_player([Card(1,2), Card(1,4), Card(1,5), Card(2,3)]),
    trick=make_trick([(1,3)]),        # quelqu'un a joué S1:V3
    rules=RULES_GAMMA,
    trump_suit=TRUMP
)

# ================================================================
# CAS 4 : Obligation de monter mais impossible (toutes mes cartes sont plus faibles)
# ================================================================
show_test(
    "CAS 4 : gamma=True mais je ne peux pas monter -> toute la couleur",
    make_player([Card(1,1), Card(1,2), Card(2,3)]),
    trick=make_trick([(1,5)]),        # quelqu'un a joué S1:V5 (le max)
    rules=RULES_GAMMA,
    trump_suit=TRUMP
)

# ================================================================
# CAS 5 : Pas la couleur demandée, obligation de couper (kappa)
# ================================================================
show_test(
    "CAS 5 : Pas la couleur, kappa=True -> je dois couper",
    make_player([Card(1,4), Card(2,2), Card(2,5)]),   # pas de S1, deux atouts
    trick=make_trick([(1,3)]),
    rules=RULES_STANDARD,
    trump_suit=TRUMP
)

# ================================================================
# CAS 6 : Pas la couleur, pas d'obligation de couper (kappa=False)
# ================================================================
show_test(
    "CAS 6 : Pas la couleur, kappa=False -> toute la main",
    make_player([Card(1,4), Card(2,2), Card(2,5)]),
    trick=make_trick([(1,3)]),
    rules=RULES_NO_KAPPA,
    trump_suit=TRUMP
)

# ================================================================
# CAS 7 : Quelqu'un a déjà coupé, obligation de surcouper (mu)
# ================================================================
show_test(
    "CAS 7 : Déjà coupé S2:V3, mu=True -> je dois surcouper",
    make_player([Card(2,1), Card(2,4), Card(2,5)]),   # que des atouts
    trick=make_trick([(1,3), (2,3)]),   # S1:V3 demandée, puis coupé avec S2:V3
    rules=RULES_STANDARD,
    trump_suit=TRUMP
)

# ================================================================
# CAS 8 : Déjà coupé mais je ne peux pas surcouper
# ================================================================
show_test(
    "CAS 8 : Déjà coupé S2:V4, mu=True mais impossible -> tout l'atout",
    make_player([Card(2,1), Card(2,2), Card(2,3)]),   # atouts tous < V4
    trick=make_trick([(1,3), (2,4)]),
    rules=RULES_STANDARD,
    trump_suit=TRUMP
)

# ================================================================
# CAS 9 : Aucune couleur demandée, aucun atout -> toute la main
# ================================================================
show_test(
    "CAS 9 : Pas la couleur, pas d'atout -> défausse libre",
    make_player([Card(1,4), Card(1,5)]),               # que de la couleur 1
    trick=make_trick([(1,3)]),                         # mais la couleur 1 est demandée... 
    rules=RULES_STANDARD,
    trump_suit=TRUMP
)
# Note : ce cas ne déclenche pas la défausse libre car le joueur A la couleur.
# Pour une vraie défausse : couleur demandée=1, main=que de la couleur 3 (ni demandée ni atout)

# ================================================================
# CAS 10 : Défausse libre réelle (ni couleur ni atout)
# ================================================================
show_test(
    "CAS 10 : Vraie défausse (pas couleur, pas atout) -> toute la main",
    make_player([Card(1,2), Card(1,5)]),               # couleur 1 uniquement
    trick=make_trick([(2,3)]),                         # couleur demandée = 2 (atout ici)
    rules=RULES_STANDARD,
    trump_suit=TRUMP
)
# Ici suit_led=2=trump_suit, cards_in_suit = atouts, donc on rentre dans le 1er cas.
# Pour une vraie défausse, il faudrait une 3ème couleur non-atout.

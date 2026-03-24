from mapp_card import *

# Lancement
if __name__ == "__main__":
    # On peut tester avec BELOTE_RULES, BRIDGE_RULES ou TAROT_RULES
    print("********** BELOTE RULES **********")
    for i in range(100000):
        simulate_game(BELOTE_RULES, use_human=False)
    print("********** BRIDGE RULES **********")
    for i in range(100000):
        simulate_game(BRIDGE_RULES, use_human=False)
    print("********** TAROT RULES **********")
    for i in range(100000):
        simulate_game(TAROT_RULES, use_human=False)

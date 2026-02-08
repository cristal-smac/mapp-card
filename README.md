# mapp-card
Multi-Agent Play Policy for Card games

Ce travail présente MAPP-CARD (Multi-Agent Play Policy for CARD games), un environnement de simulation et d'apprentissage conçu pour l'étude des jeux de plis internationaux. L'originalité de ce framework réside dans l'abstraction complète des mécaniques de jeu via une signature universelle. Cette approche permet d'unifier, sous un moteur unique, des jeux aux dynamiques variées tels que la Belote, le Bridge, le Tarot ou le Sheng Ji chinois.

Le système ne se contente pas de simuler des règles ; il définit une architecture de coopération hybride. En séparant strictement la logique légale (le moteur de contraintes) de la logique décisionnelle (les agents), MAPP-CARD permet :
- L'interopérabilité des joueurs : Des agents autonomes et des avatars humains peuvent cohabiter et collaborer au sein d'une même partie.
- La flexibilité de substitution : Un joueur humain peut être remplacé en temps réel par un agent sans rupture de la continuité logique du jeu.
- Un terrain d'entraînement pour le MARL : Bien que le moteur actuel utilise des politiques de décision simplifiées, il est spécifiquement structuré pour l'intégration d'algorithmes de type MAPPO, visant l'émergence d'une intelligence collective capable d'inférer les intentions des partenaires à travers le prisme de règles changeantes.

En offrant une plateforme capable de simuler un spectre quasi infini de variantes de jeux de plis, MAPP-CARD pose les jalons d'une IA véritablement généraliste dans le domaine des jeux à information imparfaite.

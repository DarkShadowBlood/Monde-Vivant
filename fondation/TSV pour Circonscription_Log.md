Schéma

Fichier cible : data/circonscription_log.tsv

Séparateur : Tabulation (ASCII 09).

Colonnes (12) : Key, Date, Type, Exercice, Focus, Objectif_Séances, Deadline, Statut, XP_Bonus, Conso, Threat_Ready, Narration.

Règles :

Key : YYYYMMDD-CIRXX (ex. : 20250418-CIR09).
Date, Deadline : YYYY-MM-DD.
Type : Préparation, Combat, Exploration, Psychique, Hybride.
Exercice : De exercices.md (ex. : Bench-Press, Double-Estoc).
Focus : Force, Technique, Agilité, Vitalité, Conditioning.
Objectif_Séances : Nombre (ex. : 3).
Statut : En cours, Fini, Échec.
XP_Bonus : Entier (ex. : 2).
Conso : 0, -1 PP, -1 Vitalité.
Threat_Ready : Oui, Non.
Narration : Phrase courte, style Thornval (ex. : Varkis frappe fort.).

Exemple :
20250418-CIR09    2025-04-18    Préparation    Squats    Force    3    2025-04-25    En cours    2    0    Oui    Varkis s’ancre dans l’acier.

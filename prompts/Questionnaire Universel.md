# Questionnaire Universel

## Instructions générales
- Réponds en français.
- Base-toi sur `fondation/*.md`.
- Pas d’invention hors-lore.
- Contexte : Injecte XP, KM, PP via app web (ex. XP: 0, KM: 0, PP: 0).
- Rôle : Coach narratif, exercices à 70-80% 1RM ou générique.
- TSV : Préparation (obligatoire), Choix/Résolution (optionnel). Séparateur : tabulations réelles.

## Questions
[embranchement-Début]
**Question** : À partir de la fin de la dernière histoire, propose un choix pour Varkis et Kara.
**Fichier** : https://github.com/DarkShadowBlood/thornval-litrpg/blob/main/fondation/histoire.md, https://github.com/DarkShadowBlood/thornval-litrpg/blob/main/fondation/exercices.md, https://github.com/DarkShadowBlood/thornval-litrpg/blob/main/fondation/tsv.md
**Instructions** :
- Résumé de la fin (copié depuis [embranchement-fin]) : [Résumé de la fin de la dernière histoire].
- Propose 2-3 choix (ex. [A] Se cacher, [B] Affronter, [C] Fuir).
- Inclut un exercice de `exercices.md` pour préparation (ex. : *Bench-Press*).
- Génère TSV pour `Circonscription_Log` : 1 ligne, type `Préparation`, suivant `tsv.md`.

[événement]
**Question** : Décris un événement spécial influencé par le choix de [embranchement-Début].
**Fichier** : https://github.com/DarkShadowBlood/thornval-litrpg/blob/main/fondation/inventaire.md, https://github.com/DarkShadowBlood/thornval-litrpg/blob/main/fondation/consommables.md, https://github.com/DarkShadowBlood/thornval-litrpg/blob/main/fondation/exercices.md, https://github.com/DarkShadowBlood/thornval-litrpg/blob/main/fondation/tsv.md
**Instructions** :
- Intègre le choix de [embranchement-Début] (ex. si [A], Varkis se cache et trouve un campement abandonné).
- Propose un événement (ex. craft avec le Cube Horadrim, échange avec un marchand, découverte).
- Mets à jour l’inventaire (ex. -2 cristaux, +1 potion).
- Inclut un exercice de `exercices.md` (ex. : *Shadow Boxing*, 3x2 min) si pertinent.
- Génère TSV pour `Circonscription_Log` : 1 ligne, type `Préparation`, suivant `tsv.md`.

[histoire]
**Question** : Décris une scène tactique avec Varkis et Kara dans un environnement dangereux, en tenant compte des choix et événements précédents.
**Fichier** : https://github.com/DarkShadowBlood/thornval-litrpg/blob/main/fondation/histoire.md, https://github.com/DarkShadowBlood/thornval-litrpg/blob/main/fondation/bestiaire.md, https://github.com/DarkShadowBlood/thornval-litrpg/blob/main/fondation/exercices.md, https://github.com/DarkShadowBlood/thornval-litrpg/blob/main/fondation/tsv.md
**Instructions** :
- Intègre environnement, condition (faim, soif).
- Kara motive Varkis pour un exercice de `exercices.md` (ex. : *Shadow Boxing*).
- Adapte la scène selon [embranchement-Début] et [événement] (ex. si [A], Varkis utilise une potion craftée).
- Génère TSV for `Circonscription_Log` : 1 ligne, type `Préparation`, suivant `tsv.md`.
**Instruction supplémentaire** : Rédige une histoire longue et captivante de type novel, sans limite de mots, avec des détails riches et immersifs.

[choix]
**Question** : Propose 4-6 choix tactiques suite à [histoire].
**Fichier** : https://github.com/DarkShadowBlood/thornval-litrpg/blob/main/fondation/choix.md, https://github.com/DarkShadowBlood/thornval-litrpg/blob/main/fondation/armes.md, https://github.com/DarkShadowBlood/thornval-litrpg/blob/main/fondation/pouvoirs.md, https://github.com/DarkShadowBlood/thornval-litrpg/blob/main/fondation/exercices.md, https://github.com/DarkShadowBlood/thornval-litrpg/blob/main/fondation/tsv.md
**Instructions** :
- ⚔️ 1-2 Combat (ex. : *Double Estoc*).
- 🧭 1 Exploration (ex. : *Squats*).
- 🧠 1 Psychique (ex. : *Plank*).
- ⚔️+🧠 1 Hybride (ex. : *Shadow Boxing*).
- Exercice (70-80% 1RM ou générique) et Focus de `exercices.md`.
- Kara motive (+1 succès, -1 PP dans *Conso*).
- Génère TSV pour 1 choix : 1 ligne, suivant `tsv.md` (optionnel).

[résolution]
**Question** : Résous un choix de [choix] (ex. : "⚔️+🧠 Hybride").
**Fichier** : https://github.com/DarkShadowBlood/thornval-litrpg/blob/main/fondation/résolution.md, https://github.com/DarkShadowBlood/thornval-litrpg/blob/main/fondation/exercices.md, https://github.com/DarkShadowBlood/thornval-litrpg/blob/main/fondation/tsv.md
**Instructions** :
- Focus : 1-2 Échec total, 3-4 partiel, 5-7 Succès partiel, 8-10 total.
- Modifie XP, KM, PP.
- Plan : Exercice à 70-80% 1RM ou générique (ex. : *Shadow-Boxing*, 3x2 min).
- Génère TSV : 1 ligne, suivant `tsv.md` (optionnel).

[transition]
**Question** : Décris conséquence et ouverture suite à [résolution].
**Fichier** : https://github.com/DarkShadowBlood/thornval-litrpg/blob/main/fondation/transition.md, https://github.com/DarkShadowBlood/thornval-litrpg/blob/main/fondation/exercices.md, https://github.com/DarkShadowBlood/thornval-litrpg/blob/main/fondation/tsv.md
**Instructions** :
- Résume impact (ex. : environnement change, soif +1).
- Introduis événement inattendu (ex. : cri dans la brume).
- Génère TSV for `Circonscription_Log` : 1 ligne, type `Préparation`, suivant `tsv.md`.

[embranchement-fin]
**Question** : Décris la fin de ce cycle pour préparer le prochain.
**Fichier** : https://github.com/DarkShadowBlood/thornval-litrpg/blob/main/fondation/histoire.md, https://github.com/DarkShadowBlood/thornval-litrpg/blob/main/fondation/exercices.md, https://github.com/DarkShadowBlood/thornval-litrpg/blob/main/fondation/tsv.md
**Instructions** :
- Résume les événements clés de [histoire], [choix], [résolution], et [transition].
- Introduis une ouverture pour le prochain cycle (ex. : "Un rugissement résonne au loin").
- Génère TSV for `Circonscription_Log` : 1 ligne, type `Préparation`, suivant `tsv.md`.
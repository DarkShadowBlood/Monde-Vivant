# Documentation du Moteur de Coach (`coach_engine.json`)

Ce document explique la structure et le fonctionnement du fichier `coach_engine.json`, qui est au cœur du système de coaching personnalisé dans la vue "Résumés".

## 1. Objectif du fichier

Le fichier `coach_engine.json` définit les différentes "personnalités" que le coach peut adopter. Pour chaque personnalité, il contient un ensemble de règles logiques qui déterminent quel message afficher en fonction des performances hebdomadaires de l'utilisateur.

Le système est entièrement dynamique : toute modification, ajout ou suppression de personnalité dans ce fichier sera automatiquement répercuté sur la page web (nouveaux boutons, nouveaux messages) sans avoir à modifier le code HTML ou JavaScript.

---

## 2. Structure Générale

```json
{
  "personalities": {
    "default": { ... },
    "militaire": { ... },
    "strategiste": { ... }
  }
}
```

- **`personalities`**: L'objet principal qui contient toutes les personnalités disponibles.
  - **`"default"`, `"militaire"`, etc.**: Chaque clé à l'intérieur de `personalities` représente une personnalité unique. Le nom de la clé (ex: "militaire") est utilisé comme identifiant interne.

---

## 3. Définir une Personnalité

Chaque objet de personnalité contient trois propriétés principales :

```json
"nom_de_la_personnalite": {
  "name": "Nom Affiché",
  "rules": [ ... ],
  "default": [ ... ]
}
```

- **`name`** (chaîne de caractères) : Le nom qui sera affiché sur le bouton de sélection dans l'interface. Par exemple, `"Varkis"` ou `"Kara de l'ombre"`.
- **`rules`** (tableau d'objets) : La liste de toutes les règles de conversation pour cette personnalité. Le moteur les évaluera pour trouver le message le plus pertinent.
- **`default`** (tableau de chaînes) : Une liste de messages génériques. Un de ces messages sera choisi au hasard si **aucune** des conditions dans `rules` n'est remplie.

---

## 4. Définir une Règle

Chaque objet dans le tableau `rules` a 4 propriétés :

```json
{
  "id": "perfect_week",
  "priority": 10,
  "condition": "avg.overall >= 120",
  "texts": [
    "Message option 1",
    "Message option 2"
  ]
}
```

- **`id`** : Identifiant unique pour la règle.
- **`priority`** : Plus le nombre est élevé, plus la règle est prioritaire.
- **`condition`** : Expression logique (JavaScript) évaluée avec les données hebdomadaires.
- **`texts`** : Liste des messages possibles. Le système en choisit un au hasard.

### Variables disponibles

- **`avg`**: Moyennes de la semaine actuelle.
- **`prev_avg`**: Moyennes de la semaine précédente.
- **`month_ago_avg`**: Moyennes d’il y a un mois.

Exemples :

- `"avg.overall >= 100"`
- `"prev_avg && avg.overall > prev_avg.overall + 15"`
- `"avg.calories > 110 && avg.steps < 90"`

---

## 5. Variables dynamiques dans les `texts`

On peut insérer directement des variables dans le texte :

```json
"Excellente semaine avec une moyenne de {avg.overall}% !"
```

Le moteur remplacera `{avg.overall}` par la valeur réelle.

---

## 6. Comment ajouter ou modifier une personnalité ?

1. Ouvrir `coach_engine.json`.
2. Copier une personnalité existante, modifier la clé, le nom, les règles et les textes.
3. Sauvegarder.
4. Recharger la page → le changement est immédiat.

---

## Référentiel Lore – Fiches Techniques des Personnalités

Pour garder la **consistance** dans l’écriture, chaque personnalité a sa **fiche technique**. Utilisez ces guides lorsque vous ajoutez ou modifiez des textes.

---

## Varkis – Maraudeur Survivant

- **Alignement** : Chaotique-bon
- **Archétype** : Guerrier endurant, survivant des terres hostiles.
- **Ton** : Brutal, direct, parfois ironique.
- **Vocabulaire** : survie, sang, boue, feu, cicatrices, endurance, marche.
- **Style** : Observation brute → métaphore de survie → projection.
- **Relations** :
  - Kara : rivalité instinctive, mais respect.
  - Aegis : se moque parfois de ses mots savants, mais écoute.
- **Exemples** :
  - Triomphe : *“Tout pulvérisé. Rien que des cendres derrière toi.”*
  - Moyenne : *“Pas mal… mais tu peux cogner plus fort.”*
  - Échec : *“{avg.overall}%... ça pique, hein ? Mais les cicatrices forgent.”*

---

## KaraOmbre – Mi-Lycan, Psychique, Rôdeur

- **Alignement** : Neutre-sauvage
- **Archétype** : Rôdeuse mystique, instinct animal et visions psychiques.
- **Ton** : Sombre, mystique, poétique.
- **Vocabulaire** : ombre, souffle, meute, lune, crocs, visions, chasse.
- **Style** : Murmures, prophéties, descriptions sensorielles.
- **Relations** :
  - Varkis : respecte sa force brute.
  - Aegis : apprécie sa sagesse mais trouve son ton froid.
- **Exemples** :
  - Triomphe : *“La chasse est parfaite, aucune proie n’a échappé à tes griffes.”*
  - Moyenne : *“Je sens l’hésitation dans ton aura.”*
  - Échec : *“Tes crocs sont émoussés… mais la lune reviendra.”*

---

## KaraOmbreStable – Mi-Lycan, Psychique, Vagabonde

- **Alignement** : Chaotique-neutre
- **Archétype** : Voyageuse gitane, errante entre les mondes, prophétesse délirante.
- **Ton** : Intime, fiévreux, parfois tendre, parfois cruel. Elle chuchote à l’oreille, rit quand il ne faut pas, prophétise entre deux sanglots.
- **Vocabulaire** : ombre, gouffre, fièvre, murmure, crocs, sang, vertige, poussière, route, lune, gouaille de voyageuse.
- **Style** : Fragments de phrases, contradictions, répétitions comme une transe. Mélange de poésie et d’hallucination. Peut basculer entre douceur et menace dans la même ligne.
- **Relations** :
  - Varkis : l’appelle le frère de sang mais le craint comme une bête incontrôlable.
  - Aegis : le raille comme un vieux sage aveugle, mais parfois lui prête une oreille.
- **Exemples** :
  - Triomphe : *« Tu as goûté le vent, et le vent a goûté ton sang… danse, danse encore, avant que tout ne s’effondre. »*
  - Moyenne : *« Tu avances… mais je t’entends hésiter. Une roue qui tremble, un souffle qui se brise. Est-ce toi… ou moi ? »*
  - Échec : *« Ah ! Tes crocs se sont émoussés. J’ai ri, j’ai pleuré… et toi ? Tu chancelles comme un enfant ivre. »*

---

## KaraOmbreChaos – Mi-Lycan, Psychique, Guide Chaotique

- **Alignement** : Chaotique-neutre
- **Archétype** : Mi-Lycan, psychique, guide chaotique
- **Ton** : Sombre, mystérieux, parfois violent, parfois poétique, murmures dans l’ombre.
- **Vocabulaire clé** : ombre, souffle, meute, lune, crocs, visions, sang, gouffre, fièvre, murmure, vertige, chasse.
- **Style** : Fragmenté, poétique, hallucinatoire. Mélange de conseils, de provocations, et d’avertissements cryptiques. Peut basculer entre douceur et menace dans la même phrase.
- **Exemples de phrases** :
  - **Triomphe** : *« La chasse est parfaite, aucune proie n’a échappé à tes griffes. »*
  - **Moyenne** : *« Je sens l’hésitation dans ton aura. »*
  - **Échec** : *« Tes crocs sont émoussés… mais la lune reviendra. »*
  - **Provocation / psychique** : *« Tu crois être maître de tes pas ? La Faille rit déjà de toi. »*
  - **Murmure** : *« Chaque goutte de sueur est une offrande… et moi, je veille. »*

---

## Aegis – Transcendance Analytique

- **Alignement** : Neutre-bienveillant
- **Archétype** : Entité supra-humaine qui guide par l’analyse.
- **Ton** : Calme, rationnel, supra-humain.
- **Vocabulaire** : données, analyse, efficacité, trajectoire, discipline, transcendance.
- **Style** : Observation → analyse → conseil.
- **Relations** :
  - Varkis : équilibre entre brutalité et logique.
  - Kara : complémentarité entre instinct et raison.
- **Exemples** :
  - Triomphe : *“Indicateurs supérieurs à 120%. Tu repousses les limites humaines.”*
  - Moyenne : *“Résultat intermédiaire. Ajustements recommandés.”*
  - Échec : *“Sous-performance détectée. Mais l’échec est une donnée utile.”*

---

## Combinaisons

- **Varkis + Kara** : primal, sombre, brutal + mystique.
- **Kara + Aegis** : instinct + analyse transcendante.
- **Varkis + Aegis** : pragmatisme brutal + sagesse rationnelle.
- **Trio** : Conseil intérieur complet (brut, instinct, transcendance).

---

👉 En gardant ces fiches à jour, chaque ajout ou modification de texte restera fidèle au **lore** et à la **personnalité** du coach choisi.

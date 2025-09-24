# Documentation du Moteur de Coach (`coach_engine.json`)

Ce document explique la structure et le fonctionnement du fichier `coach_engine.json`, qui est au cœur du système de coaching personnalisé dans la vue "Résumés".

## 1. Objectif du fichier

Le fichier `coach_engine.json` définit les différentes "personnalités" que le coach peut adopter. Pour chaque personnalité, il contient un ensemble de règles logiques qui déterminent quel message afficher en fonction des performances hebdomadaires de l'utilisateur.

Le système est entièrement dynamique : toute modification, ajout ou suppression de personnalité dans ce fichier sera automatiquement répercuté sur la page web (nouveaux boutons, nouveaux messages) sans avoir à modifier le code HTML ou JavaScript.

---

## 2. Structure Générale

Le fichier a une structure JSON simple :

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

C'est ici que la logique du coach prend vie. Chaque objet dans le tableau `rules` a 4 propriétés :

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

- **`id`** (chaîne de caractères) : Un nom unique et descriptif pour la règle. Utile pour le débogage.
- **`priority`** (nombre) : Un chiffre qui définit l'importance de la règle. Si plusieurs conditions sont vraies, **seule la règle avec la plus haute priorité sera choisie**.
- **`condition`** (chaîne de caractères) : Une expression logique JavaScript qui sera évaluée. Si elle retourne `true`, la règle est activée.
- **`texts`** (tableau de chaînes) : La liste des messages possibles pour cette règle. Le système en choisira un au hasard.

### Variables disponibles dans `condition`

La condition est évaluée avec un contexte de données qui inclut :

- **`avg`**: Objet contenant les pourcentages moyens de la **semaine actuelle**.
  - `avg.calories`
  - `avg.steps`
  - `avg.distance`
  - `avg.overall` (moyenne des 3 autres)

- **`prev_avg`**: Objet contenant les pourcentages moyens de la **semaine précédente**. Il peut être `null` s'il n'y a pas de données pour la semaine d'avant.
  - `prev_avg.calories`
  - `prev_avg.steps`
  - `prev_avg.distance`
  - `prev_avg.overall`

**Exemples de conditions :**

- `"avg.overall >= 100"` : La moyenne générale de la semaine est supérieure ou égale à 100%.
- `"avg.calories > 110 && avg.steps < 90"` : Les calories sont excellentes, mais les pas sont un peu bas.
- `"prev_avg && avg.overall > prev_avg.overall + 15"` : Il y a une progression de plus de 15 points par rapport à la semaine précédente (on vérifie que `prev_avg` existe avant de l'utiliser).

---

## 5. Variables dynamiques dans les `texts`

Vous pouvez insérer les valeurs de performance directement dans les messages en utilisant des accolades `{}`.

**Exemple :**
`"Excellente semaine avec une moyenne de {avg.overall}% !"`

Le système remplacera `{avg.overall}` par la valeur numérique correspondante (ex: 105). Vous pouvez utiliser toutes les variables disponibles dans les conditions (ex: `{avg.calories}`, `{prev_avg.overall}`).

---

## 6. Comment ajouter ou modifier une personnalité ?

1. Ouvrez le fichier `historique_objectifs/coach_engine.json`.
2. Pour **ajouter** une personnalité, copiez un bloc de personnalité existant (de `"nom_interne": {` à `}`), collez-le à la fin de la liste des personnalités, et modifiez la clé (`"strategiste"`), le `name` (`"Aegis"`) et les `rules`.
3. Pour **modifier** une personnalité, changez simplement les valeurs de `name`, `rules` ou `default`.
4. Sauvegardez le fichier.
5. Rechargez la page de l'historique, allez dans la vue "Résumés" et vos changements apparaîtront instantanément.

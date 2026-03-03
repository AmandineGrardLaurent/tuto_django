# Application de Sondages Django

Application de sondages réalisée avec Django permettant de créer des questions, de voter et de consulter des statistiques détaillées sur les votes.

---

## 🚀 Fonctionnalités

- Affichage de la liste des derniers sondages publiés (page d’accueil).

- Affichage de la liste complète de tous les sondages.

- Détail d’un sondage avec formulaire de vote.

- Affichage des résultats d’un sondage après le vote.

- Affichage de la fréquence des votes pour un sondage donné (pourcentages par choix).

- Page de création d’un sondage avec ses choix (formulaire + formset).

- Page de statistiques globales :
  - Nombre total de sondages

  - Nombre total de choix

  - Nombre total de votes

  - Moyenne de votes par sondage

  - Question la plus / moins populaire

  - Dernière question créée

- Interface d’administration personnalisée.

---

## 🧱 Structure de l’application

### `models.py`

- `Question`
  - Texte de la question
  - Date de publication
  - Méthodes utilitaires :
    - `was_published_recently`
    - `age`
    - `get_choices`
    - `get_max_choice`
- `Choice`
  - Choix associé à une question
  - Nombre de votes

### `forms.py`

- `QuestionForm` : création/édition d’une question (définit automatiquement `pub_date`).
- `ChoiceForm`
- `ChoiceFormSet`
  - Basé sur `inlineformset_factory`
  - Minimum 3 choix requis

### `views.py`

- Vues génériques :
  - `IndexView`
  - `AllView`
  - `DetailView`
  - `ResultsView`
  - `FrequencyView`
  - `StatisticsView`
- Vue fonctionnelle :
  - `vote`

### `admin.py`

- Configuration personnalisée :
  - Inlines
  - Filtres
  - Recherche
  - Colonnes custom

---

## ⚙️ Prérequis

- Python 3.13.7
- Django 5.2.11
- DB Browser for SQLite

---

## 💻 Installation

1. Cloner le dépôt :

   ```bash
   git clone https://github.com/AmandineGrardLaurent/tuto_django.git
   cd tuto_django/djangotutorial
   ```

2. Créer et activer un environnement virtuel :

   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. Installer les dépendances :

   ```bash
   pip install -r requirements.txt
   ```

4. Appliquer les migrations :

   ```bash
   python manage.py migrate
   ```

5. Lancer le serveur de développememt :

   ```bash
   python manage.py runserver
   ```

---

## 📁 Arborescence du projet

```
TUTO_DJANGO/
├── .idea/
├── .mypy_cache/
├── .venv/
├── djangotutorial/
│ ├── mysite/
│ │ ├── pycache/
│ │ ├── init.py
│ │ ├── asgi.py
│ │ ├── settings.py
│ │ ├── urls.py
│ │ └── wsgi.py
│ ├── polls/
│ │ ├── pycache/
│ │ ├── migrations/
│ │ ├── static/
│ │ ├── templates/
│ │ ├── init.py
│ │ ├── admin.py
│ │ ├── apps.py
│ │ ├── forms.py
│ │ ├── models.py
│ │ ├── tests.py
│ │ ├── urls.py
│ │ └── views.py
│ ├── static/
│ ├── templates/
│ │ ├── admin/
│ │ └── base.html
│ ├── .gitignore
│ ├── db.sqlite3
│ ├── manage.py
│ ├── docs/
│ ├── mypy.ini
│ └── README.md
```

---

## 🌐 Utilisation

- Accueil des sondages : http://localhost:8000/polls/ — derniers sondages publiés.

- Liste complète : http://localhost:8000/polls/all — tous les sondages.

- Création d'un sondage : http://localhost:8000/polls/add_poll — question + plusieurs choix (formset).

- Vote sur un sondage : accéder à la page de détail d'une question, sélectionner un choix puis valider.

- Résultats et fréquences : pages results et frequency pour un sondage donné.

- Statistiques globales : http://localhost:8000/polls/statistics.

- Interface d'administration : http://localhost:8000/admin/ pour gérer questions et choix.

---

## 🧠 Notes techniques

- Utilisation des vues génériques ListView et DetailView pour la plupart des pages.

- Mise à jour atomique des votes via F() dans la vue vote pour éviter les conditions de concurrence.

- Calcul de statistiques globales via aggregate et annotate (Sum) dans StatisticsView.

- Méthodes utilitaires dans le modèle Question pour calculer pourcentages, top choix, âge, etc.

- Formset ChoiceFormSet imposant un nombre minimum de choix pour chaque question.

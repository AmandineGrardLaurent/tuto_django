import datetime

from django.db import models
from django.db.models import Sum
from django.utils import timezone

MAX_LENGTH = 20


def text_excerpt(text, max_length):
    """
    Retourne un extrait du texte limité à `max_length` caractères.

    Si le texte dépasse la longueur maximale, ajoute '...' à la fin.

    :param text: Texte original
    :param max_length: Nombre maximum de caractères
    :return: Texte tronqué si nécessaire
    """
    return text[:max_length] + ('...' if len(text) > max_length else '')


class Question(models.Model):
    """
    Modèle représentant une question d'un sondage.

    Une question possède :
    - un texte
    - une date de publication
    - plusieurs choix associés (relation 1-n avec Choice)
    """

    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField("date published")

    def __str__(self):
        """
        Représentation texte de la question.

        Affiche la date de publication suivie d'un extrait du texte.
        """
        return "{} {}".format(self.pub_date, text_excerpt(self.question_text, MAX_LENGTH))

    def was_published_recently(self):
        """
        Indique si la question a été publiée dans les dernières 24 heures.

        :return: True si publiée dans la dernière journée, sinon False
        """
        return self.pub_date >= timezone.now() - datetime.timedelta(days=1)

    def age(self):
        """
        Retourne l'âge de la question (durée depuis sa publication).

        :return: timedelta représentant le temps écoulé depuis la publication
        """
        return timezone.now() - self.pub_date

    def get_choices(self):
        """
        Retourne la liste des choix avec leurs statistiques.

        Pour chaque choix :
        - texte du choix
        - nombre de votes
        - pourcentage par rapport au total

        :return: Liste de tuples (choice_text, votes, pourcentage)
        """
        resultat = self.choice_set.aggregate(total=Sum('votes'))
        total = resultat['total']

        if not total:
            return [(c.choice_text, c.votes, 0) for c in self.choice_set.all()]

        return [
            (c.choice_text, c.votes, (c.votes / total) * 100)
            for c in self.choice_set.all()
        ]

    def get_max_choice(self):
        """
        Retourne le choix ayant le plus grand pourcentage de votes.

        :return: Tuple (texte_du_choix, pourcentage)
        """
        choices = self.choice_set.all()
        resultat = self.choice_set.aggregate(total=Sum('votes'))
        total = resultat['total']

        if not total:
            return None, 0

        max_choice = max(choices, key=lambda c: c.votes / total)
        return max_choice.choice_text, max_choice.votes / total


class Choice(models.Model):
    """
    Modèle représentant un choix possible pour une question.

    Chaque choix est lié à une question et possède :
    - un texte
    - un nombre de votes
    """

    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)

    def __str__(self):
        """
        Représentation texte du choix.

        Retourne un extrait du texte du choix.
        """
        return text_excerpt(self.choice_text, MAX_LENGTH)
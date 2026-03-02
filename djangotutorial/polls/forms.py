from django import forms
from django.forms import inlineformset_factory
from django.utils import timezone
from .models import Question, Choice


class QuestionForm(forms.ModelForm):
    """
    Formulaire pour créer ou modifier une question de sondage.

    Ce formulaire est lié au modèle Question et contient :
    - question_text : le texte de la question
    - pub_date : date de publication définie automatiquement lors du save()
    """

    class Meta:
        """
        Classe interne pour configurer le ModelForm.

        - model : modèle lié (Question)
        - fields : liste des champs affichés dans le formulaire
        - error_messages : personnalisation des messages d'erreurs
        """
        model = Question
        fields = ["question_text"]
        error_messages = {
            'question_text': {
                'required': 'Vous devez saisir une question (obligatoire).',
                'max_length': 'La question est trop longue (max 200 caractères).'
            }
        }

    def save(self, commit=True):
        """
        Surcharge de la méthode save pour définir automatiquement la date de publication.

        :param commit (bool) : si True, enregistre l'objet en base de données.
        :return Question : instance du modèle Question sauvegardée ou prête à être sauvegardée
        """

        # Crée l'objet Question en mémoire sans l'enregistrer
        question = super().save(commit=False)

        # Définition de la date de publication
        question.pub_date = timezone.now()

        # Enregistrement si commit=True
        if commit:
            question.save()

        return question


class ChoiceForm(forms.ModelForm):
    """
    Formulaire pour créer ou modifier un choix associé à une question.

    Ce formulaire est lié au modèle Choice et contient :
    - choice_text : texte du choix
    """

    class Meta:
        """
        Classe interne pour configurer le ModelForm Choice.

        - model : modèle lié (Choice)
        - fields : liste des champs affichés
        - error_messages : messages d'erreur personnalisés
        """
        model = Choice
        fields = ['choice_text']
        error_messages = {
            'choice_text': {
                'required': 'Vous devez entrer un texte pour ce choix.',
                'max_length': 'Le choix est trop long (max 200 caractères).'
            }
        }


# Création du formset pour gérer plusieurs choix liés à une question
ChoiceFormSet = inlineformset_factory(
    # Modèle parent
    parent_model=Question,
    # Modèle enfant
    model=Choice,
    # Formulaire à utiliser pour chaque enfant
    form=ChoiceForm,
    # Champs à afficher pour chaque enfant
    fields=("choice_text",),
    # Nombre d'inputs vides supplémentaires affichés
    extra=2,
    # Nombre minimum de formulaires requis
    min_num=3,
    # Active la validation du minimum
    validate_min=True,
)

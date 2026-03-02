from django.db.models import F, Sum
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.utils import timezone
from django.views import generic
import logging
from .forms import QuestionForm, ChoiceFormSet
from .models import Choice, Question

# pour garder une trace des erreurs dans les logs
logger = logging.getLogger(__name__)

URL_POLL_FORM = "polls/poll_form.html"

"""
def index(request):
    latest_question_list = Question.objects.order_by("-pub_date")[:5]
    context = {"latest_question_list": latest_question_list}
    return render(request, "polls/index.html", context)

def detail(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    return render(request, "polls/detail.html", {"question": question})

def results(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    return render(request, "polls/results.html", {"question": question})
"""


class IndexView(generic.ListView):
    """
    Affiche la liste des derniers sondages publiés.

    Utilise le gabarit 'polls/index.html' et fournit les 5 questions
    les plus récentes sous la variable 'latest_question_list'.
    """
    template_name = "polls/index.html"
    context_object_name = "latest_question_list"

    def get_queryset(self):
        """ Retourne les cinq dernières questions publiées """
        return Question.objects.order_by("-pub_date")[:5]


class AllView(generic.ListView):
    """
    Affiche l'intégralité des sondages présents en base de données.

    Trié par identifiant (ID) croissant.
    """
    template_name = "polls/all.html"
    context_object_name = "question_list"

    def get_queryset(self):
        """Retourne toutes les questions triées par ID."""
        return Question.objects.order_by("id")


class DetailView(generic.DetailView):
    """
    Affiche le formulaire de vote pour une question spécifique.

    L'identifiant de la question est récupéré via l'URL (pk).
    """
    model = Question
    template_name = "polls/detail.html"


class ResultsView(generic.DetailView):
    """
    Affiche les résultats d'un sondage spécifique après un vote.
    """
    model = Question
    template_name = "polls/results.html"


class FrequencyView(generic.DetailView):
    """
    Affiche les statistiques détaillées (fréquences) d'un sondage.
    """
    model = Question
    template_name = "polls/frequency.html"


class StatisticsView(generic.ListView):
    """
    Vue globale calculant des statistiques transversales sur l'application.

    Cette vue calcule :
    - Le nombre total de questions, choix et votes.
    - La moyenne de votes par question.
    - La question la plus populaire (best_question).
    - La question la moins populaire (worst_question).
    """
    template_name = "polls/statistics.html"
    context_object_name = "question_list"

    def get_queryset(self):
        """Retourne la liste des questions pour affichage détaillé."""
        return Question.objects.order_by("id")

    def get_context_data(self, **kwargs):
        """
        Enrichit le contexte avec des agrégations et des annotations globales.
        """
        context = super().get_context_data(**kwargs)

        total_questions = Question.objects.count()
        total_votes = Choice.objects.aggregate(Sum('votes'))['votes__sum'] or 0
        total_choices = Choice.objects.count()

        # Calcul de la moyenne arithmétique de participation
        vote_average = (total_votes / total_questions) if total_questions > 0 else 0

        # Identification des extrêmes via l'annotation (calcul par ligne)
        # On ajoute une colonne virtuelle 'total_votes_count' pour trier les questions
        best_question = Question.objects.annotate(
            total_votes_count=Sum('choice__votes')
        ).order_by('-total_votes_count').first()
        worst_question = Question.objects.annotate(
            total_votes_count=Sum('choice__votes')
        ).order_by('-total_votes_count').last()

        last_question = Question.objects.order_by('id').last()

        context['choices_count'] = total_choices
        context['questions_count'] = total_questions
        context['votes_count'] = total_votes
        context['votes_average_by_question'] = vote_average
        context['best_question'] = best_question
        context['worst_question'] = worst_question
        context['last_question'] = last_question

        return context


def vote(request, question_id):
    """
    Gère la soumission d'un vote pour une question donnée.

    Vérifie la présence d'un choix dans les données POST.
    En cas de succès, incrémente le compteur de votes de manière atomique
    via F() et redirige vers la vue 'frequency'.

    :param request: L'objet HttpRequest
    :param question_id: L'ID de la question concernée
    :return: Une redirection vers les résultats ou un ré-affichage du formulaire avec erreur
    """
    question = get_object_or_404(Question, pk=question_id)
    try:
        selected_choice = question.choice_set.get(pk=request.POST["choice"])
    except (KeyError, Choice.DoesNotExist):
        # Ré-affiche le formulaire de vote avec un message d'erreur.
        return render(
            request,
            "polls/detail.html",
            {
                "question": question,
                "error_message": "Vous n'avez pas sélectionner votre choix.",
            },
        )
    else:
        # Utilisation de F() pour demander à la base de données d'incrémenter
        selected_choice.votes = F("votes") + 1
        selected_choice.save()

        # Redirection après succès POST pour éviter les doubles soumissions
        return HttpResponseRedirect(reverse("polls:frequency", args=(question.id,)))


def poll(request):
    """
    Vue pour créer une nouvelle question de sondage avec ses choix.

    Cette vue gère à la fois l'affichage du formulaire (GET) et la soumission (POST).

    Fonctionnement :
    1. Si la requête est POST :
        - Crée un QuestionForm avec les données soumises.
        - Si le formulaire Question est valide :
            - Crée un ChoiceFormSet lié à la question (mais non encore sauvegardé)
            - Si le formset est valide :
                - Enregistre la question avec la date de publication actuelle
                - Lie le formset à l'instance de la question et sauvegarde les choix
                - Redirige vers l'index des sondages
        - Si le formulaire Question n'est pas valide, on initialise un formset vide pour l'affichage.
    2. Si la requête est GET :
        - Crée un formulaire QuestionForm vide
        - Crée un ChoiceFormSet vide (avec les champs vides prédéfinis par extra)

    :param request (HttpRequest) : Objet contenant la requête HTTP (GET ou POST)
    :return : HttpResponse : rendu du formulaire ou redirection vers l'index après succès
    """

    # --- requête POST ---
    if request.method == "POST":
        # Création du formulaire Question avec les données POST
        form = QuestionForm(request.POST)
        if form.is_valid():
            # Crée un formset de Choice lié à l'instance Question (non encore sauvegardée)
            formset = ChoiceFormSet(request.POST, instance=form.save(commit=False))

            if formset.is_valid():
                # Enregistrement de la question avec date actuelle
                question = form.save(commit=False)
                question.pub_date = timezone.now()
                question.save()

                # Lie le formset à la question sauvegardée
                formset.instance = question
                # Enregistre tous les choix du formset
                formset.save()

                # Redirection vers la page d'accueil des sondages
                return redirect("polls:index")
        else:
            # Si QuestionForm invalide, on crée un formset vide pour affichage
            formset = ChoiceFormSet()

    # --- requête GET ---
    else:
        # formulaire vide pour la question
        form = QuestionForm()
        # formset vide pour les choix
        formset = ChoiceFormSet()

    # --- Rendu du template avec les formulaires ---
    return render(request, "polls/poll_form.html", {
        "form": form,
        "formset": formset
    })


"""
def poll(request):
    
    Gère la création d'un sondage : affiche le formulaire (GET)
    ou enregistre la question et redirige vers l'index (POST).

    :param request: L'objet HttpRequest.
    :return: HttpResponseRedirect vers l'index ou rendu du formulaire avec erreur.
    

    if request.method == "POST":
        try:
            # Récupération du formulaire
            text = request.POST.get("question_text")
            if not text or text.strip() == "":
                raise ValueError("La question ne peut pas être vide.")

            # Sauvegarde de la question
            new_question = Question.objects.create(
                question_text=text,
                pub_date=timezone.now()
            )

            # Récupération et création des choix (non vides)
            choices = request.POST.getlist("choice_text")
            for choice_text in choices:
                if choice_text.strip():
                    new_question.choice_set.create(
                        choice_text=choice_text,
                        votes=0
                    )

            # Redirection
            return redirect("polls:index")

        except ValueError as e:
            # Erreur de validation
            return render(request, URL_POLL_FORM, {
                "error_message": str(e)
            })
        except Exception as e:
            # Erreur imprévue
            logger.error(f"Erreur lors de la création du sondage : {e}")
            return render(request, URL_POLL_FORM, {
                "error_message": "Une erreur technique est survenue. Réessayez plus tard."
            })

    return render(request, URL_POLL_FORM, {"choice_range": range(1, 6)})
"""

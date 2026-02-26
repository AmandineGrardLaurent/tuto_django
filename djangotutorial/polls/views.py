from django.db.models import F, Sum
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.utils import timezone
from django.views import generic
import logging
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
        # Réaffiche le formulaire de vote avec un message d'erreur.
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
    Gère la création d'un sondage : affiche le formulaire (GET)
    ou enregistre la question et redirige vers l'index (POST).

    :param request: L'objet HttpRequest.
    :return: HttpResponseRedirect vers l'index ou rendu du formulaire avec erreur.
    """
    if request.method == "POST":
        try:
            # Récupération du formulaire
            text = request.POST.get("question_text")
            if not text or text.strip() == "":
                raise ValueError("Le texte de la question est obligatoire.")

            # Sauvegarde de la question
            new_question = Question(
                question_text=text,
                pub_date=timezone.now()
            )
            new_question.save()

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

    return render(request, URL_POLL_FORM)


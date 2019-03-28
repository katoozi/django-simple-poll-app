# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json
import random

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.transaction import atomic
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import FormView, ListView

from .forms import LoginForm
from .models import Item, Poll, Question, Vote

redis_con = settings.REDIS_CONNECTION


class LoginView(FormView):
    form_class = LoginForm
    http_method_names = ['get', 'post']
    template_name = "Public/login.html"

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.is_superuser and request.user.is_staff:
                return redirect(reverse("public:view_result", kwargs={'chart_type': "pie"}))
            else:
                return redirect("public:vote")
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        form_data = self.form_class(request.POST)

        if not form_data.is_valid():
            # form that user submited have errors
            # we split form errors in template, show them by notifications
            return render(request, self.template_name, {
                "form": form_data
            })

        # check the form data with database
        user_obj = authenticate(**form_data.cleaned_data)
        if user_obj is None:
            # credentials that user submited do not belong to anyone
            return render(request, self.template_name, {
                "form": form_data
            })

        if not user_obj.is_active:
            # user is disabled and it's not allowed to login
            return render(request, self.template_name, {
                "form": form_data
            })

        # check the user remember box checked
        if form_data.cleaned_data['remember_me'] is 'True':
            settings.SESSION_EXPIRE_AT_BROWSER_CLOSE = False

        login(request, user_obj)

        if user_obj.is_superuser and user_obj.is_staff:
            return redirect(reverse("public:view_result", kwargs={'chart_type': "pie"}))

        # redirect to next url arg if it exist in url
        if request.GET.get("next", None):
            return redirect(request.GET["next"])

        # default redirect to vote page
        return redirect("public:vote")


@method_decorator(login_required, name="dispatch")
class VoteView(FormView):
    model = Poll
    template_name = "Public/vote.html"
    context_object_name = "polls"

    def get(self, request, *args, **kwargs):
        # get polls that user does not send vote yet and published polls
        if request.user.is_superuser and request.user.is_staff:
            return redirect(reverse("public:view_result", kwargs={'chart_type': "pie"}))
        polls = self.model.published.exclude_user_old_votes(
            self.request.user.pk)

        return render(request, self.template_name, {
            'polls': polls
        })

    def post(self, request, *args, **kwargs):
        if request.user.is_superuser and request.user.is_staff:
            return redirect(reverse("public:view_result", kwargs={'chart_type': "pie"}))

        # convert request.POST QueryDict to dict
        post_data = request.POST.dict()

        # pop(remove) the csrf token from request.POST data
        post_data.pop("csrfmiddlewaretoken", None)

        polls = self.model.published.exclude_user_old_votes(
            self.request.user.pk)

        poll_id = post_data.get('poll_id', None)
        if not poll_id:
            return render(request, self.template_name, {
                "polls": polls
            })

        try:
            poll = polls.get(pk=poll_id)
        except Poll.DoesNotExist:
            return render(request, self.template_name, {
                "polls": polls
            })

        queries = []

        poll_questions = poll.questions.all()
        for question in poll_questions:
            key = "%s:%s" % (poll_id, question.id)
            answer_id = post_data.get(key, None)
            if not answer_id:
                return render(request, self.template_name, {
                    "polls": polls
                })
            question_answers = question.question_answers.all()

            try:
                answer = question_answers.get(id=answer_id)
            except Item.DoesNotExist:
                return render(request, self.template_name, {
                    "polls": polls
                })
            # Vote.objects.create(user=request.user, poll=poll, question=question, item=answer, ip="127.0.0.1")
            queries.append(
                {
                    "poll": poll,
                    "user": request.user,
                    "question": question,
                    "item": answer,
                    "ip": request.META['REMOTE_ADDR']
                }
            )

        # save the user vote poll
        redis_con.sadd("user:%s" % request.user.id, poll_id)

        # # use for get total poll votes
        redis_con.incr("poll:%s" % poll_id)

        with atomic():
            for query in queries:
                Vote.objects.create(**query)

        polls = self.model.published.exclude_user_old_votes(
            self.request.user.pk)
        return render(request, self.template_name, {
            "polls": polls
        })


@method_decorator(login_required, name="dispatch")
class VoteResultView(ListView):
    model = Poll
    template_name = "Public/result_view.html"
    context_object_name = "polls"
    chart_types = ['pie', 'bar', 'radar', 'polarArea']

    def get(self, request, *args, **kwargs):
        if not request.user.is_superuser or not request.user.is_staff:
            return redirect("public:vote")
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return Poll.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        chart_type = self.kwargs['chart_type']
        if chart_type in self.chart_types:
            context['chart_type'] = chart_type
        else:
            context['chart_type'] = "pie"
        return context


@method_decorator(login_required, name="dispatch")
class VoteResultJsonGenerator(FormView):
    model = Poll
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        if not request.user.is_superuser or not request.user.is_staff:
            return redirect("public:vote")

        poll_id = self.kwargs['poll_id']
        question_id = self.kwargs['question_id']

        try:
            poll = Poll.objects.get(id=poll_id)
        except Poll.DoesNotExist:
            return JsonResponse({"Error": "Poll With That Id Does not Exist."})

        try:
            question = poll.questions.get(id=question_id)
        except Question.DoesNotExist:
            return JsonResponse({"Error": "Question With That Id Does not belong to This Poll"})

        answer_objects = question.question_answers.all()

        labels = [answer.value[:20] for answer in answer_objects]

        data = []
        for answer in answer_objects:
            result = answer.get_vote_count(poll_id, question_id)
            if result is None:
                data.append(0)
            else:
                data.append(result.decode("utf-8"))

        backgroundColor = ["rgb(%s, %s, %s)" % (
            random.randrange(0, 255, 1),
            random.randrange(0, 255, 1),
            random.randrange(0, 255, 1),
        ) for color in range(len(data))]

        data = {
            "labels": labels,
            "datasets": [
                {
                    'label': question.title,
                    'data': data,
                    "backgroundColor": backgroundColor,
                    'borderColor': 'rgb(%s, %s, %s)' % (
                        random.randrange(0, 255, 1),
                        random.randrange(0, 255, 1),
                        random.randrange(0, 255, 1),
                    ),
                    'borderAlign': "center"
                },
            ]
        }
        return JsonResponse(data)


@login_required
def logout_view(request):
    logout(request)
    return redirect("public:login")

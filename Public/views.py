# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views.generic import FormView, ListView

from .forms import LoginForm, PollForm
from .models import Item, Poll, Question, Vote

redis_con = settings.REDIS_CONNECTION


class LoginView(FormView):
    form_class = LoginForm
    http_method_names = ['get', 'post']
    template_name = "Public/login.html"

    def get(self, request, *args, **kwargs):
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

        # check the user remember box checked
        if form_data.cleaned_data['remember_me'] is 'True':
            settings.SESSION_EXPIRE_AT_BROWSER_CLOSE = False

        login(request, user_obj)

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
        polls = self.model.published.exclude_user_old_votes(
            self.request.user.pk)

        return render(request, self.template_name, {
            'polls': polls
        })

    def post(self, request, *args, **kwargs):
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
    template_name = ""

    def get_queryset(self):
        return Poll.objects.all()


@login_required
def logout_view(request):
    logout(request)
    return redirect("public:login")

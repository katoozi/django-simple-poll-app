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
        return redirect("public:vote")


class VoteView(FormView):
    model = Poll
    template_name = "Public/vote.html"
    context_object_name = "polls"

    def get(self, request, *args, **kwargs):
        # get polls that user does not send vote yet
        polls = self.model.published.exclude_user_old_votes(
            self.request.user.pk)

        return render(request, self.template_name, {
            'polls': polls
        })

    def post(self, request, *args, **kwargs):
        return render(request, self.template_name, {
            "polls": None
        })


@login_required
def logout_view(request):
    logout(request)
    return redirect("public:login")

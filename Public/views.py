from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.generic import FormView
from Poll.models import Item, Poll, Vote


class LoginView(FormView):
    def get(self, request, *args, **kwargs):
        return render(request, "Public/login.html", {})

    def post(self, request, *args, **kwargs):
        return render(request, "Public/login.html", {})


def logout(request):
    logout(request)
    return redirect("Public:login")

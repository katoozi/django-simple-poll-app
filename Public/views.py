from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.conf import settings
from django.contrib.auth import login, logout, authenticate


def home(request):
    return render(request, "Public/home.html", {
        "Text": "Download From Google"
    })


def login(request):
    pass


def logout(request):
    logout(request)
    return redirect("Public:home")

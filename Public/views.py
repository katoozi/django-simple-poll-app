from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings


def home(request):
    print(settings.REDIS_CONNECTION.set("download", "mohammad"))
    print(settings.REDIS_CONNECTION.get("download").decode("utf-8"))
    return HttpResponse("skdfmlkmsdflkmsldfmkklsmdfklm")

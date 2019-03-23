from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views.generic import FormView

from Poll.models import Item, Poll, Vote

from .forms import LoginForm


class LoginView(FormView):
    form_class = LoginForm
    http_method_names = ['get', 'post']

    def get(self, request, *args, **kwargs):
        return render(request, "Public/login.html", {})

    def post(self, request, *args, **kwargs):
        form_data = self.form_class(request.POST)

        if not form_data.is_valid():
            # form that user submited have errors
            # TODO: Handle the form errors
            return render(request, "Public/login.html", {
                "form": form_data
            })
        user_obj = authenticate(**form_data.cleaned_data)
        if user_obj is None:
            # credentials that user submited do not belong to anyone
            # TODO: handle the user does not exists situation
            pass

        # check the user remember box checked
        if form_data.cleaned_data['remember_me'] is 'True':
            settings.SESSION_EXPIRE_AT_BROWSER_CLOSE = False

        login(request, user_obj)
        return redirect("public:login")


@login_required
def logout_view(request):
    logout(request)
    return redirect("public:login")

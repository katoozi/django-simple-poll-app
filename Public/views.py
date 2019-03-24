from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views.generic import FormView, ListView

from .forms import LoginForm, PollForm


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


class VoteView(ListView):
    # model = Poll
    template_name = "Public/vote.html"
    context_object_name = "polls"

    def get_queryset(self):
        return self.model.published.filter()

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     context[""] =
    #     return context


@login_required
def logout_view(request):
    logout(request)
    return redirect("public:login")

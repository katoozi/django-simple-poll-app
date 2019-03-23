from django.conf.urls import url
from . import views

urlpatterns = [
    url("^$", views.LoginView.as_view(), name="login"),
    url("^Vote/$", views.VoteView.as_view(), name="vote"),
    url("^logout/$", views.logout_view, name="logout"),
]

from django.conf.urls import url
from . import views

urlpatterns = [
    url("$", views.LoginView.as_view(), name="login"),
    url("$", views.logout, name="logout"),
]
from django.conf.urls import url
from . import views

urlpatterns = [
    url("^$", views.LoginView.as_view(), name="login"),
    url("^Vote/$", views.VoteView.as_view(), name="vote"),
    url("^view-result/$", views.VoteResultView.as_view(), name="view_result"),
    url("^logout/$", views.logout_view, name="logout"),
]

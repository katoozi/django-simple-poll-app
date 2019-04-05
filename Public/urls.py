from django.conf.urls import url
from . import views

urlpatterns = [
    url(r"^$", views.LoginView.as_view(), name="login"),
    url(r"^vote/$", views.VoteView.as_view(), name="vote"),
    url(r"^view-result/(?P<chart_type>[-\w]+)/$",
        views.VoteResultView.as_view(), name="view_result"),
    url(r"^view-result-json-generator/"
        r"(?P<poll_id>[0-9]+)/(?P<question_id>[0-9]+)/$",
        views.VoteResultJsonGenerator.as_view(),
        name="view_result_json_generator"),
    url(r"^logout/$", views.logout_view, name="logout"),
]

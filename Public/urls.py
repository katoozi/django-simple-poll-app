from django.conf.urls import url
from . import views

urlpatterns = [
    url("^$", views.LoginView.as_view(), name="login"),
    url("^vote/$", views.VoteView.as_view(), name="vote"),
    url("^view-result/(?P<chart_type>[-\w]+)/$",
        views.VoteResultView.as_view(), name="view_result"),
    url("^view-result-json-generator/(?P<poll_id>[0-9]+)/(?P<question_id>[0-9]+)/$",
        views.VoteResultJsonGenerator.as_view(), name="view_result_json_generator"),
    url("^logout/$", views.logout_view, name="logout"),
]

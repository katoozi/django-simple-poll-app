from django.conf.urls import url, include
from django.contrib import admin
from Public import views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^poll/', include('Poll.urls')),
    url(r'^$', views.home),
]

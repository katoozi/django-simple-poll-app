from django.conf.urls import url, include
from django.contrib import admin

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^poll/', include('Poll.urls')),
    url(r'^', include("Public.urls", namespace="public", app_name="Public")),
]

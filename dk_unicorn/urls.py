from django.urls import path

from dk_unicorn.views import message

app_name = "dk_unicorn"

urlpatterns = [
    path("message/<path:component_name>", message, name="message"),
]

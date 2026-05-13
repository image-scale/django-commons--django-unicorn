from django.urls import path

app_name = "dk_unicorn"

urlpatterns = [
    path("message/<path:component_name>", lambda r, component_name: None, name="message"),
]

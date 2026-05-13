from django.urls import include, path

urlpatterns = [
    path("unicorn/", include("dk_unicorn.urls")),
]

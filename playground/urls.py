from django.urls import path
from .views import hello_view

urlpatterns = [
    path("hello/<str:name>/", hello_view, name="hello"),
]

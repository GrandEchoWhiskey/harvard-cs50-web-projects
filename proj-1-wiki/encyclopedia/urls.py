from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("wiki/<str:title>", views.wiki, name="wiki"),
    path("new", views.new, name="new"),
    path("edit", views.edit, name="edit"),
]

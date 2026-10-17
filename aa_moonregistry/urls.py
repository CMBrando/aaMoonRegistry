"""Routes."""

from django.urls import path

from . import views

app_name = "aa_moonregistry"

urlpatterns = [
    path("", views.index, name="index"),
    path("SearchUniverse", views.search_universe),
    path("SearchMoonOre", views.search_moon_ore),
    path("SearchSovOwner", views.search_sov_owner),
    path("MoonList", views.get_moon_list),
    path("SaveMoonDetail", views.save_moon_detail),
]

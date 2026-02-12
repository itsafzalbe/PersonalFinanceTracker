from django.urls import path
from .views import *


app_name = "cards"


urlpatterns = [
    


    path("currencies/", CurrencyListView.as_view(), name="currency_list"),
    path("currencies/convert/", CurrencyConvertView.as_view(), name="currency_convert"),



    path("cards/", CardListView.as_view(), name="cards_list"),
    path("cards/create/", CardCreateView.as_view(), name="card_create"),
    path("cards/<int:pk>/", CardDetailView.as_view(), name="card_detail"),
    path("cards/<int:pk>/edit/", CardUpdateView.as_view(), name="card_edit"),
    path("cards/<int:pk>/delete/", CardDeleteView.as_view(), name="card_delete"),
    path("cards/<int:pk>/update-balance/", CardUpdateBalanceView.as_view(), name="card_update_balance"),
    path("cards/<int:pk>/change-status/", CardChangeStatusView.as_view(), name="card_change_status"),
    path("cards/<int:pk>/set-default/", CardSetDefaultView.as_view(), name="card_set_default"),
    path("card-types/", CardTypeListView.as_view(), name="card_types")


]

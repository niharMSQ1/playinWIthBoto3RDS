from django.urls import path
from .views import *

urlpatterns = [
    path('user/register/', register),
    path('user/login/', login),
    path('api/create-pdf/', createPdf),
    path('api/store-quotes/', storeQuotes),
]

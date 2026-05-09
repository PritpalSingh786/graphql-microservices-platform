from django.urls import path
from . import views

urlpatterns = [
    path('', views.AuthGraphQLProxyView.as_view()),
]
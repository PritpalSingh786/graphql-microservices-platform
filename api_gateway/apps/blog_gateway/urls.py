from django.urls import path
from . import views

urlpatterns = [
    path('', views.BlogGraphQLProxyView.as_view()),
]
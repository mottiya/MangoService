from django.urls import path
from .views import *

urlpatterns = [
    path('tgbot/new/', TgNewAPIView.as_view()),
    path('tgbot/csvdatabase/', TgCSVAPIView.as_view()),
    path('tgbot/stats/', TgStatsAPIView.as_view()),
    path('call/', CallListAPIView.as_view()),
    path('call/delete/<int:pk>', CallDeleteAPIView.as_view()),
    path('newadvert/', AdvertCreateAPIView.as_view()),
    path('events/call', CallCreateAPIView.as_view()),
    path('clear/', ClearDBApiVIew.as_view()),
    path('events/campaign/tasks', TaskCreateAPIView.as_view())
]
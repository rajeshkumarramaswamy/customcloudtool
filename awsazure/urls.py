from django.urls import path, include
from . import views


urlpatterns = [
    path('/', views.index, name='aws'),
    path('/getDetails', views.getDetails),
]

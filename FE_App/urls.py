from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # 👈 Ruta principal
    path('login/', views.login_view, name='login'),  # si ya tienes el login
    path('dashboard/', views.dashboard, name='dashboard'),
]

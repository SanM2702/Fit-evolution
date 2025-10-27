from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  
    path('login/', views.login_view, name='login'),  
    path('register/', views.register_view, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    #Urls de  seccion quienessomos
    path('fit-evolution/', views.fit_evolution, name='fit-evolution'),
    path('QSgymsisuno/', views.QSgymsisuno, name='QSgymsisuno'),
    path('QMgymsisdos/', views.QMgymsisdos, name='QMgymsisdos'),
    path('SEgymsistres/', views.SEgymsistres, name='SEgymsistres'),
    path('MenuNutricion/', views.menu_nutricion, name='MenuNutricion'),
    path('nutricioninfo/', views.nutricioninfo, name='nutricioninfo'),
    path('nutricion/', views.nutricion, name='nutricion'),
    path('logout/', views.logout_view, name='logout'),
    # URLs de perfil
    path('crear-perfil/', views.crear_perfil, name='crear_perfil'),
    path('perfil/', views.ver_perfil, name='ver_perfil'),
    path('editar-perfil/', views.editar_perfil, name='editar_perfil'),
]

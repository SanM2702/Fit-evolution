from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'Bienvenido {username} 👋')
            return redirect('dashboard')  # redirige a la página principal
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')

    return render(request, 'login.html')

def home(request):
    return HttpResponse("<h1>Bienvenido a Fit Evolution 🏋️</h1><p>Página principal del sistema.</p>")

@login_required
def dashboard(request):
    return render(request, 'dashboard.html')   


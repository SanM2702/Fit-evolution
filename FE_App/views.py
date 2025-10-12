from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .forms import CustomUserCreationForm

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


def register_view(request):
    """Registrar un nuevo usuario usando UserCreationForm.

    - Si POST y el formulario es válido: crea el usuario, muestra mensaje y redirige al login.
    - Si no es válido o es GET: muestra el formulario con errores.
    """
    User = get_user_model()
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Cuenta creada para {user.username}. Puedes iniciar sesión ahora.')
            return redirect('login')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = CustomUserCreationForm()

    return render(request, 'register.html', {'form': form})

@login_required
def dashboard(request):
    return render(request, 'dashboard.html')   


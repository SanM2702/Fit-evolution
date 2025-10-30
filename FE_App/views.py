from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth import logout
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .forms import CustomUserCreationForm, UserProfileStep1Form, UserProfileStep2Form, UserProfileEditForm
from .models import UserProfile

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'Bienvenido {username}')
            return redirect('dashboard')  # redirige al menu principal
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')

    return render(request, 'login.html')

def home(request):
    return HttpResponse("<h1>Bienvenido a Fit Evolution</h1><p>Página principal del sistema.</p>")


def register_view(request):
    """Registrar un nuevo usuario usando UserCreationForm.

    - Si POST y el formulario es válido: crea el usuario, inicia sesión y redirige a crear-perfil.
    - Si no es válido o es GET: muestra el formulario con errores.
    """
    User = get_user_model()
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Iniciar sesión automáticamente después del registro
            login(request, user)
            messages.success(request, f'Cuenta creada para {user.username}. Por favor completa tu perfil.')
            return redirect('crear_perfil')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = CustomUserCreationForm()

    return render(request, 'register.html', {'form': form})

@login_required
def dashboard(request):
    return render(request, 'dashboard.html')   

def fit_evolution(request):
    return render(request, 'fit-evolution.html')

def QSgymsisuno(request):
    return render(request, 'QSgymsisuno.html')

def QMgymsisdos(request):
    return render(request, 'QMgymsisdos.html')

def SEgymsistres(request):
    return render(request, 'SEgymsistres.html')

def menu_nutricion(request):
    return render(request, 'MenuNutricion.html')

@login_required
def nutricion(request):
    """Vista de nutrición con datos del perfil del usuario."""
    try:
        profile = request.user.profile
        context = {
            'profile': profile,
            'user': request.user,
        }
        return render(request, 'nutricion.html', context)
    except UserProfile.DoesNotExist:
        messages.warning(request, 'Debes crear tu perfil primero para ver tus recomendaciones nutricionales.')
        return redirect('crear_perfil')

def nutricioninfo(request):
    return render(request, 'nutricioninfo.html')

def logout_view(request):
    """Cerrar sesión y redirigir al login. Solo acepta POST."""
    if request.method == 'POST':
        logout(request)
        return redirect('login')
    return redirect('dashboard')


@login_required
def crear_perfil(request):
    """Vista para crear el perfil del usuario en 2 pasos."""
    if hasattr(request.user, 'profile'):
        messages.info(request, 'Ya tienes un perfil creado. Puedes editarlo desde tu página de perfil.')
        return redirect('ver_perfil')

    step = request.session.get('profile_step', 1)

    if request.method == 'POST':
        if 'volver_paso1' in request.POST:
            request.session['profile_step'] = 1
            return redirect('crear_perfil')

        # --- Paso 1 ---
        if step == 1:
            form = UserProfileStep1Form(request.POST)
            if form.is_valid():
                request.session['profile_step1_data'] = {
                    'edad': form.cleaned_data['edad'],
                    'sexo': form.cleaned_data['sexo'],
                    'peso': str(form.cleaned_data['peso']),
                    'altura': form.cleaned_data['altura'],
                    'imc': str(form.cleaned_data['imc']) if form.cleaned_data.get('imc') else None,
                }
                request.session['profile_step'] = 2
                return redirect('crear_perfil')

        # --- Paso 2 ---
        elif step == 2:
            form = UserProfileStep2Form(request.POST)
            if form.is_valid():
                step1_data = request.session.get('profile_step1_data', {})

                profile = form.save(commit=False)
                profile.usuario = request.user
                profile.edad = step1_data['edad']
                profile.sexo = step1_data['sexo']
                profile.peso = step1_data['peso']
                profile.altura = step1_data['altura']
                if step1_data.get('imc'):
                    profile.imc = step1_data['imc']

                profile.save()

                request.session.pop('profile_step1_data', None)
                request.session.pop('profile_step', None)

                messages.success(request, '¡Perfil creado exitosamente!')
                return redirect('ver_perfil')

    else:
        # --- Render inicial o cambio de paso ---
        if step == 1:
            initial_data = request.session.get('profile_step1_data', {})
            form = UserProfileStep1Form(initial=initial_data)

        elif step == 2:
            step1_data = request.session.get('profile_step1_data', {})

            # 🔹 Calcular porcentaje de grasa sin guardar en BD
            porcentaje_grasa = None
            try:
                edad = step1_data.get('edad')
                sexo = step1_data.get('sexo')
                peso = float(step1_data.get('peso', 0))
                altura = float(step1_data.get('altura', 0))
                
                if peso > 0 and altura > 0 and edad and sexo:
                    # Calcular IMC
                    altura_metros = altura / 100
                    imc = peso / (altura_metros ** 2)
                    
                    # Calcular porcentaje de grasa
                    S = 1 if sexo == 'M' else 0
                    grasa = (1.20 * imc) + (0.23 * edad) - (10.8 * S) - 5.4
                    grasa = max(3, min(grasa, 70))  # limitar entre 3% y 70%
                    porcentaje_grasa = round(grasa, 1)
            except (ValueError, TypeError):
                porcentaje_grasa = None

            # 🔹 Prellenar el paso 2 con el porcentaje de grasa calculado
            initial_data = {
                'porcentaje_grasa': porcentaje_grasa,
            }

            form = UserProfileStep2Form(initial=initial_data)

    context = {'form': form, 'step': step}
    return render(request, 'crear-perfil.html', context)



@login_required
def ver_perfil(request):
    """Vista para ver el perfil del usuario."""
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        messages.warning(request, 'Aún no has creado tu perfil.')
        return redirect('crear_perfil')
    
    context = {
        'profile': profile,
    }
    return render(request, 'perfil.html', context)


@login_required
def editar_perfil(request):
    """Vista para editar el perfil del usuario."""
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        messages.warning(request, 'Primero debes crear tu perfil.')
        return redirect('crear_perfil')
    
    if request.method == 'POST':
        form = UserProfileEditForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado exitosamente.')
            return redirect('ver_perfil')
    else:
        form = UserProfileEditForm(instance=profile)
    
    context = {
        'form': form,
        'profile': profile,
    }
    return render(request, 'editar-perfil.html', context)
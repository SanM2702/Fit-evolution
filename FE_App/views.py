from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth import logout
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .forms import CustomUserCreationForm, UserProfileStep1Form, UserProfileStep2Form, UserProfileEditForm, PlanEntrenamientoForm, DiaEntrenamientoForm, DiaEjercicioForm
from .models import UserProfile, PlanEntrenamiento, DiaEntrenamiento, DiaEjercicio, GrupoMuscular, Ejercicio
from datetime import date, timedelta

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


# ==================== VISTAS DE ENTRENAMIENTO ====================

@login_required
def dashboard_entrenamiento(request):
    """Vista principal de entrenamiento con datos del usuario y predicciones ML."""
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        messages.warning(request, 'Debes crear tu perfil primero.')
        return redirect('crear_perfil')
    
    # Obtener o crear plan activo del usuario
    plan_activo = PlanEntrenamiento.objects.filter(
        usuario=request.user, 
        estado='activo'
    ).first()
    
    # Si no existe plan, crear uno de ejemplo
    if not plan_activo:
        plan_activo = crear_plan_ejemplo(request.user, profile)
    
    context = {
        'profile': profile,
        'plan': plan_activo,
        'user': request.user,
    }
    return render(request, 'entrenamiento-dashboard.html', context)


@login_required
def ver_plan_entrenamiento(request, plan_id):
    """Vista detallada del plan de entrenamiento con ejercicios por día."""
    plan = get_object_or_404(PlanEntrenamiento, id=plan_id, usuario=request.user)
    
    # Obtener días de entrenamiento ordenados
    dias = plan.dias.all().prefetch_related('ejercicios_asignados__ejercicio__grupo_muscular')
    
    context = {
        'plan': plan,
        'dias': dias,
    }
    return render(request, 'plan-detallado.html', context)


def crear_plan_ejemplo(usuario, profile):
    """Crea un plan de entrenamiento de ejemplo para el usuario."""
    # Crear plan
    plan = PlanEntrenamiento.objects.create(
        usuario=usuario,
        nombre_plan=f"Plan {profile.get_objetivo_display()}",
        fecha_inicio=date.today(),
        fecha_fin=date.today() + timedelta(weeks=12),
        objetivo=profile.objetivo,
        estado='activo',
        dias_semana=4,
        riesgo_lesion=False,  # Datos de ejemplo (futuro: predicción ML)
        riesgo_estancamiento=False  # Datos de ejemplo (futuro: predicción ML)
    )
    
    # Día 1: Pecho y Tríceps
    dia1 = DiaEntrenamiento.objects.create(
        plan=plan,
        numero_dia=1,
        nombre_dia="Pecho y Tríceps",
        descripcion="Enfoque en desarrollo de pecho con trabajo complementario de tríceps"
    )
    
    # Ejercicios del día 1
    ejercicios_dia1 = [
        (1, 1, 4, "8-10", 60.0, 2.0),  # Press Banca
        (2, 2, 4, "10-12", 25.0, 1.5),  # Press Inclinado
        (3, 3, 3, "12-15", 15.0, 1.0),  # Aperturas
        (4, 4, 3, "10-12", None, 1.5),  # Fondos
        (5, 5, 3, "12-15", 30.0, 1.0),  # Press Francés
    ]
    
    for orden, ejercicio_id, series, reps, peso, descanso in ejercicios_dia1:
        DiaEjercicio.objects.create(
            dia=dia1,
            ejercicio_id=ejercicio_id,
            orden=orden,
            series=series,
            repeticiones=reps,
            peso_sugerido=peso,
            descanso_minutos=descanso
        )
    
    # Día 2: Espalda y Bíceps
    dia2 = DiaEntrenamiento.objects.create(
        plan=plan,
        numero_dia=3,
        nombre_dia="Espalda y Bíceps",
        descripcion="Desarrollo de espalda con énfasis en dorsales y trabajo de bíceps"
    )
    
    ejercicios_dia2 = [
        (1, 6, 4, "8-10", None, 2.0),  # Dominadas
        (2, 7, 4, "8-10", 50.0, 2.0),  # Remo con Barra
        (3, 8, 3, "10-12", 50.0, 1.5),  # Jalón
        (4, 9, 3, "10-12", 30.0, 1.0),  # Curl Barra
        (5, 10, 3, "12-15", 12.0, 1.0),  # Curl Martillo
    ]
    
    for orden, ejercicio_id, series, reps, peso, descanso in ejercicios_dia2:
        DiaEjercicio.objects.create(
            dia=dia2,
            ejercicio_id=ejercicio_id,
            orden=orden,
            series=series,
            repeticiones=reps,
            peso_sugerido=peso,
            descanso_minutos=descanso
        )
    
    # Día 3: Piernas
    dia3 = DiaEntrenamiento.objects.create(
        plan=plan,
        numero_dia=5,
        nombre_dia="Piernas Completo",
        descripcion="Entrenamiento completo de tren inferior"
    )
    
    ejercicios_dia3 = [
        (1, 11, 4, "8-10", 80.0, 2.5),  # Sentadilla
        (2, 12, 4, "10-12", 120.0, 2.0),  # Prensa
        (3, 13, 3, "10-12", 60.0, 2.0),  # Peso Muerto Rumano
        (4, 14, 3, "12-15", 40.0, 1.0),  # Extensiones
    ]
    
    for orden, ejercicio_id, series, reps, peso, descanso in ejercicios_dia3:
        DiaEjercicio.objects.create(
            dia=dia3,
            ejercicio_id=ejercicio_id,
            orden=orden,
            series=series,
            repeticiones=reps,
            peso_sugerido=peso,
            descanso_minutos=descanso
        )
    
    # Día 4: Hombros y Abdomen
    dia4 = DiaEntrenamiento.objects.create(
        plan=plan,
        numero_dia=6,
        nombre_dia="Hombros y Core",
        descripcion="Desarrollo de hombros y trabajo de core"
    )
    
    ejercicios_dia4 = [
        (1, 15, 4, "8-10", 40.0, 2.0),  # Press Militar
        (2, 16, 4, "12-15", 10.0, 1.0),  # Elevaciones Laterales
        (3, 17, 3, "15-20", 20.0, 1.0),  # Face Pulls
        (4, 18, 3, "30-60s", None, 1.0),  # Plancha
        (5, 19, 3, "15-20", 30.0, 1.0),  # Crunch Polea
    ]
    
    for orden, ejercicio_id, series, reps, peso, descanso in ejercicios_dia4:
        DiaEjercicio.objects.create(
            dia=dia4,
            ejercicio_id=ejercicio_id,
            orden=orden,
            series=series,
            repeticiones=reps,
            peso_sugerido=peso,
            descanso_minutos=descanso
        )
    
    return plan


@login_required
def editar_plan_entrenamiento(request, plan_id):
    """Vista para editar el plan de entrenamiento completo."""
    plan = get_object_or_404(PlanEntrenamiento, id=plan_id, usuario=request.user)
    
    if request.method == 'POST':
        # Actualizar información básica del plan
        if 'actualizar_plan' in request.POST:
            form = PlanEntrenamientoForm(request.POST, instance=plan)
            if form.is_valid():
                form.save()
                messages.success(request, 'Plan actualizado exitosamente.')
                return redirect('editar_plan_entrenamiento', plan_id=plan.id)
        
        # Agregar nuevo día
        elif 'agregar_dia' in request.POST:
            numero_dia = request.POST.get('numero_dia')
            nombre_dia = request.POST.get('nombre_dia')
            descripcion = request.POST.get('descripcion', '')
            
            if numero_dia and nombre_dia:
                # Verificar que el día no exista ya
                if not DiaEntrenamiento.objects.filter(plan=plan, numero_dia=numero_dia).exists():
                    DiaEntrenamiento.objects.create(
                        plan=plan,
                        numero_dia=numero_dia,
                        nombre_dia=nombre_dia,
                        descripcion=descripcion
                    )
                    messages.success(request, f'Día {nombre_dia} agregado exitosamente.')
                else:
                    messages.error(request, 'Ya existe un entrenamiento para ese día.')
            return redirect('editar_plan_entrenamiento', plan_id=plan.id)
        
        # Eliminar día
        elif 'eliminar_dia' in request.POST:
            dia_id = request.POST.get('dia_id')
            dia = get_object_or_404(DiaEntrenamiento, id=dia_id, plan=plan)
            dia.delete()
            messages.success(request, 'Día eliminado exitosamente.')
            return redirect('editar_plan_entrenamiento', plan_id=plan.id)
        
        # Actualizar día
        elif 'actualizar_dia' in request.POST:
            dia_id = request.POST.get('dia_id')
            dia = get_object_or_404(DiaEntrenamiento, id=dia_id, plan=plan)
            dia.nombre_dia = request.POST.get('nombre_dia', dia.nombre_dia)
            dia.descripcion = request.POST.get('descripcion', '')
            dia.save()
            messages.success(request, 'Día actualizado exitosamente.')
            return redirect('editar_plan_entrenamiento', plan_id=plan.id)
        
        # Agregar ejercicio a un día
        elif 'agregar_ejercicio' in request.POST:
            dia_id = request.POST.get('dia_id')
            ejercicio_id = request.POST.get('ejercicio_id')
            series = request.POST.get('series')
            repeticiones = request.POST.get('repeticiones')
            peso_sugerido = request.POST.get('peso_sugerido') or None
            descanso_minutos = request.POST.get('descanso_minutos')
            
            dia = get_object_or_404(DiaEntrenamiento, id=dia_id, plan=plan)
            
            # Obtener el siguiente orden disponible
            ultimo_orden = DiaEjercicio.objects.filter(dia=dia).count()
            orden = ultimo_orden + 1
            
            DiaEjercicio.objects.create(
                dia=dia,
                ejercicio_id=ejercicio_id,
                orden=orden,
                series=series,
                repeticiones=repeticiones,
                peso_sugerido=peso_sugerido,
                descanso_minutos=descanso_minutos
            )
            messages.success(request, 'Ejercicio agregado exitosamente.')
            return redirect('editar_plan_entrenamiento', plan_id=plan.id)
        
        # Eliminar ejercicio
        elif 'eliminar_ejercicio' in request.POST:
            ejercicio_dia_id = request.POST.get('ejercicio_dia_id')
            ejercicio_dia = get_object_or_404(DiaEjercicio, id=ejercicio_dia_id, dia__plan=plan)
            ejercicio_dia.delete()
            messages.success(request, 'Ejercicio eliminado exitosamente.')
            return redirect('editar_plan_entrenamiento', plan_id=plan.id)
        
        # Actualizar ejercicio
        elif 'actualizar_ejercicio' in request.POST:
            ejercicio_dia_id = request.POST.get('ejercicio_dia_id')
            ejercicio_dia = get_object_or_404(DiaEjercicio, id=ejercicio_dia_id, dia__plan=plan)
            
            ejercicio_dia.series = request.POST.get('series', ejercicio_dia.series)
            ejercicio_dia.repeticiones = request.POST.get('repeticiones', ejercicio_dia.repeticiones)
            peso = request.POST.get('peso_sugerido')
            ejercicio_dia.peso_sugerido = peso if peso else None
            ejercicio_dia.descanso_minutos = request.POST.get('descanso_minutos', ejercicio_dia.descanso_minutos)
            ejercicio_dia.save()
            
            messages.success(request, 'Ejercicio actualizado exitosamente.')
            return redirect('editar_plan_entrenamiento', plan_id=plan.id)
    
    # GET request
    form_plan = PlanEntrenamientoForm(instance=plan)
    dias = plan.dias.all().prefetch_related('ejercicios_asignados__ejercicio__grupo_muscular').order_by('numero_dia')
    
    # Obtener todos los ejercicios disponibles agrupados por grupo muscular
    grupos_musculares = GrupoMuscular.objects.all().prefetch_related('ejercicios')
    
    context = {
        'plan': plan,
        'form_plan': form_plan,
        'dias': dias,
        'grupos_musculares': grupos_musculares,
        'dias_semana': DiaEntrenamiento.DIAS_SEMANA,
    }
    return render(request, 'editar-plan.html', context)
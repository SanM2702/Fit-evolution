import joblib
import os
import numpy as np
from django.conf import settings
from django.http import JsonResponse

from django.shortcuts import render, redirect, get_object_or_404
from django.db import IntegrityError
from django.db.models import Max
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

@login_required
def get_macronutrientes(request):
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        return JsonResponse({'error': 'Perfil no encontrado'}, status=404)

    # Mapear los datos del perfil al formato esperado por el modelo
    genero_map = {'M': 'Masculino', 'F': 'Femenino', 'O': 'Otro'}
    nivel_exp_map = {
        'principiante': 'Principiante',
        'intermedio': 'Intermedio',
        'avanzado': 'Avanzado'
    }

    # Obtener valores del perfil con valores por defecto seguros
    datos_usuario = {
        'Edad': int(profile.edad or 25),
        'Género': genero_map.get(profile.sexo, 'Masculino'),
        'Peso_(kg)': float(profile.peso or 70),
        'Altura_(m)': float(profile.altura or 1.70) / 100,  # Convertir cm a m
        'Frecuencia_entrenamiento_(días/semana)': 5,  # Valor por defecto
        'Duración_sesión_(horas)': 1.0,  # Valor por defecto
        'Nivel_experiencia': nivel_exp_map.get(profile.nivel_actividad, 'Intermedio'),
        'Objetivo': getattr(profile, 'objetivo', 'Mantener peso'),
        'Porcentaje_grasa': float(getattr(profile, 'porcentaje_grasa', 20.0)),
        'Masa_magra_(kg)': float(profile.peso or 70) * (1 - (float(getattr(profile, 'porcentaje_grasa', 20.0)) / 100))
    }

    try:
        # Ruta al modelo y al escalador
        model_path = os.path.join(settings.BASE_DIR, 'ModelosML', 'MacroNutrientes', 'modelo_macros.pkl')
        scaler_path = os.path.join(settings.BASE_DIR, 'ModelosML', 'MacroNutrientes', 'scaler.pkl')
        
        # Cargar modelo y escalador
        model = joblib.load(model_path)
        scaler = joblib.load(scaler_path)
        
        # Codificar variables categóricas
        genero_encoder = {'Masculino': 0, 'Femenino': 1, 'Otro': 2}
        objetivo_encoder = {'Perder grasa': 0, 'Mantener peso': 1, 'Ganar músculo': 2}
        nivel_encoder = {'Principiante': 0, 'Intermedio': 1, 'Avanzado': 2}

        # Preparar datos para predicción
        X_pred = np.array([[
            datos_usuario['Edad'],
            genero_encoder[datos_usuario['Género']],
            datos_usuario['Peso_(kg)'],
            datos_usuario['Altura_(m)'],
            datos_usuario['Frecuencia_entrenamiento_(días/semana)'],
            datos_usuario['Duración_sesión_(horas)'],
            nivel_encoder[datos_usuario['Nivel_experiencia']],
            objetivo_encoder.get(datos_usuario['Objetivo'], 1),  # Default a 'Mantener peso'
            datos_usuario['Porcentaje_grasa'],
            datos_usuario['Masa_magra_(kg)']
        ]])

        # Escalar características
        X_scaled = scaler.transform(X_pred)
        
        # Realizar predicción
        y_pred = model.predict(X_scaled)
        
        # Redondear valores
        proteinas = round(y_pred[0][0])
        carbohidratos = round(y_pred[0][1])
        grasas = round(y_pred[0][2])
        
        # Calcular calorías totales
        calorias = (proteinas * 4) + (carbohidratos * 4) + (grasas * 9)
        
        return JsonResponse({
            'calorias': int(calorias),
            'proteinas': proteinas,
            'carbohidratos': carbohidratos,
            'grasas': grasas
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

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
        # Obtener plan activo del usuario y contar días configurados
        plan_activo = PlanEntrenamiento.objects.filter(usuario=request.user, estado='activo').first()
        dias_entrenamiento = plan_activo.dias.count() if plan_activo else 0

        context = {
            'profile': profile,
            'user': request.user,
            'plan': plan_activo,
            'dias_entrenamiento': dias_entrenamiento,
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
    
    # Obtener el plan de entrenamiento más reciente del usuario
    plan = PlanEntrenamiento.objects.filter(usuario=request.user).order_by('-fecha_creacion').first()
    
    context = {
        'profile': profile,
        'plan': plan,
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
    ).order_by('-fecha_actualizacion').first()
    
    # Si no existe plan, crear uno de ejemplo
    if not plan_activo:
        plan_activo = crear_plan_ejemplo(request.user, profile)
    
    # Evaluar porcentaje de grasa para alertas
    porcentaje_grasa = profile.porcentaje_grasa
    alerta_grasa = None
    
    if porcentaje_grasa <= 4:
        alerta_grasa = {
            'tipo': 'critico',
            'titulo': 'Problema Crítico Detectado',
            'mensaje': 'Tu porcentaje de grasa corporal está en un nivel crítico ({}%). Existe riesgo de fallo orgánico o anorexia. Es urgente consultar con un profesional de la salud.'.format(porcentaje_grasa),
            'icono': 'fas fa-exclamation-circle'
        }
    elif porcentaje_grasa > 31:
        alerta_grasa = {
            'tipo': 'critico',
            'titulo': 'Problema Crítico Detectado',
            'mensaje': 'Tu porcentaje de grasa corporal está en un nivel de alto riesgo ({}%). Existe alto riesgo de enfermedades cardiovasculares, diabetes y otras enfermedades. Es importante consultar con un profesional de la salud.'.format(porcentaje_grasa),
            'icono': 'fas fa-exclamation-circle'
        }
    
    context = {
        'profile': profile,
        'plan': plan_activo,
        'user': request.user,
        'alerta_grasa': alerta_grasa,
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
                # Guardar inmediatamente los cambios del formulario (incluye fecha_inicio/fecha_fin)
                plan = form.save()

                # Actualizar el objetivo en el perfil del usuario si está presente en el formulario
                if 'objetivo' in form.cleaned_data and hasattr(request.user, 'profile'):
                    request.user.profile.objetivo = form.cleaned_data['objetivo']
                    request.user.profile.save()

                # Sincronizar cantidad de días configurados sin sobreescribir otros campos ya guardados
                nuevo_total_dias = plan.dias.count()
                if plan.dias_semana != nuevo_total_dias:
                    plan.dias_semana = nuevo_total_dias
                    plan.save(update_fields=['dias_semana'])

                # Si este plan quedó activo, desactivar otros activos del mismo usuario
                if plan.estado == 'activo':
                    (PlanEntrenamiento.objects
                        .filter(usuario=request.user, estado='activo')
                        .exclude(id=plan.id)
                        .update(estado='pausado'))
                messages.success(request, 'Plan actualizado exitosamente.')
                return redirect('editar_plan_entrenamiento', plan_id=plan.id)
            else:
                # Mantener el formulario con errores para mostrarlos en la plantilla
                form_plan = form
                # Mostrar errores en mensajes para diagnóstico rápido
                try:
                    messages.error(request, f"Errores al guardar el plan: {form.errors.as_text()}")
                except Exception:
                    pass
                # Continuar hacia la sección de render al final del método
                
        
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
                    # Actualizar cantidad de días configurados
                    plan.dias_semana = plan.dias.count()
                    plan.save(update_fields=['dias_semana'])
                    messages.success(request, f'Día {nombre_dia} agregado exitosamente.')
                else:
                    messages.error(request, 'Ya existe un entrenamiento para ese día.')
            return redirect('editar_plan_entrenamiento', plan_id=plan.id)
        
        # Eliminar día
        elif 'eliminar_dia' in request.POST:
            dia_id = request.POST.get('dia_id')
            dia = get_object_or_404(DiaEntrenamiento, id=dia_id, plan=plan)
            dia.delete()
            # Actualizar cantidad de días configurados
            plan.dias_semana = plan.dias.count()
            plan.save(update_fields=['dias_semana'])
            messages.success(request, 'Día eliminado exitosamente.')
            return redirect('editar_plan_entrenamiento', plan_id=plan.id)
        
        # Actualizar día
        elif 'actualizar_dia' in request.POST:
            dia_id = request.POST.get('dia_id')
            dia = get_object_or_404(DiaEntrenamiento, id=dia_id, plan=plan)
            numero_dia = request.POST.get('numero_dia')
            nombre_dia = request.POST.get('nombre_dia')
            descripcion = request.POST.get('descripcion', '')
            
            # Verificar que el nuevo número de día no esté ya ocupado (excepto por el día actual)
            if numero_dia and numero_dia != str(dia.numero_dia):
                if DiaEntrenamiento.objects.filter(plan=plan, numero_dia=numero_dia).exclude(id=dia.id).exists():
                    messages.error(request, 'Ya existe un entrenamiento para ese día de la semana.')
                    return redirect('editar_plan_entrenamiento', plan_id=plan.id)
            
            # Actualizar los campos
            if numero_dia:
                dia.numero_dia = numero_dia
            if nombre_dia:
                dia.nombre_dia = nombre_dia
            dia.descripcion = descripcion
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

            # Calcular siguiente orden disponible de forma segura
            intentos = 0
            while True:
                intentos += 1
                ultimo_orden = DiaEjercicio.objects.filter(dia=dia).aggregate(m=Max('orden'))['m'] or 0
                orden = int(ultimo_orden) + 1
                try:
                    DiaEjercicio.objects.create(
                        dia=dia,
                        ejercicio_id=ejercicio_id,
                        orden=orden,
                        series=series,
                        repeticiones=repeticiones,
                        peso_sugerido=peso_sugerido,
                        descanso_minutos=descanso_minutos
                    )
                    break
                except IntegrityError:
                    # En caso de colisión (doble submit), reintentar con un orden mayor
                    if intentos >= 3:
                        messages.error(request, 'No se pudo agregar el ejercicio por un conflicto de orden. Intenta nuevamente.')
                        return redirect('editar_plan_entrenamiento', plan_id=plan.id)
                    continue
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
    
    # Preparar formulario para renderizar
    # Si fue un POST inválido arriba, ya existe form_plan = form
    if request.method != 'POST' or 'form_plan' not in locals():
        # Inicializar el formulario con los datos del plan y el objetivo del perfil del usuario
        initial_data = {}
        if hasattr(request.user, 'profile') and request.user.profile.objetivo:
            initial_data['objetivo'] = request.user.profile.objetivo
        form_plan = PlanEntrenamientoForm(instance=plan, initial=initial_data)
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


# ==================== FUNCIONES DE ML PARA PLANES INTELIGENTES ====================

def generar_plan_inteligente_basico(profile):
    """
    Genera un plan de entrenamiento inteligente basado en reglas y datos del perfil
    Esta es una versión simplificada que no requiere modelo ML entrenado
    """
    # Configuraciones basadas en nivel y objetivo
    configuraciones = {
        'sedentario': {
            'series_range': (2, 3),
            'reps_ranges': {
                'perdida_peso': (12, 15),
                'hipertrofia': (10, 12),
                'recomposicion': (10, 12)
            },
            'descanso_range': (60, 90),
            'dias_semana': 3
        },
        'ligero': {
            'series_range': (3, 4),
            'reps_ranges': {
                'perdida_peso': (10, 12),
                'hipertrofia': (8, 10),
                'recomposicion': (8, 12)
            },
            'descanso_range': (90, 120),
            'dias_semana': 4
        },
        'moderado': {
            'series_range': (3, 4),
            'reps_ranges': {
                'perdida_peso': (10, 12),
                'hipertrofia': (8, 10),
                'recomposicion': (8, 12)
            },
            'descanso_range': (90, 120),
            'dias_semana': 4
        },
        'intenso': {
            'series_range': (4, 5),
            'reps_ranges': {
                'perdida_peso': (8, 10),
                'hipertrofia': (6, 8),
                'recomposicion': (6, 10)
            },
            'descanso_range': (120, 180),
            'dias_semana': 5
        }
    }
    
    # Obtener configuración para el usuario
    nivel = profile.nivel_actividad if profile.nivel_actividad in configuraciones else 'ligero'
    objetivo = profile.objetivo if profile.objetivo in ['perdida_peso', 'hipertrofia', 'recomposicion'] else 'hipertrofia'
    
    config = configuraciones[nivel]
    
    # Distribuciones de entrenamiento por días
    distribuciones_ejercicios = {
        3: [  # 3 días - Push/Pull/Legs
            {'nombre': 'Push (Pecho, Hombros, Tríceps)', 'grupos': ['Pecho', 'Hombros', 'Tríceps']},
            {'nombre': 'Pull (Espalda, Bíceps)', 'grupos': ['Espalda', 'Bíceps']},
            {'nombre': 'Legs (Piernas, Abdomen)', 'grupos': ['Piernas', 'Abdomen']}
        ],
        4: [  # 4 días - Upper/Lower
            {'nombre': 'Upper 1 (Pecho, Tríceps)', 'grupos': ['Pecho', 'Tríceps']},
            {'nombre': 'Lower 1 (Piernas)', 'grupos': ['Piernas']},
            {'nombre': 'Upper 2 (Espalda, Bíceps)', 'grupos': ['Espalda', 'Bíceps']},
            {'nombre': 'Lower 2 (Piernas, Abdomen)', 'grupos': ['Piernas', 'Abdomen']}
        ],
        5: [  # 5 días - Bro Split
            {'nombre': 'Pecho', 'grupos': ['Pecho']},
            {'nombre': 'Espalda', 'grupos': ['Espalda']},
            {'nombre': 'Piernas', 'grupos': ['Piernas']},
            {'nombre': 'Hombros', 'grupos': ['Hombros']},
            {'nombre': 'Brazos (Bíceps, Tríceps, Abdomen)', 'grupos': ['Bíceps', 'Tríceps', 'Abdomen']}
        ]
    }
    
    dias_semana = config['dias_semana']
    distribucion = distribuciones_ejercicios[dias_semana]
    
    # Seleccionar ejercicios por grupo muscular
    ejercicios_por_grupo = {
        'Pecho': [1, 2, 3],  # Press Banca, Press Inclinado, Aperturas
        'Espalda': [6, 7, 8],  # Dominadas, Remo, Jalón
        'Piernas': [11, 12, 13, 14],  # Sentadilla, Prensa, Peso Muerto, Extensiones
        'Hombros': [15, 16, 17],  # Press Militar, Elevaciones, Face Pulls
        'Bíceps': [9, 10],  # Curl Barra, Curl Martillo
        'Tríceps': [4, 5],  # Fondos, Press Francés
        'Abdomen': [18, 19]  # Plancha, Crunch
    }
    
    # Calcular parámetros personalizados
    peso_corporal = float(profile.peso)
    
    # Factores de peso por grupo muscular (porcentaje del peso corporal)
    factores_peso = {
        'Pecho': 0.8 + (0.2 if nivel == 'intenso' else 0.1 if nivel in ['moderado', 'ligero'] else 0),
        'Espalda': 0.7 + (0.3 if nivel == 'intenso' else 0.2 if nivel in ['moderado', 'ligero'] else 0.1),
        'Piernas': 1.2 + (0.3 if nivel == 'intenso' else 0.2 if nivel in ['moderado', 'ligero'] else 0),
        'Hombros': 0.4 + (0.2 if nivel == 'intenso' else 0.1 if nivel in ['moderado', 'ligero'] else 0),
        'Bíceps': 0.3 + (0.15 if nivel == 'intenso' else 0.1 if nivel in ['moderado', 'ligero'] else 0.05),
        'Tríceps': 0.4 + (0.2 if nivel == 'intenso' else 0.1 if nivel in ['moderado', 'ligero'] else 0.05),
        'Abdomen': 0  # Peso corporal
    }
    
    plan_generado = {}
    
    for dia_num, info_dia in enumerate(distribucion, 1):
        ejercicios_dia = []
        
        for grupo in info_dia['grupos']:
            ejercicios_disponibles = ejercicios_por_grupo.get(grupo, [])
            
            # Número de ejercicios por grupo
            if len(info_dia['grupos']) == 1:  # Día enfocado en un solo grupo
                num_ejercicios = min(len(ejercicios_disponibles), 4)
            elif len(info_dia['grupos']) == 2:  # Dos grupos
                num_ejercicios = min(len(ejercicios_disponibles), 3)
            else:  # Tres o más grupos
                num_ejercicios = min(len(ejercicios_disponibles), 2)
            
            # Seleccionar ejercicios (tomar los primeros para consistencia)
            ejercicios_seleccionados = ejercicios_disponibles[:num_ejercicios]
            
            for ejercicio_id in ejercicios_seleccionados:
                # Calcular parámetros
                series = config['series_range'][0] if objetivo == 'perdida_peso' else config['series_range'][1]
                
                reps_range = config['reps_ranges'][objetivo]
                repeticiones = f"{reps_range[0]}-{reps_range[1]}"
                
                # Peso sugerido
                factor_peso = factores_peso.get(grupo, 0.5)
                peso_sugerido = round(peso_corporal * factor_peso, 1) if factor_peso > 0 else None
                
                # Descanso (en minutos)
                descanso_base = config['descanso_range'][1] if grupo in ['Pecho', 'Espalda', 'Piernas'] else config['descanso_range'][0]
                descanso_minutos = round(descanso_base / 60, 1)
                
                ejercicios_dia.append({
                    'ejercicio_id': ejercicio_id,
                    'series': series,
                    'repeticiones': repeticiones,
                    'peso_sugerido': peso_sugerido,
                    'descanso_minutos': descanso_minutos
                })
        
        plan_generado[dia_num] = {
            'nombre_dia': info_dia['nombre'],
            'ejercicios': ejercicios_dia
        }
    
    return plan_generado, dias_semana


@login_required
def generar_plan_inteligente(request):
    """
    Vista para generar un plan de entrenamiento inteligente basado en el perfil del usuario
    """
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        messages.error(request, 'Debes crear tu perfil primero para generar un plan inteligente.')
        return redirect('crear_perfil')
    
    if request.method == 'POST':
        # Generar plan inteligente
        plan_data, dias_semana = generar_plan_inteligente_basico(profile)
        
        # Crear el plan en la base de datos
        # Desactivar planes activos previos
        PlanEntrenamiento.objects.filter(
            usuario=request.user, 
            estado='activo'
        ).update(estado='pausado')
        
        # Crear nuevo plan
        nuevo_plan = PlanEntrenamiento.objects.create(
            usuario=request.user,
            nombre_plan=f"Plan Inteligente {profile.get_objetivo_display()}",
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(weeks=8),
            objetivo=profile.objetivo,
            estado='activo',
            dias_semana=dias_semana
        )
        
        # Crear días y ejercicios
        for dia_num, info_dia in plan_data.items():
            # Mapear día número a día de la semana
            dias_mapping = {1: 1, 2: 3, 3: 5, 4: 6, 5: 2}  # Lun, Mie, Vie, Sab, Mar
            numero_dia_semana = dias_mapping.get(dia_num, dia_num)
            
            dia_entrenamiento = DiaEntrenamiento.objects.create(
                plan=nuevo_plan,
                numero_dia=numero_dia_semana,
                nombre_dia=info_dia['nombre_dia'],
                descripcion=f"Entrenamiento generado automáticamente para {profile.get_objetivo_display()}"
            )
            
            # Agregar ejercicios
            for orden, ejercicio_info in enumerate(info_dia['ejercicios'], 1):
                DiaEjercicio.objects.create(
                    dia=dia_entrenamiento,
                    ejercicio_id=ejercicio_info['ejercicio_id'],
                    orden=orden,
                    series=ejercicio_info['series'],
                    repeticiones=ejercicio_info['repeticiones'],
                    peso_sugerido=ejercicio_info['peso_sugerido'],
                    descanso_minutos=ejercicio_info['descanso_minutos']
                )
        
        messages.success(request, f'¡Plan inteligente generado exitosamente! Se creó un plan de {dias_semana} días adaptado a tu perfil.')
        return redirect('ver_plan_entrenamiento', plan_id=nuevo_plan.id)
    
    # Vista previa del plan que se generaría
    plan_preview, dias_semana = generar_plan_inteligente_basico(profile)
    
    context = {
        'profile': profile,
        'plan_preview': plan_preview,
        'dias_semana': dias_semana
    }
    
    return render(request, 'generar-plan-inteligente.html', context)
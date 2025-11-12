from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import UserProfile, PlanEntrenamiento, DiaEntrenamiento, DiaEjercicio, Ejercicio

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Correo', widget=forms.EmailInput(attrs={'placeholder': 'correo@ejemplo.com'}))
    first_name = forms.CharField(required=True, label='Nombre', widget=forms.TextInput(attrs={'placeholder': 'Tu nombre'}))
    last_name = forms.CharField(required=True, label='Apellido', widget=forms.TextInput(attrs={'placeholder': 'Tu apellido'}))

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Ya existe una cuenta con ese correo electrónico.')
        return email


class UserProfileStep1Form(forms.ModelForm):
    """Formulario para el Paso 1: Datos Personales"""
    class Meta:
        model = UserProfile
        fields = ['edad', 'sexo', 'peso', 'altura', 'imc']
        widgets = {
            'edad': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Edad',
                'min': '13',
                'max': '100'
            }),
            'sexo': forms.Select(attrs={
                'class': 'form-control'
            }),
            'peso': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Peso en kg',
                'step': '0.01',
                'min': '20',
                'max': '400'
            }),
            'altura': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Altura en cm',
                'min': '80',
                'max': '300'
            }),
            'imc': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'IMC (se calcula automáticamente)',
                'step': '0.01'
            }),
        }
        labels = {
            'edad': 'Edad',
            'sexo': 'Sexo',
            'peso': 'Peso (kg)',
            'altura': 'Altura (cm)',
            'imc': 'Índice de Masa Corporal (IMC)',
        }


class UserProfileStep2Form(forms.ModelForm):
    """Formulario para el Paso 2: Datos de Entrenamiento"""
    class Meta:
        model = UserProfile
        fields = ['nivel_actividad', 'objetivo', 'porcentaje_grasa', 'tiempo_entrenamiento']
        widgets = {
            'nivel_actividad': forms.Select(attrs={
                'class': 'form-control'
            }),
            'objetivo': forms.Select(attrs={
                'class': 'form-control'
            }),
            'porcentaje_grasa': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Porcentaje de grasa corporal',
                'step': '0.1',
                'min': '3',
                'max': '60'
            }),
            'tiempo_entrenamiento': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tiempo en minutos',
                'min': '10',
                'max': '230'
            }),
        }
        labels = {
            'nivel_actividad': 'Nivel de Actividad',
            'objetivo': 'Objetivo',
            'porcentaje_grasa': 'Porcentaje de Grasa Corporal (%)',
            'tiempo_entrenamiento': 'Tiempo Promedio de Entrenamiento (minutos)',
        }


class UserProfileEditForm(forms.ModelForm):
    """Formulario completo para editar el perfil"""
    class Meta:
        model = UserProfile
        fields = ['edad', 'sexo', 'peso', 'altura', 'imc', 'nivel_actividad', 
                  'objetivo', 'porcentaje_grasa', 'tiempo_entrenamiento', 'foto_perfil']
        widgets = {
            'edad': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '13',
                'max': '100'
            }),
            'sexo': forms.Select(attrs={
                'class': 'form-control'
            }),
            'peso': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '20',
                'max': '400'
            }),
            'altura': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '80',
                'max': '300'
            }),
            'imc': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'nivel_actividad': forms.Select(attrs={
                'class': 'form-control'
            }),
            'objetivo': forms.Select(attrs={
                'class': 'form-control'
            }),
            'porcentaje_grasa': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '3',
                'max': '60'
            }),
            'tiempo_entrenamiento': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '10',
                'max': '230'
            }),
            'foto_perfil': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
        }
        labels = {
            'edad': 'Edad',
            'sexo': 'Sexo',
            'peso': 'Peso (kg)',
            'altura': 'Altura (cm)',
            'imc': 'IMC',
            'nivel_actividad': 'Nivel de Actividad',
            'objetivo': 'Objetivo',
            'porcentaje_grasa': 'Porcentaje de Grasa (%)',
            'tiempo_entrenamiento': 'Tiempo de Entrenamiento (min)',
            'foto_perfil': 'Foto de Perfil',
        }


# ==================== FORMULARIOS DE ENTRENAMIENTO ====================

class PlanEntrenamientoForm(forms.ModelForm):
    """Formulario para editar información básica del plan"""
    OBJETIVO_CHOICES = [
        ('perdida_peso', 'Pérdida de peso'),
        ('recomposicion', 'Recomposición genética'),
        ('hipertrofia', 'Hipertrofia'),
    ]
    
    # Sobrescribir el campo objetivo para usar un select
    objetivo = forms.ChoiceField(
        choices=OBJETIVO_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Objetivo de Entrenamiento',
    )
    
    # Sobrescribir el campo nombre_plan para cambiar el help_text
    nombre_plan = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': ''
        }),
        label='Nombre del Plan',
        help_text='',  # Eliminar el help_text o poner el texto que quieras
    )
    
    class Meta:
        model = PlanEntrenamiento
        fields = ['nombre_plan', 'fecha_inicio', 'fecha_fin', 'objetivo', 'dias_semana', 'estado']
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'fecha_fin': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'dias_semana': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '7',
                'readonly': 'readonly',
                'disabled': 'disabled'
            }),
            'estado': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'nombre_plan': 'Nombre del Plan',
            'fecha_inicio': 'Fecha de Inicio',
            'fecha_fin': 'Fecha de Fin',
            'objetivo': 'Objetivo',
            'dias_semana': '',
            'estado': 'Estado del Plan',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Deshabilitar a nivel de formulario para que no sea requerido ni procesado desde el POST
        if 'dias_semana' in self.fields:
            self.fields['dias_semana'].disabled = True
            self.fields['dias_semana'].required = False


class DiaEntrenamientoForm(forms.ModelForm):
    """Formulario para editar un día de entrenamiento"""
    class Meta:
        model = DiaEntrenamiento
        fields = ['numero_dia', 'nombre_dia', 'descripcion']
        widgets = {
            'numero_dia': forms.Select(attrs={
                'class': 'form-control'
            }),
            'nombre_dia': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Pecho y Tríceps'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Descripción del día (opcional)'
            }),
        }
        labels = {
            'numero_dia': 'Día de la Semana',
            'nombre_dia': 'Nombre del Día',
            'descripcion': 'Descripción',
        }


class DiaEjercicioForm(forms.ModelForm):
    """Formulario para editar un ejercicio dentro de un día"""
    class Meta:
        model = DiaEjercicio
        fields = ['ejercicio', 'orden', 'series', 'repeticiones', 'peso_sugerido', 'descanso_minutos']
        widgets = {
            'ejercicio': forms.Select(attrs={
                'class': 'form-control'
            }),
            'orden': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'series': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '10'
            }),
            'repeticiones': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 8-12, 15, 20+'
            }),
            'peso_sugerido': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.5',
                'placeholder': 'Peso en kg (opcional)'
            }),
            'descanso_minutos': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.5',
                'min': '0.5',
                'max': '10'
            }),
        }
        labels = {
            'ejercicio': 'Ejercicio',
            'orden': 'Orden',
            'series': 'Series',
            'repeticiones': 'Repeticiones',
            'peso_sugerido': 'Peso Sugerido (kg)',
            'descanso_minutos': 'Descanso (minutos)',
        }

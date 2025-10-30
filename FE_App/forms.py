from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import UserProfile

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

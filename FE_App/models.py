from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

class UserProfile(models.Model):
    SEXO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
    ]
    
    NIVEL_ACTIVIDAD_CHOICES = [
        ('sedentario', 'Sedentario'),
        ('ligero', 'Ligero'),
        ('moderado', 'Moderado'),
        ('intenso', 'Intenso'),
    ]
    
    OBJETIVO_CHOICES = [
        ('perdida_peso', 'Pérdida de peso'),
        ('recomposicion', 'Recomposición genética'),
        ('hipertrofia', 'Hipertrofia'),
    ]
    
    # Relación uno a uno con el usuario
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    
    # Datos personales (Paso 1 - Obligatorios)
    edad = models.IntegerField(validators=[MinValueValidator(13), MaxValueValidator(100)])
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES)
    peso = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(20), MaxValueValidator(400)], help_text="Peso en kilogramos")
    altura = models.IntegerField(validators=[MinValueValidator(80), MaxValueValidator(300)], help_text="Altura en centímetros")
    imc = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Índice de Masa Corporal")
    
    # Datos de entrenamiento (Paso 2 - Obligatorios)
    nivel_actividad = models.CharField(max_length=20, choices=NIVEL_ACTIVIDAD_CHOICES)
    objetivo = models.CharField(max_length=20, choices=OBJETIVO_CHOICES)
    porcentaje_grasa = models.DecimalField(max_digits=4, decimal_places=1, validators=[MinValueValidator(1), MaxValueValidator(300)], help_text="Porcentaje de grasa corporal")
    tiempo_entrenamiento = models.IntegerField(validators=[MinValueValidator(10), MaxValueValidator(230)], help_text="Tiempo promedio de entrenamiento por sesión en minutos", null=True, blank=True)
    
    # Foto de perfil (opcional)
    foto_perfil = models.ImageField(upload_to='perfiles/', blank=True, null=True)
    
    # Timestamps
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        try:
            # Convertir peso y altura a float (por si llegan como texto)
            peso = float(self.peso)
            altura = float(self.altura)
            altura_metros = altura / 100

            # Calcular IMC automáticamente si hay datos válidos
            if peso > 0 and altura_metros > 0:
                self.imc = round(peso / (altura_metros ** 2), 2)

            # Calcular porcentaje de grasa corporal si hay datos suficientes
            if self.imc and self.edad and self.sexo:
                S = 1 if self.sexo == 'M' else 0
                grasa = (1.20 * float(self.imc)) + (0.23 * float(self.edad)) - (10.8 * S) - 5.4
                grasa = max(3, min(grasa, 70))  # limitar entre 3% y 70%
                self.porcentaje_grasa = round(grasa, 1)

        except (ValueError, TypeError):
            # En caso de error, evita romper el guardado
            self.imc = None
            self.porcentaje_grasa = None

        super().save(*args, **kwargs)

    
    def __str__(self):
        return f"Perfil de {self.usuario.username}"
    
    class Meta:
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuarios"

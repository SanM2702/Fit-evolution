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


# ==================== MODELOS DE ENTRENAMIENTO ====================

class GrupoMuscular(models.Model):
    """Grupos musculares (pecho, espalda, piernas, etc.)"""
    nombre_grupo = models.CharField(max_length=50, unique=True, help_text="Ej: Pecho, Espalda, Piernas")
    descripcion = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.nombre_grupo
    
    class Meta:
        verbose_name = "Grupo Muscular"
        verbose_name_plural = "Grupos Musculares"
        ordering = ['nombre_grupo']


class Ejercicio(models.Model):
    """Ejercicios específicos con su grupo muscular"""
    NIVEL_CHOICES = [
        ('principiante', 'Principiante'),
        ('intermedio', 'Intermedio'),
        ('avanzado', 'Avanzado'),
    ]
    
    TIPO_EQUIPO_CHOICES = [
        ('mancuerna', 'Mancuerna'),
        ('barra', 'Barra'),
        ('polea', 'Polea'),
        ('maquina', 'Máquina'),
        ('peso_corporal', 'Peso Corporal'),
        ('banda_elastica', 'Banda Elástica'),
        ('kettlebell', 'Kettlebell'),
    ]
    
    grupo_muscular = models.ForeignKey(GrupoMuscular, on_delete=models.CASCADE, related_name='ejercicios')
    nombre_ejercicio = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True, help_text="Técnica y consejos")
    tipo_equipo = models.CharField(max_length=20, choices=TIPO_EQUIPO_CHOICES)
    nivel = models.CharField(max_length=15, choices=NIVEL_CHOICES, default='intermedio')
    
    def __str__(self):
        return f"{self.nombre_ejercicio} ({self.grupo_muscular.nombre_grupo})"
    
    class Meta:
        verbose_name = "Ejercicio"
        verbose_name_plural = "Ejercicios"
        ordering = ['grupo_muscular', 'nombre_ejercicio']


class PlanEntrenamiento(models.Model):
    """Plan de entrenamiento personalizado para cada usuario"""
    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('completado', 'Completado'),
        ('pausado', 'Pausado'),
    ]
    
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='planes_entrenamiento')
    nombre_plan = models.CharField(max_length=100, help_text="Ej: Plan Hipertrofia 12 semanas")
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    objetivo = models.CharField(max_length=100, help_text="Objetivo del plan")
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='activo')
    
    # Campos de predicción ML (por ahora datos de ejemplo)
    dias_semana = models.IntegerField(default=4, validators=[MinValueValidator(1), MaxValueValidator(7)], help_text="Días de entrenamiento por semana")
    riesgo_lesion = models.BooleanField(default=False, help_text="Predicción ML: Riesgo de lesión")
    riesgo_estancamiento = models.BooleanField(default=False, help_text="Predicción ML: Riesgo de estancamiento")
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.nombre_plan} - {self.usuario.username}"
    
    class Meta:
        verbose_name = "Plan de Entrenamiento"
        verbose_name_plural = "Planes de Entrenamiento"
        ordering = ['-fecha_creacion']


class DiaEntrenamiento(models.Model):
    """Día específico dentro de un plan de entrenamiento"""
    DIAS_SEMANA = [
        (1, 'Lunes'),
        (2, 'Martes'),
        (3, 'Miércoles'),
        (4, 'Jueves'),
        (5, 'Viernes'),
        (6, 'Sábado'),
        (7, 'Domingo'),
    ]
    
    plan = models.ForeignKey(PlanEntrenamiento, on_delete=models.CASCADE, related_name='dias')
    numero_dia = models.IntegerField(choices=DIAS_SEMANA, help_text="Día de la semana")
    nombre_dia = models.CharField(max_length=100, help_text="Ej: Pecho y Tríceps")
    descripcion = models.TextField(blank=True, null=True, help_text="Notas adicionales del día")
    
    def __str__(self):
        return f"{self.get_numero_dia_display()} - {self.nombre_dia}"
    
    class Meta:
        verbose_name = "Día de Entrenamiento"
        verbose_name_plural = "Días de Entrenamiento"
        ordering = ['plan', 'numero_dia']
        unique_together = ['plan', 'numero_dia']


class DiaEjercicio(models.Model):
    """Tabla intermedia: Ejercicios asignados a un día específico"""
    dia = models.ForeignKey(DiaEntrenamiento, on_delete=models.CASCADE, related_name='ejercicios_asignados')
    ejercicio = models.ForeignKey(Ejercicio, on_delete=models.CASCADE, related_name='dias_asignados')
    orden = models.IntegerField(help_text="Posición en la rutina del día")
    series = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)], help_text="Número de series")
    repeticiones = models.CharField(max_length=20, help_text="Ej: 8-12, 15, 20+")
    peso_sugerido = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Peso sugerido en kg")
    descanso_minutos = models.DecimalField(max_digits=3, decimal_places=1, help_text="Descanso entre series en minutos")
    
    def __str__(self):
        return f"{self.dia.nombre_dia} - {self.ejercicio.nombre_ejercicio} (Orden {self.orden})"
    
    class Meta:
        verbose_name = "Ejercicio del Día"
        verbose_name_plural = "Ejercicios del Día"
        ordering = ['dia', 'orden']
        unique_together = ['dia', 'orden']


class HistorialEntrenamiento(models.Model):
    """Registro de entrenamientos completados por el usuario"""
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='historial_entrenamientos')
    dia_ejercicio = models.ForeignKey(DiaEjercicio, on_delete=models.CASCADE, related_name='registros')
    fecha = models.DateTimeField(auto_now_add=True)
    serie_num = models.IntegerField(validators=[MinValueValidator(1)], help_text="Número de serie realizada")
    repeticiones_realizadas = models.IntegerField(validators=[MinValueValidator(0)])
    peso_utilizado = models.DecimalField(max_digits=5, decimal_places=2, help_text="Peso utilizado en kg")
    rpe = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)], help_text="Rate of Perceived Exertion (1-10)")
    molestia_nivel = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(10)], default=0, help_text="Nivel de molestia/dolor (0-10)")
    notas = models.TextField(blank=True, null=True, help_text="Notas adicionales")
    
    def __str__(self):
        return f"{self.usuario.username} - {self.dia_ejercicio.ejercicio.nombre_ejercicio} - {self.fecha.strftime('%Y-%m-%d')}"
    
    class Meta:
        verbose_name = "Historial de Entrenamiento"
        verbose_name_plural = "Historiales de Entrenamiento"
        ordering = ['-fecha']

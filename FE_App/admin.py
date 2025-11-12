from django.contrib import admin
from .models import (
    UserProfile, 
    GrupoMuscular, 
    Ejercicio, 
    PlanEntrenamiento, 
    DiaEntrenamiento, 
    DiaEjercicio, 
    HistorialEntrenamiento
)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['id', 'usuario', 'edad', 'sexo', 'peso', 'altura', 'imc', 'objetivo', 'nivel_actividad', 'fecha_creacion']
    list_filter = ['sexo', 'objetivo', 'nivel_actividad', 'fecha_creacion']
    search_fields = ['usuario__username', 'usuario__email', 'usuario__first_name', 'usuario__last_name']
    readonly_fields = ['id', 'fecha_creacion', 'fecha_actualizacion']
    list_display_links = ['id', 'usuario']
    
    fieldsets = (
        ('Usuario', {
            'fields': ('usuario',)
        }),
        ('Datos Personales', {
            'fields': ('edad', 'sexo', 'peso', 'altura', 'imc')
        }),
        ('Datos de Entrenamiento', {
            'fields': ('nivel_actividad', 'objetivo', 'porcentaje_grasa', 'tiempo_entrenamiento')
        }),
        ('Foto de Perfil', {
            'fields': ('foto_perfil',)
        }),
        ('Información del Sistema', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )


# ==================== ADMINISTRACIÓN DE ENTRENAMIENTO ====================

@admin.register(GrupoMuscular)
class GrupoMuscularAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre_grupo', 'descripcion', 'total_ejercicios']
    search_fields = ['nombre_grupo', 'descripcion']
    ordering = ['nombre_grupo']
    list_display_links = ['id', 'nombre_grupo']
    
    def total_ejercicios(self, obj):
        return obj.ejercicios.count()
    total_ejercicios.short_description = 'Total Ejercicios'


@admin.register(Ejercicio)
class EjercicioAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre_ejercicio', 'grupo_muscular', 'tipo_equipo', 'nivel']
    list_filter = ['grupo_muscular', 'tipo_equipo', 'nivel']
    search_fields = ['nombre_ejercicio', 'descripcion']
    ordering = ['grupo_muscular', 'nombre_ejercicio']
    list_display_links = ['id', 'nombre_ejercicio']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre_ejercicio', 'grupo_muscular', 'descripcion')
        }),
        ('Características', {
            'fields': ('tipo_equipo', 'nivel')
        }),
    )


class DiaEjercicioInline(admin.TabularInline):
    model = DiaEjercicio
    extra = 1
    fields = ['ejercicio', 'orden', 'series', 'repeticiones', 'peso_sugerido', 'descanso_minutos']
    ordering = ['orden']


@admin.register(DiaEntrenamiento)
class DiaEntrenamientoAdmin(admin.ModelAdmin):
    list_display = ['id', 'plan', 'get_numero_dia_display', 'nombre_dia', 'total_ejercicios']
    list_filter = ['numero_dia', 'plan__usuario']
    search_fields = ['nombre_dia', 'descripcion', 'plan__nombre_plan']
    ordering = ['plan', 'numero_dia']
    inlines = [DiaEjercicioInline]
    list_display_links = ['id', 'nombre_dia']
    
    fieldsets = (
        ('Plan', {
            'fields': ('plan',)
        }),
        ('Información del Día', {
            'fields': ('numero_dia', 'nombre_dia', 'descripcion')
        }),
    )
    
    def total_ejercicios(self, obj):
        return obj.ejercicios_asignados.count()
    total_ejercicios.short_description = 'Total Ejercicios'


class DiaEntrenamientoInline(admin.TabularInline):
    model = DiaEntrenamiento
    extra = 0
    fields = ['numero_dia', 'nombre_dia']
    show_change_link = True


@admin.register(PlanEntrenamiento)
class PlanEntrenamientoAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre_plan', 'usuario', 'fecha_inicio', 'fecha_fin', 'dias_semana', 'estado', 'total_dias']
    list_filter = ['estado', 'fecha_inicio', 'riesgo_lesion', 'riesgo_estancamiento']
    search_fields = ['nombre_plan', 'usuario__username', 'objetivo']
    readonly_fields = ['id', 'fecha_creacion', 'fecha_actualizacion']
    date_hierarchy = 'fecha_inicio'
    inlines = [DiaEntrenamientoInline]
    list_display_links = ['id', 'nombre_plan']
    
    fieldsets = (
        ('Usuario', {
            'fields': ('usuario',)
        }),
        ('Información del Plan', {
            'fields': ('nombre_plan', 'objetivo', 'fecha_inicio', 'fecha_fin', 'dias_semana', 'estado')
        }),
        ('Predicciones ML', {
            'fields': ('riesgo_lesion', 'riesgo_estancamiento'),
            'classes': ('collapse',)
        }),
        ('Información del Sistema', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    def total_dias(self, obj):
        return obj.dias.count()
    total_dias.short_description = 'Días Configurados'


@admin.register(DiaEjercicio)
class DiaEjercicioAdmin(admin.ModelAdmin):
    list_display = ['id', 'dia', 'ejercicio', 'orden', 'series', 'repeticiones', 'peso_sugerido', 'descanso_minutos']
    list_filter = ['dia__plan__usuario', 'ejercicio__grupo_muscular']
    search_fields = ['ejercicio__nombre_ejercicio', 'dia__nombre_dia']
    ordering = ['dia', 'orden']
    readonly_fields = ['id']
    list_display_links = ['id', 'ejercicio']
    
    fieldsets = (
        ('Día de Entrenamiento', {
            'fields': ('dia',)
        }),
        ('Ejercicio', {
            'fields': ('ejercicio', 'orden')
        }),
        ('Configuración', {
            'fields': ('series', 'repeticiones', 'peso_sugerido', 'descanso_minutos')
        }),
    )


@admin.register(HistorialEntrenamiento)
class HistorialEntrenamientoAdmin(admin.ModelAdmin):
    list_display = ['id', 'usuario', 'get_ejercicio', 'fecha', 'serie_num', 'repeticiones_realizadas', 'peso_utilizado', 'rpe', 'molestia_nivel']
    list_filter = ['fecha', 'usuario', 'rpe', 'molestia_nivel']
    search_fields = ['usuario__username', 'dia_ejercicio__ejercicio__nombre_ejercicio', 'notas']
    readonly_fields = ['id', 'fecha']
    date_hierarchy = 'fecha'
    list_display_links = ['id', 'usuario']
    
    fieldsets = (
        ('Usuario y Ejercicio', {
            'fields': ('usuario', 'dia_ejercicio')
        }),
        ('Datos de la Serie', {
            'fields': ('serie_num', 'repeticiones_realizadas', 'peso_utilizado')
        }),
        ('Percepción', {
            'fields': ('rpe', 'molestia_nivel', 'notas')
        }),
        ('Fecha', {
            'fields': ('fecha',)
        }),
    )
    
    def get_ejercicio(self, obj):
        return obj.dia_ejercicio.ejercicio.nombre_ejercicio
    get_ejercicio.short_description = 'Ejercicio'

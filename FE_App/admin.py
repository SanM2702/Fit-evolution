from django.contrib import admin
from .models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'edad', 'sexo', 'peso', 'altura', 'imc', 'objetivo', 'nivel_actividad', 'fecha_creacion']
    list_filter = ['sexo', 'objetivo', 'nivel_actividad', 'fecha_creacion']
    search_fields = ['usuario__username', 'usuario__email', 'usuario__first_name', 'usuario__last_name']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    
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

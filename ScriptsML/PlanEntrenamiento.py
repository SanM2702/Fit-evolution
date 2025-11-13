import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.neighbors import NearestNeighbors
import joblib
import os
from collections import defaultdict

# ===============================================
# 1. Cargar dataset
# ===============================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(CURRENT_DIR)
ARTIFACT_DIR = os.path.join(PROJECT_DIR, "ModelosML", "PlanEntrenamiento")
os.makedirs(ARTIFACT_DIR, exist_ok=True)

DATASET_PATH = os.path.join(PROJECT_DIR, "Fit-Evolution_Dataset.csv")
df_full = pd.read_csv(DATASET_PATH)

# Seleccionar columnas útiles
columnas_usadas = [
    'Edad', 'Género', 'Peso_(kg)', 'Altura_(m)', 'IMC', 
    'Porcentaje_grasa', 'Nivel_experiencia',
    'Duración_sesión_(horas)', 'Frecuencia_entrenamiento_(días/semana)',
    'Objetivo',
    'Tipo_entrenamiento', 'Entrenamiento', 'Grupo_muscular_objetivo',
    'Equipamiento_necesario', 'Nivel_dificultad', 'Parte_cuerpo'
]

df = df_full[columnas_usadas].dropna().reset_index(drop=True)

# ===============================================
# 2. Preprocesamiento y entrenamiento (solo si no existe el modelo)
# ===============================================
model_path = os.path.join(ARTIFACT_DIR, "fit_model_knn.pkl")
if not os.path.exists(model_path):
    label_cols = ['Género', 'Nivel_experiencia', 'Objetivo']
    encoders = {}
    
    for col in label_cols:
        encoders[col] = LabelEncoder()
        df[col] = encoders[col].fit_transform(df[col])

    X = df[['Edad', 'Género', 'Peso_(kg)', 'Altura_(m)', 'IMC',
            'Porcentaje_grasa', 'Nivel_experiencia',
            'Duración_sesión_(horas)', 'Frecuencia_entrenamiento_(días/semana)', 'Objetivo']]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    k = 20  # Aumentamos para tener más variedad
    model_knn = NearestNeighbors(n_neighbors=k, metric='euclidean')
    model_knn.fit(X_scaled)

    joblib.dump(model_knn, os.path.join(ARTIFACT_DIR, "fit_model_knn.pkl"))
    joblib.dump(scaler, os.path.join(ARTIFACT_DIR, "fit_scaler.pkl"))
    joblib.dump(encoders, os.path.join(ARTIFACT_DIR, "fit_encoders.pkl"))

# ===============================================
# 3. Función para generar plan semanal
# ===============================================
def generar_plan_semanal(usuario):
    """
    Genera un plan semanal (7 días) con ejercicios asignados solo en los días de entrenamiento.
    usuario: dict con campos necesarios + "Días_entrenamiento" (opcional, si quieres elegir días específicos)
    """
    # Cargar artefactos
    model_knn = joblib.load(os.path.join(ARTIFACT_DIR, "fit_model_knn.pkl"))
    scaler = joblib.load(os.path.join(ARTIFACT_DIR, "fit_scaler.pkl"))
    encoders = joblib.load(os.path.join(ARTIFACT_DIR, "fit_encoders.pkl"))

    df = df_full[columnas_usadas].dropna().reset_index(drop=True)

    usuario_input = usuario.copy()
    for col, encoder in encoders.items():
        if usuario_input[col] in encoder.classes_:
            usuario_input[col] = encoder.transform([usuario_input[col]])[0]
        else:
            usuario_input[col] = 0

    X_user = np.array([[
        usuario_input['Edad'],
        usuario_input['Género'],
        usuario_input['Peso_(kg)'],
        usuario_input['Altura_(m)'],
        usuario_input['IMC'],
        usuario_input['Porcentaje_grasa'],
        usuario_input['Nivel_experiencia'],
        usuario_input['Duración_sesión_(horas)'],
        usuario_input['Frecuencia_entrenamiento_(días/semana)'],
        usuario_input['Objetivo']
    ]])

    X_user_scaled = scaler.transform(X_user)
    distances, indices = model_knn.kneighbors(X_user_scaled)
    ejercicios_candidatos = df.iloc[indices[0]]

    # Agrupar por tipo de entrenamiento y grupo muscular para diversidad
    ejercicios_candidatos = ejercicios_candidatos.drop_duplicates(subset=[
        'Entrenamiento', 'Grupo_muscular_objetivo', 'Parte_cuerpo'
    ]).sample(frac=1).reset_index(drop=True)

    dias_entrenamiento = int(usuario['Frecuencia_entrenamiento_(días/semana)'])
    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

    # Opcional: permitir al usuario elegir qué días entrenar (ej. ["Lunes", "Miércoles", "Viernes"])
    if 'Días_entrenamiento' in usuario and isinstance(usuario['Días_entrenamiento'], list):
        dias_seleccionados = [d for d in usuario['Días_entrenamiento'] if d in dias_semana]
        if len(dias_seleccionados) < dias_entrenamiento:
            # Completar con otros días si faltan
            restantes = [d for d in dias_semana if d not in dias_seleccionados]
            dias_seleccionados += restantes[:dias_entrenamiento - len(dias_seleccionados)]
    else:
        dias_seleccionados = dias_semana[:dias_entrenamiento]

    # Asignar ejercicios a los días
    plan_semanal = {dia: [] for dia in dias_semana}
    ejercicios_disponibles = ejercicios_candidatos.to_dict('records')

    for i, dia in enumerate(dias_seleccionados):
        if i < len(ejercicios_disponibles):
            ejercicio = ejercicios_disponibles[i]
            plan_semanal[dia] = [ejercicio]
        else:
            # Reutilizar de forma balanceada si hay más días que candidatos
            idx = i % len(ejercicios_disponibles)
            plan_semanal[dia] = [ejercicios_disponibles[idx]]

    # Formatear salida
    resultado = {}
    for dia in dias_semana:
        if plan_semanal[dia]:
            ej = plan_semanal[dia][0]
            resultado[dia] = {
                "Entrenamiento": ej['Entrenamiento'],
                "Tipo": ej['Tipo_entrenamiento'],
                "Grupo_muscular": ej['Grupo_muscular_objetivo'],
                "Parte_cuerpo": ej['Parte_cuerpo'],
                "Dificultad": ej['Nivel_dificultad'],
                "Equipamiento": ej['Equipamiento_necesario']
            }
        else:
            resultado[dia] = "Descanso"

    return resultado

# ===============================================
# Ejemplo de uso
# ===============================================
if __name__ == "__main__":
    usuario_ejemplo = {
        "Edad": 28,
        "Género": "Hombre",
        "Peso_(kg)": 75.0,
        "Altura_(m)": 1.75,
        "IMC": 24.5,
        "Porcentaje_grasa": 18.0,
        "Nivel_experiencia": "Intermedio",
        "Duración_sesión_(horas)": 1.5,
        "Frecuencia_entrenamiento_(días/semana)": 4,
        "Objetivo": "Hipertrofia"
        # Opcional: "Días_entrenamiento": ["Lunes", "Martes", "Jueves", "Sábado"]
    }

    plan = generar_plan_semanal(usuario_ejemplo)
    for dia, info in plan.items():
        print(f"\n{dia}:")
        if info == "Descanso":
            print("  → Descanso")
        else:
            for k, v in info.items():
                print(f"  {k}: {v}")

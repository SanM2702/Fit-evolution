import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.multioutput import MultiOutputRegressor, MultiOutputClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_squared_error, accuracy_score, classification_report
import joblib
import os
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

class PlanEntrenamientoML:
    def __init__(self):
        self.ejercicio_classifier = None
        self.parametros_regressor = None
        self.scaler_features = StandardScaler()
        self.le_objetivo = LabelEncoder()
        self.le_nivel = LabelEncoder()
        self.le_sexo = LabelEncoder()
        self.ejercicios_por_grupo = {}
        
    def generar_dataset_sintetico(self, n_samples=5000):
        """
        Genera un dataset sintético basado en conocimiento de entrenamiento
        """
        np.random.seed(42)
        
        # Definir ejercicios por grupo muscular (basado en tu BD)
        ejercicios_grupos = {
            'Pecho': [1, 2, 3],  # Press Banca, Press Inclinado, Aperturas
            'Espalda': [6, 7, 8],  # Dominadas, Remo, Jalón
            'Piernas': [11, 12, 13, 14],  # Sentadilla, Prensa, Peso Muerto, Extensiones
            'Hombros': [15, 16, 17],  # Press Militar, Elevaciones, Face Pulls
            'Bíceps': [9, 10],  # Curl Barra, Curl Martillo
            'Tríceps': [4, 5],  # Fondos, Press Francés
            'Abdomen': [18, 19]  # Plancha, Crunch
        }
        
        # Niveles de experiencia y sus características
        niveles_config = {
            'principiante': {'series_range': (2, 3), 'reps_range': (12, 15), 'descanso_range': (60, 90)},
            'intermedio': {'series_range': (3, 4), 'reps_range': (8, 12), 'descanso_range': (90, 120)},
            'avanzado': {'series_range': (4, 5), 'reps_range': (6, 10), 'descanso_range': (120, 180)}
        }
        
        # Objetivos y sus características
        objetivos_config = {
            'perdida_peso': {'reps_modifier': 1.2, 'descanso_modifier': 0.8},
            'hipertrofia': {'reps_modifier': 1.0, 'descanso_modifier': 1.0},
            'recomposicion': {'reps_modifier': 1.1, 'descanso_modifier': 0.9}
        }
        
        data = []
        
        for i in range(n_samples):
            # Características del usuario
            edad = np.random.randint(18, 65)
            sexo = np.random.choice(['M', 'F'])
            peso = np.random.normal(70 if sexo == 'M' else 60, 15)
            peso = max(45, min(120, peso))
            altura = np.random.normal(175 if sexo == 'M' else 165, 10)
            altura = max(150, min(200, altura))
            imc = peso / ((altura/100) ** 2)
            
            nivel = np.random.choice(['principiante', 'intermedio', 'avanzado'], 
                                   p=[0.4, 0.4, 0.2])
            objetivo = np.random.choice(['perdida_peso', 'hipertrofia', 'recomposicion'])
            
            porcentaje_grasa = np.random.normal(
                20 if sexo == 'M' else 25, 5
            )
            porcentaje_grasa = max(8, min(35, porcentaje_grasa))
            
            tiempo_entrenamiento = np.random.choice([45, 60, 75, 90])
            
            # Generar plan de entrenamiento
            dias_semana = np.random.choice([3, 4, 5], p=[0.3, 0.5, 0.2])
            
            # Seleccionar grupos musculares para cada día
            grupos_disponibles = list(ejercicios_grupos.keys())
            
            for dia in range(1, dias_semana + 1):
                # Lógica de distribución de grupos musculares
                if dias_semana == 3:  # Full body o push/pull/legs
                    if dia == 1:
                        grupos_dia = ['Pecho', 'Tríceps', 'Hombros']
                    elif dia == 2:
                        grupos_dia = ['Espalda', 'Bíceps']
                    else:
                        grupos_dia = ['Piernas', 'Abdomen']
                elif dias_semana == 4:  # Upper/Lower split
                    if dia % 2 == 1:
                        opciones_upper = [['Pecho', 'Tríceps'], ['Espalda', 'Bíceps']]
                        grupos_dia = opciones_upper[np.random.randint(0, 2)]
                    else:
                        grupos_dia = ['Piernas', 'Abdomen']
                else:  # 5 días - Bro split
                    grupos_dia = [grupos_disponibles[dia-1]]
                
                # Generar ejercicios para cada grupo
                for grupo in grupos_dia:
                    ejercicios_grupo = ejercicios_grupos[grupo]
                    num_ejercicios = min(len(ejercicios_grupo), 
                                       np.random.choice([2, 3, 4], p=[0.3, 0.5, 0.2]))
                    
                    ejercicios_seleccionados = np.random.choice(
                        ejercicios_grupo, num_ejercicios, replace=False
                    )
                    
                    for ejercicio_id in ejercicios_seleccionados:
                        # Calcular parámetros basados en nivel y objetivo
                        config_nivel = niveles_config[nivel]
                        config_objetivo = objetivos_config[objetivo]
                        
                        series = np.random.randint(*config_nivel['series_range'])
                        
                        reps_base = np.random.randint(*config_nivel['reps_range'])
                        reps = int(reps_base * config_objetivo['reps_modifier'])
                        reps = max(6, min(20, reps))
                        
                        descanso_base = np.random.randint(*config_nivel['descanso_range'])
                        descanso = descanso_base * config_objetivo['descanso_modifier']
                        descanso = max(30, min(300, descanso)) / 60  # Convertir a minutos
                        
                        # Peso sugerido (porcentaje del peso corporal)
                        if grupo in ['Pecho', 'Espalda']:
                            peso_factor = np.random.uniform(0.8, 1.2)
                        elif grupo == 'Piernas':
                            peso_factor = np.random.uniform(1.0, 1.5)
                        else:
                            peso_factor = np.random.uniform(0.3, 0.8)
                        
                        peso_sugerido = peso * peso_factor
                        
                        data.append({
                            'edad': edad,
                            'sexo': sexo,
                            'peso': peso,
                            'altura': altura,
                            'imc': imc,
                            'nivel': nivel,
                            'objetivo': objetivo,
                            'porcentaje_grasa': porcentaje_grasa,
                            'tiempo_entrenamiento': tiempo_entrenamiento,
                            'dia_semana': dia,
                            'ejercicio_id': ejercicio_id,
                            'grupo_muscular': grupo,
                            'series': series,
                            'repeticiones': reps,
                            'peso_sugerido': peso_sugerido,
                            'descanso_minutos': round(descanso, 1)
                        })
        
        return pd.DataFrame(data)
    
    def preparar_datos(self, df):
        """
        Prepara los datos para el entrenamiento
        """
        # Features de entrada
        features = ['edad', 'peso', 'altura', 'imc', 'porcentaje_grasa', 'tiempo_entrenamiento']
        
        # Codificar variables categóricas
        df['sexo_encoded'] = self.le_sexo.fit_transform(df['sexo'])
        df['nivel_encoded'] = self.le_nivel.fit_transform(df['nivel'])
        df['objetivo_encoded'] = self.le_objetivo.fit_transform(df['objetivo'])
        
        features.extend(['sexo_encoded', 'nivel_encoded', 'objetivo_encoded'])
        
        X = df[features]
        
        # Targets
        y_ejercicio = df['ejercicio_id']
        y_parametros = df[['series', 'repeticiones', 'peso_sugerido', 'descanso_minutos']]
        
        return X, y_ejercicio, y_parametros
    
    def entrenar_modelo(self, df):
        """
        Entrena los modelos Random Forest
        """
        print("🚀 Iniciando entrenamiento del modelo de planes de entrenamiento...")
        
        X, y_ejercicio, y_parametros = self.preparar_datos(df)
        
        # Dividir datos
        X_train, X_test, y_ej_train, y_ej_test, y_par_train, y_par_test = train_test_split(
            X, y_ejercicio, y_parametros, test_size=0.2, random_state=42
        )
        
        # Escalar características
        X_train_scaled = self.scaler_features.fit_transform(X_train)
        X_test_scaled = self.scaler_features.transform(X_test)
        
        # Modelo para selección de ejercicios
        print("📊 Entrenando clasificador de ejercicios...")
        self.ejercicio_classifier = RandomForestClassifier(
            n_estimators=100,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
        
        self.ejercicio_classifier.fit(X_train_scaled, y_ej_train)
        
        # Modelo para parámetros (series, reps, peso, descanso)
        print("📊 Entrenando regresor de parámetros...")
        self.parametros_regressor = MultiOutputRegressor(
            RandomForestRegressor(
                n_estimators=100,
                max_depth=12,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            )
        )
        
        self.parametros_regressor.fit(X_train_scaled, y_par_train)
        
        # Evaluación
        print("\n📈 Evaluando modelos...")
        
        # Clasificador de ejercicios
        y_ej_pred = self.ejercicio_classifier.predict(X_test_scaled)
        ejercicio_accuracy = accuracy_score(y_ej_test, y_ej_pred)
        print(f"Precisión clasificador de ejercicios: {ejercicio_accuracy:.3f}")
        
        # Regresor de parámetros
        y_par_pred = self.parametros_regressor.predict(X_test_scaled)
        parametros_mse = mean_squared_error(y_par_test, y_par_pred)
        print(f"MSE regresor de parámetros: {parametros_mse:.3f}")
        
        # Métricas por columna
        columnas = ['series', 'repeticiones', 'peso_sugerido', 'descanso_minutos']
        for i, col in enumerate(columnas):
            mse_col = mean_squared_error(y_par_test.iloc[:, i], y_par_pred[:, i])
            print(f"MSE {col}: {mse_col:.3f}")
        
        return {
            'ejercicio_accuracy': ejercicio_accuracy,
            'parametros_mse': parametros_mse,
            'n_samples': len(df)
        }
    
    def generar_plan_personalizado(self, usuario_data, dias_semana=4):
        """
        Genera un plan de entrenamiento personalizado para un usuario
        """
        # Preparar datos del usuario
        user_features = np.array([[
            usuario_data['edad'],
            usuario_data['peso'],
            usuario_data['altura'],
            usuario_data['imc'],
            usuario_data['porcentaje_grasa'],
            usuario_data['tiempo_entrenamiento'],
            self.le_sexo.transform([usuario_data['sexo']])[0],
            self.le_nivel.transform([usuario_data['nivel']])[0],
            self.le_objetivo.transform([usuario_data['objetivo']])[0]
        ]])
        
        user_features_scaled = self.scaler_features.transform(user_features)
        
        plan = {}
        
        # Distribución de grupos musculares por día
        distribuciones = {
            3: [
                ['Pecho', 'Tríceps', 'Hombros'],
                ['Espalda', 'Bíceps'],
                ['Piernas', 'Abdomen']
            ],
            4: [
                ['Pecho', 'Tríceps'],
                ['Piernas'],
                ['Espalda', 'Bíceps'],
                ['Hombros', 'Abdomen']
            ],
            5: [
                ['Pecho'],
                ['Espalda'],
                ['Piernas'],
                ['Hombros'],
                ['Bíceps', 'Tríceps', 'Abdomen']
            ]
        }
        
        grupos_por_dia = distribuciones.get(dias_semana, distribuciones[4])
        
        # Mapeo de grupos a ejercicios
        ejercicios_grupos = {
            'Pecho': [1, 2, 3],
            'Espalda': [6, 7, 8],
            'Piernas': [11, 12, 13, 14],
            'Hombros': [15, 16, 17],
            'Bíceps': [9, 10],
            'Tríceps': [4, 5],
            'Abdomen': [18, 19]
        }
        
        for dia_num, grupos in enumerate(grupos_por_dia, 1):
            ejercicios_dia = []
            
            for grupo in grupos:
                ejercicios_disponibles = ejercicios_grupos[grupo]
                
                # Seleccionar 2-3 ejercicios por grupo
                num_ejercicios = min(len(ejercicios_disponibles), 
                                   3 if len(grupos) == 1 else 2)
                
                ejercicios_seleccionados = np.random.choice(
                    ejercicios_disponibles, num_ejercicios, replace=False
                )
                
                for ejercicio_id in ejercicios_seleccionados:
                    # Predecir parámetros
                    parametros_pred = self.parametros_regressor.predict(user_features_scaled)[0]
                    
                    ejercicios_dia.append({
                        'ejercicio_id': int(ejercicio_id),
                        'series': max(2, min(5, round(parametros_pred[0]))),
                        'repeticiones': f"{max(6, min(20, round(parametros_pred[1])))}",
                        'peso_sugerido': max(5, round(parametros_pred[2], 1)),
                        'descanso_minutos': max(0.5, min(5.0, round(parametros_pred[3], 1)))
                    })
            
            plan[dia_num] = {
                'nombre_dia': ' y '.join(grupos),
                'ejercicios': ejercicios_dia
            }
        
        return plan
    
    def guardar_modelo(self, ruta_base):
        """
        Guarda el modelo entrenado
        """
        os.makedirs(ruta_base, exist_ok=True)
        
        # Guardar modelos
        joblib.dump(self.ejercicio_classifier, 
                   os.path.join(ruta_base, 'ejercicio_classifier.pkl'))
        joblib.dump(self.parametros_regressor, 
                   os.path.join(ruta_base, 'parametros_regressor.pkl'))
        
        # Guardar transformadores
        joblib.dump(self.scaler_features, 
                   os.path.join(ruta_base, 'scaler_features.pkl'))
        joblib.dump(self.le_sexo, 
                   os.path.join(ruta_base, 'le_sexo.pkl'))
        joblib.dump(self.le_nivel, 
                   os.path.join(ruta_base, 'le_nivel.pkl'))
        joblib.dump(self.le_objetivo, 
                   os.path.join(ruta_base, 'le_objetivo.pkl'))
        
        print(f"✅ Modelo guardado en: {ruta_base}")
    
    def cargar_modelo(self, ruta_base):
        """
        Carga un modelo previamente entrenado
        """
        self.ejercicio_classifier = joblib.load(
            os.path.join(ruta_base, 'ejercicio_classifier.pkl'))
        self.parametros_regressor = joblib.load(
            os.path.join(ruta_base, 'parametros_regressor.pkl'))
        
        self.scaler_features = joblib.load(
            os.path.join(ruta_base, 'scaler_features.pkl'))
        self.le_sexo = joblib.load(
            os.path.join(ruta_base, 'le_sexo.pkl'))
        self.le_nivel = joblib.load(
            os.path.join(ruta_base, 'le_nivel.pkl'))
        self.le_objetivo = joblib.load(
            os.path.join(ruta_base, 'le_objetivo.pkl'))
        
        print(f"✅ Modelo cargado desde: {ruta_base}")

def main():
    """
    Función principal para entrenar y guardar el modelo
    """
    print("🏋️‍♂️ ENTRENAMIENTO DEL MODELO DE PLANES DE ENTRENAMIENTO")
    print("=" * 60)
    
    # Crear instancia del modelo
    modelo = PlanEntrenamientoML()
    
    # Generar dataset
    print("📊 Generando dataset sintético...")
    df = modelo.generar_dataset_sintetico(n_samples=8000)
    print(f"Dataset generado: {len(df)} muestras")
    
    # Entrenar modelo
    metricas = modelo.entrenar_modelo(df)
    
    # Guardar modelo
    ruta_modelo = os.path.join(os.path.dirname(__file__), '..', 'ModelosML', 'PlanEntrenamiento')
    modelo.guardar_modelo(ruta_modelo)
    
    # Guardar métricas
    metricas_df = pd.DataFrame([metricas])
    metricas_df.to_csv(os.path.join(ruta_modelo, 'metricas_plan.csv'), index=False)
    
    # Ejemplo de uso
    print("\n Ejemplo de plan generado:")
    usuario_ejemplo = {
        'edad': 25,
        'sexo': 'M',
        'peso': 75,
        'altura': 180,
        'imc': 23.1,
        'nivel': 'intermedio',
        'objetivo': 'hipertrofia',
        'porcentaje_grasa': 15.0,
        'tiempo_entrenamiento': 60
    }
    
    plan_ejemplo = modelo.generar_plan_personalizado(usuario_ejemplo, dias_semana=4)
    
    for dia, info in plan_ejemplo.items():
        print(f"\nDía {dia}: {info['nombre_dia']}")
        for ej in info['ejercicios']:
            print(f"  - Ejercicio {ej['ejercicio_id']}: {ej['series']}x{ej['repeticiones']}, "
                  f"{ej['peso_sugerido']}kg, {ej['descanso_minutos']}min descanso")
    
    print(f"\n Entrenamiento completado!")
    print(f" Precisión ejercicios: {metricas['ejercicio_accuracy']:.3f}")
    print(f" MSE parámetros: {metricas['parametros_mse']:.3f}")

if __name__ == "__main__":
    main()

import os
import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score, RandomizedSearchCV
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error

def main():
    # --- Rutas ---
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATASET_PATH = os.path.join(BASE_DIR, 'Fit-Evolution_Dataset.csv')
    MODELOS_DIR = os.path.join(BASE_DIR, 'ModelosML/MacroNutrientes')
    os.makedirs(MODELOS_DIR, exist_ok=True)

    # --- Cargar datos ---
    print("📂 Cargando dataset...")
    df = pd.read_csv(DATASET_PATH)
    print(f"✅ Dataset original: {df.shape[0]} filas")

    # --- Definir columnas ---
    # Variables obligatorias (deben estar en el dataset y en el formulario del usuario)
    feature_cols_obligatorias = [
        'Edad',
        'Género',
        'Peso_(kg)',
        'Altura_(m)',
        'Frecuencia_entrenamiento_(días/semana)',
        'Duración_sesión_(horas)',
        'Nivel_experiencia',
        'Objetivo'
    ]

    # Variables opcionales (pueden faltar en algunos usuarios)
    feature_cols_opcionales = [
        'Porcentaje_grasa',
        'Masa_magra_(kg)'
    ]

    target_cols = ['Proteínas', 'Carbohidratos', 'Grasas']

    todas_features = feature_cols_obligatorias + feature_cols_opcionales

    # Verificar columnas
    missing_in_dataset = [col for col in todas_features if col not in df.columns]
    if missing_in_dataset:
        raise ValueError(f"Columnas faltantes en el dataset: {missing_in_dataset}")
    missing_targets = [col for col in target_cols if col not in df.columns]
    if missing_targets:
        raise ValueError(f"Columnas objetivo faltantes: {missing_targets}")

    X = df[todas_features].copy()
    y = df[target_cols].copy()

    # --- Eliminar filas donde falten variables obligatorias ---
    X = X.dropna(subset=feature_cols_obligatorias)
    y = y.loc[X.index]
    print(f"✅ Filas tras eliminar NaN en obligatorias: {X.shape[0]}")

    # --- Imputar variables opcionales con mediana ---
    for col in feature_cols_opcionales:
        if X[col].isna().any():
            mediana = X[col].median()
            X[col].fillna(mediana, inplace=True)
            print(f"  ⚠️  Imputando '{col}' con mediana: {mediana:.2f}")

    # --- Codificar categóricas ---
    print("🔄 Codificando variables categóricas...")
    le_genero = LabelEncoder()
    le_objetivo = LabelEncoder()
    le_nivel = LabelEncoder()

    X['Género'] = le_genero.fit_transform(X['Género'])
    X['Objetivo'] = le_objetivo.fit_transform(X['Objetivo'])
    X['Nivel_experiencia'] = le_nivel.fit_transform(X['Nivel_experiencia'])

    # --- Detección de outliers (IQR) ---
    print("🔍 Detectando outliers...")
    Q1 = X.quantile(0.25)
    Q3 = X.quantile(0.75)
    IQR = Q3 - Q1
    outlier_mask = ~((X < (Q1 - 3 * IQR)) | (X > (Q3 + 3 * IQR))).any(axis=1)
    X_clean = X[outlier_mask]
    y_clean = y[outlier_mask]
    outliers_removed = len(X) - len(X_clean)
    print(f"  ⚠️  Outliers removidos: {outliers_removed} ({outliers_removed/len(X)*100:.1f}%)")

    # --- Dividir datos ---
    X_train, X_test, y_train, y_test = train_test_split(
        X_clean, y_clean, test_size=0.2, random_state=42, stratify=X_clean['Objetivo']
    )

    # --- Escalar ---
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # --- Búsqueda de hiperparámetros ---
    print("🔍 Buscando mejores hiperparámetros...")
    param_distributions = {
        'estimator__n_estimators': [100, 150, 200],
        'estimator__max_depth': [10, 15, 20, None],
        'estimator__min_samples_split': [2, 4, 6],
        'estimator__min_samples_leaf': [1, 2, 3],
        'estimator__max_features': ['sqrt', 'log2']
    }
    
    rf_base = RandomForestRegressor(random_state=42, n_jobs=-1)
    model_base = MultiOutputRegressor(rf_base)
    
    random_search = RandomizedSearchCV(
        model_base,
        param_distributions,
        n_iter=20,
        cv=3,
        scoring='neg_mean_absolute_error',
        random_state=42,
        n_jobs=-1,
        verbose=1
    )
    
    random_search.fit(X_train_scaled, y_train)
    model = random_search.best_estimator_
    
    print(f"\n✅ Mejores hiperparámetros encontrados:")
    for param, value in random_search.best_params_.items():
        print(f"  {param}: {value}")

    # --- Validación cruzada ---
    print("\n🔄 Realizando validación cruzada (5-fold)...")
    cv_scores = cross_val_score(
        model, X_train_scaled, y_train,
        cv=5,
        scoring='neg_mean_absolute_error',
        n_jobs=-1
    )
    print(f"  MAE promedio (CV): {-cv_scores.mean():.2f} ± {cv_scores.std():.2f} g")

    # --- Evaluar ---
    y_pred = model.predict(X_test_scaled)
    mae = mean_absolute_error(y_test, y_pred, multioutput='raw_values')
    r2 = r2_score(y_test, y_pred, multioutput='raw_values')
    rmse = np.sqrt(mean_squared_error(y_test, y_pred, multioutput='raw_values'))

    print("\n📊 Métricas (conjunto de prueba):")
    for i, col in enumerate(target_cols):
        print(f"  {col:15} → MAE: {mae[i]:5.2f} g, RMSE: {rmse[i]:5.2f} g, R²: {r2[i]:.3f}")
    
    # --- Importancia de features ---
    print("\n🎯 Importancia de features (promedio entre targets):")
    feature_importance = np.zeros(len(todas_features))
    for estimator in model.estimators_:
        feature_importance += estimator.feature_importances_
    feature_importance /= len(model.estimators_)
    
    feature_importance_df = pd.DataFrame({
        'Feature': todas_features,
        'Importancia': feature_importance
    }).sort_values('Importancia', ascending=False)
    
    for idx, row in feature_importance_df.head(10).iterrows():
        print(f"  {row['Feature']:40} → {row['Importancia']:.4f}")
    
    # --- Visualizaciones ---
    print("\n📈 Generando visualizaciones...")
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # 1. Importancia de features
    ax1 = axes[0, 0]
    feature_importance_df.head(10).plot(x='Feature', y='Importancia', kind='barh', ax=ax1, legend=False)
    ax1.set_title('Top 10 Features Más Importantes', fontsize=12, fontweight='bold')
    ax1.set_xlabel('Importancia')
    ax1.invert_yaxis()
    
    # 2. Predicciones vs Reales (Proteínas)
    ax2 = axes[0, 1]
    ax2.scatter(y_test.iloc[:, 0], y_pred[:, 0], alpha=0.5, edgecolors='k', linewidth=0.5)
    ax2.plot([y_test.iloc[:, 0].min(), y_test.iloc[:, 0].max()],
             [y_test.iloc[:, 0].min(), y_test.iloc[:, 0].max()], 'r--', lw=2)
    ax2.set_xlabel('Proteínas Reales (g)')
    ax2.set_ylabel('Proteínas Predichas (g)')
    ax2.set_title(f'Proteínas: R² = {r2[0]:.3f}', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    
    # 3. Predicciones vs Reales (Carbohidratos)
    ax3 = axes[1, 0]
    ax3.scatter(y_test.iloc[:, 1], y_pred[:, 1], alpha=0.5, edgecolors='k', linewidth=0.5, color='orange')
    ax3.plot([y_test.iloc[:, 1].min(), y_test.iloc[:, 1].max()],
             [y_test.iloc[:, 1].min(), y_test.iloc[:, 1].max()], 'r--', lw=2)
    ax3.set_xlabel('Carbohidratos Reales (g)')
    ax3.set_ylabel('Carbohidratos Predichos (g)')
    ax3.set_title(f'Carbohidratos: R² = {r2[1]:.3f}', fontsize=12, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    
    # 4. Predicciones vs Reales (Grasas)
    ax4 = axes[1, 1]
    ax4.scatter(y_test.iloc[:, 2], y_pred[:, 2], alpha=0.5, edgecolors='k', linewidth=0.5, color='green')
    ax4.plot([y_test.iloc[:, 2].min(), y_test.iloc[:, 2].max()],
             [y_test.iloc[:, 2].min(), y_test.iloc[:, 2].max()], 'r--', lw=2)
    ax4.set_xlabel('Grasas Reales (g)')
    ax4.set_ylabel('Grasas Predichas (g)')
    ax4.set_title(f'Grasas: R² = {r2[2]:.3f}', fontsize=12, fontweight='bold')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plot_path = os.path.join(MODELOS_DIR, 'metricas_modelo.png')
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    print(f"  ✅ Gráficos guardados en: {plot_path}")
    plt.close()
    
    # --- Distribución de errores ---
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    errors = y_test.values - y_pred
    
    for i, (col, ax) in enumerate(zip(target_cols, axes)):
        ax.hist(errors[:, i], bins=30, edgecolor='black', alpha=0.7)
        ax.axvline(0, color='red', linestyle='--', linewidth=2)
        ax.set_xlabel('Error (g)')
        ax.set_ylabel('Frecuencia')
        ax.set_title(f'Distribución de Errores: {col}', fontweight='bold')
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    error_plot_path = os.path.join(MODELOS_DIR, 'distribucion_errores.png')
    plt.savefig(error_plot_path, dpi=300, bbox_inches='tight')
    print(f"  ✅ Distribución de errores guardada en: {error_plot_path}")
    plt.close()

    # --- Guardar métricas ---
    metricas_df = pd.DataFrame({
        'Target': target_cols,
        'MAE': mae,
        'RMSE': rmse,
        'R2': r2
    })
    metricas_path = os.path.join(MODELOS_DIR, 'metricas.csv')
    metricas_df.to_csv(metricas_path, index=False)
    print(f"\n� Métricas guardadas en: {metricas_path}")
    
    # Guardar importancia de features
    feature_importance_path = os.path.join(MODELOS_DIR, 'feature_importance.csv')
    feature_importance_df.to_csv(feature_importance_path, index=False)
    print(f"📊 Importancia de features guardada en: {feature_importance_path}")

    # --- Guardar ---
    print("\n�💾 Guardando modelo y utilidades...")
    joblib.dump(model, os.path.join(MODELOS_DIR, 'modelo_macros.pkl'))
    joblib.dump(le_genero, os.path.join(MODELOS_DIR, 'le_genero.pkl'))
    joblib.dump(le_objetivo, os.path.join(MODELOS_DIR, 'le_objetivo.pkl'))
    joblib.dump(le_nivel, os.path.join(MODELOS_DIR, 'le_nivel.pkl'))
    joblib.dump(scaler, os.path.join(MODELOS_DIR, 'scaler.pkl'))
    joblib.dump(todas_features, os.path.join(MODELOS_DIR, 'feature_columns.pkl'))  # ¡Importante!

    print(f"\n✅ ¡Modelo listo! Guardado en: {MODELOS_DIR}/")

if __name__ == "__main__":
    main()
from flask import Flask, render_template, request, jsonify
import joblib
import pandas as pd
import numpy as np
import os

app = Flask(__name__)

# Variables globales para los modelos
clf_model = None
scaler = None
regresores = None
label_encoders = None
df_data = None

def cargar_modelos():
    """Cargar todos los modelos y datos necesarios"""
    global clf_model, scaler, regresores, label_encoders, df_data
    
    try:
        # Cargar modelos guardados
        clf_model = joblib.load('modelo_clasificacion.pkl')
        scaler = joblib.load('scaler.pkl')
        regresores = joblib.load('regresores.pkl')
        label_encoders = joblib.load('label_encoders.pkl')
        
        # Cargar datos (asegúrate de tener el archivo Excel)
        df_data = pd.read_excel('dataset_final_merged.xlsx', sheet_name='Sheet1')
        
        print("✅ Modelos cargados exitosamente")
        return True
    except Exception as e:
        print(f"❌ Error cargando modelos: {e}")
        return False

def obtener_equipos_disponibles():
    """Obtener lista de equipos únicos disponibles"""
    if df_data is None:
        return []
    
    # Obtener equipos únicos de ambas columnas
    equipos_home = set(df_data['home_team_name'].unique())
    equipos_away = set(df_data['away_team_name'].unique())
    equipos_todos = sorted(list(equipos_home.union(equipos_away)))
    
    return equipos_todos

def predecir_partido_final_v2(home_team, away_team, season_actual):
    """
    Función de predicción adaptada de tu notebook
    """
    # Crear columnas normalizadas temporalmente
    df_data['home_team_name_lower'] = df_data['home_team_name'].astype(str).str.lower().str.strip()
    df_data['away_team_name_lower'] = df_data['away_team_name'].astype(str).str.lower().str.strip()
    home_team_norm = home_team.lower().strip()
    away_team_norm = away_team.lower().strip()

    # Buscar datos del equipo local y visitante
    home_match = df_data[df_data['home_team_name_lower'] == home_team_norm]
    away_match = df_data[df_data['away_team_name_lower'] == away_team_norm]

    if home_match.empty or away_match.empty:
        raise ValueError(f"No se encontraron datos para {home_team} o {away_team}")

    # Usar promedio de registros si hay varios
    home = home_match.mean(numeric_only=True)
    away = away_match.mean(numeric_only=True)

    # Preparar entrada para el modelo
    entrada = {
        'home_team_name': label_encoders['home_team_name'].transform([home_team])[0],
        'away_team_name': label_encoders['away_team_name'].transform([away_team])[0],
        'league_name': label_encoders['league_name'].transform([home_match.iloc[0]['league_name']])[0],
        'season': season_actual,
        'home_avg_corners': home['home_avg_corners'],
        'home_avg_yellow_cards': home['home_avg_yellow_cards'],
        'home_avg_red_cards': home['home_avg_red_cards'],
        'away_avg_corners': away['away_avg_corners'],
        'away_avg_yellow_cards': away['away_avg_yellow_cards'],
        'away_avg_red_cards': away['away_avg_red_cards'],
        'total_avg_corners': (home['home_avg_corners'] + away['away_avg_corners']) / 2,
        'total_avg_yellow_cards': (home['home_avg_yellow_cards'] + away['away_avg_yellow_cards']) / 2,
        'total_avg_red_cards': (home['home_avg_red_cards'] + away['away_avg_red_cards']) / 2
    }

    entrada_df = pd.DataFrame([entrada])
    entrada_scaled = scaler.transform(entrada_df)

    # Predicción del resultado
    resultado_pred = clf_model.predict(entrada_scaled)[0]
    probabilidades = clf_model.predict_proba(entrada_scaled)[0]
    
    # Mapear probabilidades a etiquetas
    clases = clf_model.classes_
    prob_dict = dict(zip(clases, probabilidades))

    # Si es empate, solo devolvemos eso
    if resultado_pred == "D":
        return {
            'resultado_modelo': "D",
            'detalle': "Empate detectado",
            'probabilidades': prob_dict,
            'home_goals': 0,
            'away_goals': 0,
            'yellow_cards': 0,
            'red_cards': 0,
            'corners': 0
        }

    # Predecir estadísticas con regresores
    estadisticas_crudas = {}
    for col, modelo in regresores.items():
        estadisticas_crudas[col] = modelo.predict(entrada_scaled)[0]

    # Goles con distribución Poisson
    home_g = np.random.poisson(max(0.1, estadisticas_crudas['home_goals_norm']))
    away_g = np.random.poisson(max(0.1, estadisticas_crudas['away_goals_norm']))

    # Forzar consistencia entre resultado_modelo y goles simulados
    if resultado_pred == "H":
        if home_g <= away_g:
            home_g = away_g + np.random.randint(1, 3)
    elif resultado_pred == "A":
        if away_g <= home_g:
            away_g = home_g + np.random.randint(1, 3)

    # Simulación realista con algo de aleatoriedad
    yellow_cards = max(0, int(np.random.normal(estadisticas_crudas['total_avg_yellow_cards'] / 10, 1)))
    red_cards = max(0, int(np.random.normal(estadisticas_crudas['total_avg_red_cards'] / 10, 0.5)))
    corners = max(0, int(np.random.normal(estadisticas_crudas['total_avg_corners'] / 10, 1.5)))

    return {
        'resultado_modelo': resultado_pred,
        'probabilidades': prob_dict,
        'home_goals': home_g,
        'away_goals': away_g,
        'yellow_cards': yellow_cards,
        'red_cards': red_cards,
        'corners': corners
    }

@app.route('/')
def index():
    """Página principal"""
    equipos = obtener_equipos_disponibles()
    return render_template('index.html', equipos=equipos)

@app.route('/predecir', methods=['POST'])
def predecir():
    """Endpoint para realizar predicciones"""
    try:
        data = request.get_json()
        home_team = data.get('home_team')
        away_team = data.get('away_team')
        season = data.get('season', 2025)
        
        if not home_team or not away_team:
            return jsonify({'error': 'Faltan datos del equipo'}), 400
        
        if home_team == away_team:
            return jsonify({'error': 'Los equipos deben ser diferentes'}), 400
        
        # Realizar predicción
        resultado = predecir_partido_final_v2(home_team, away_team, season)
        
        # Formatear respuesta
        response = {
            'success': True,
            'home_team': home_team,
            'away_team': away_team,
            'season': season,
            'prediccion': resultado
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/equipos')
def get_equipos():
    """Endpoint para obtener lista de equipos"""
    equipos = obtener_equipos_disponibles()
    return jsonify(equipos)

if __name__ == '__main__':
    # Cargar modelos al iniciar
    if cargar_modelos():
        print("🚀 Iniciando servidor Flask...")
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        print("❌ No se pudieron cargar los modelos. Verifica que existan los archivos necesarios.")
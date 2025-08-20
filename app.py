from flask import Flask, render_template, request, jsonify
import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor

# ===============================
# PoissonRegressor personalizado
# ===============================
class PoissonRegressor:
    def __init__(self, base_regressor=None, random_state=42):
        self.base_regressor = base_regressor or RandomForestRegressor(random_state=random_state)

    def fit(self, X, y):
        y_log = np.log(np.maximum(y, 0.1))
        self.base_regressor.fit(X, y_log)
        return self

    def predict(self, X):
        y_log_pred = self.base_regressor.predict(X)
        return np.exp(y_log_pred)

# ===============================
# Flask App
# ===============================
app = Flask(__name__)

clf_model = None
scaler = None
regresores = None
label_encoders = None
df_data = None

# ===============================
# Cargar modelos y datos
# ===============================
def cargar_modelos():
    global clf_model, scaler, regresores, label_encoders, df_data
    try:
        clf_model = joblib.load('modelo_clasificacion.pkl')
        scaler = joblib.load('scaler.pkl')
        regresores = joblib.load('regresores.pkl')
        label_encoders = joblib.load('label_encoders.pkl')
        df_data = pd.read_excel('dataset_final.xlsx', sheet_name='Sheet1')
        df_data['home_team_name_lower'] = df_data['home_team_name'].astype(str).str.lower().str.strip()
        df_data['away_team_name_lower'] = df_data['away_team_name'].astype(str).str.lower().str.strip()
        print("✅ Modelos cargados correctamente")
        return True
    except Exception as e:
        print(f"❌ Error cargando modelos: {e}")
        return False

# ===============================
# Predicción completa
# ===============================
def predecir_partido_completo(home_team, away_team, season_actual, clf_model, scaler, regresores_dict, label_encs, datos):
    home_norm = home_team.lower().strip()
    away_norm = away_team.lower().strip()

    home_match = datos[datos['home_team_name_lower'] == home_norm]
    away_match = datos[datos['away_team_name_lower'] == away_norm]

    if home_match.empty or away_match.empty:
        raise ValueError(f"No se encontraron datos para {home_team} o {away_team}")

    home_stats = home_match.mean(numeric_only=True)
    away_stats = away_match.mean(numeric_only=True)

    entrada = {
        'home_team_name': label_encs['home_team_name'].transform([home_team])[0],
        'away_team_name': label_encs['away_team_name'].transform([away_team])[0],
        'league_name': label_encs['league_name'].transform([home_match.iloc[0]['league_name']])[0],
        'season': season_actual,
        'home_avg_corners': home_stats['home_avg_corners'],
        'home_avg_yellow_cards': home_stats['home_avg_yellow_cards'],
        'home_avg_red_cards': home_stats['home_avg_red_cards'],
        'away_avg_corners': away_stats['away_avg_corners'],
        'away_avg_yellow_cards': away_stats['away_avg_yellow_cards'],
        'away_avg_red_cards': away_stats['away_avg_red_cards'],
        'total_avg_corners': (home_stats['home_avg_corners'] + away_stats['away_avg_corners']) / 2,
        'total_avg_yellow_cards': (home_stats['home_avg_yellow_cards'] + away_stats['away_avg_yellow_cards']) / 2,
        'total_avg_red_cards': (home_stats['home_avg_red_cards'] + away_stats['away_avg_red_cards']) / 2
    }

    entrada_df = pd.DataFrame([entrada])
    entrada_scaled = scaler.transform(entrada_df)

    # Clasificación H/D/A
    resultado_num = clf_model.predict(entrada_scaled)[0]
    resultado_pred = label_encs['match_result'].inverse_transform([resultado_num])[0]
    probabilidades_arr = clf_model.predict_proba(entrada_scaled)[0]
    confianza = probabilidades_arr.max()

    # Predicción de estadísticas
    predicciones_raw = {col: float(modelo.predict(entrada_scaled)[0]) for col, modelo in regresores_dict.items()}

    home_goals_exact = max(0, predicciones_raw.get('home_goals_norm', 0) * 16)
    away_goals_exact = max(0, predicciones_raw.get('away_goals_norm', 0) * 16)
    corners_exact = max(0, predicciones_raw.get('total_avg_corners', 0))
    yellow_exact = max(0, predicciones_raw.get('total_avg_yellow_cards', 0))
    red_exact = max(0, predicciones_raw.get('total_avg_red_cards', 0))

    home_goals = max(0, round(home_goals_exact / 10))
    away_goals = max(0, round(away_goals_exact / 10))
    corners = max(0, round(corners_exact / 10))
    yellow_cards = max(0, round(yellow_exact / 10))
    red_cards = max(0, round(red_exact / 10))

    # Ajuste según resultado
    if resultado_pred == "H" and home_goals <= away_goals:
        home_goals = away_goals + 1
    elif resultado_pred == "A" and away_goals <= home_goals:
        away_goals = home_goals + 1

    elif resultado_pred == "D":
    # Si es empate
        avg_goals = round((home_goals + away_goals) / 2)
        home_goals = away_goals = max(0, avg_goals)    

    return {
        'resultado_modelo': resultado_pred,
        'home_goals': home_goals,
        'away_goals': away_goals,
        'yellow_cards': yellow_cards,
        'red_cards': red_cards,
        'corners': corners,
        'probabilidades': {
            'H': float(probabilidades_arr[2]),
            'D': float(probabilidades_arr[1]),
            'A': float(probabilidades_arr[0])
        },
        'confidence': float(confianza),
        'expected': {
            'home_goals': home_goals_exact / 10,
            'away_goals': away_goals_exact / 10,
            'yellow_cards': yellow_exact / 10,
            'red_cards': red_exact / 10,
            'corners': corners_exact / 10
        }
    }

# ===============================
# Rutas Flask
# ===============================
@app.route('/')
def index():
    equipos = sorted(list(set(df_data['home_team_name'].unique()).union(set(df_data['away_team_name'].unique()))))
    return render_template('index.html', equipos=equipos)

@app.route('/equipos')
def get_equipos():
    equipos = sorted(list(set(df_data['home_team_name'].unique()).union(set(df_data['away_team_name'].unique()))))
    return jsonify({'success': True, 'equipos': equipos, 'total': len(equipos)})

@app.route('/predecir', methods=['POST'])
def predecir_ruta():
    data = request.get_json()
    home_team = data.get('home_team')
    away_team = data.get('away_team')
    season = data.get('season', 2025)

    if not home_team or not away_team:
        return jsonify({'error': 'Faltan datos del equipo'}), 400
    if home_team == away_team:
        return jsonify({'error': 'Los equipos deben ser diferentes'}), 400

    try:
        pred = predecir_partido_completo(home_team, away_team, season, clf_model, scaler, regresores, label_encoders, df_data)
        return jsonify({'success': True, 'home_team': home_team, 'away_team': away_team, 'prediccion': pred})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/test')
def test_modelo():
    equipos = sorted(list(set(df_data['home_team_name'].unique()).union(set(df_data['away_team_name'].unique()))))
    if len(equipos) < 2:
        return jsonify({'error': 'No hay suficientes equipos'}), 500
    resultado_test = predecir_partido_completo(equipos[0], equipos[1], 2025, clf_model, scaler, regresores, label_encoders, df_data)
    return jsonify({'success': True, 'test_prediction': resultado_test, 'equipos_disponibles': len(equipos)})

# ===============================
# Main
# ===============================
if __name__ == '__main__':
    if cargar_modelos():
        print("🚀 Servidor Flask iniciado en http://0.0.0.0:5000")
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        print("❌ No se pudieron cargar los modelos")

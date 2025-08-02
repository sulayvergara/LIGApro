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
        print(f"📊 Datos cargados: {len(df_data)} registros")
        print(f"🎯 Clases del modelo: {label_encoders['match_result'].classes_}")
        return True
    except Exception as e:
        print(f"❌ Error cargando modelos: {e}")
        return False

def obtener_equipos_disponibles():
    """Obtener lista de equipos únicos disponibles"""
    if df_data is None:
        return []
    
    try:
        # Los datos en el DataFrame están encoded (números), necesitamos decodificar
        home_teams_encoded = df_data['home_team_name'].unique()
        away_teams_encoded = df_data['away_team_name'].unique()
        
        # Decodificar a nombres originales
        home_teams_decoded = label_encoders['home_team_name'].inverse_transform(home_teams_encoded)
        away_teams_decoded = label_encoders['away_team_name'].inverse_transform(away_teams_encoded)
        
        # Combinar y eliminar duplicados
        equipos_originales = set(home_teams_decoded).union(set(away_teams_decoded))
        
        print(f"📋 Equipos decodificados: {len(equipos_originales)} únicos")
        return sorted(list(equipos_originales))
        
    except Exception as e:
        print(f"❌ Error decodificando equipos: {e}")
        # Como fallback, devolver lista de equipos conocidos del encoder
        try:
            equipos_fallback = list(label_encoders['home_team_name'].classes_)
            print(f"🔄 Usando equipos del encoder: {len(equipos_fallback)}")
            return sorted(equipos_fallback)
        except:
            return []

def predecir_partido_final_v3(home_team, away_team, season_actual):

    print(f"Buscando datos para: {home_team} vs {away_team}")
    
    try:
        # Primero verificar que los equipos existan en el encoder
        if home_team not in label_encoders['home_team_name'].classes_:
            equipos_disponibles = list(label_encoders['home_team_name'].classes_)
            raise ValueError(f"Equipo '{home_team}' no encontrado. Equipos disponibles: {equipos_disponibles[:10]}...")
        
        if away_team not in label_encoders['away_team_name'].classes_:
            equipos_disponibles = list(label_encoders['away_team_name'].classes_)
            raise ValueError(f"Equipo '{away_team}' no encontrado. Equipos disponibles: {equipos_disponibles[:10]}...")
        
        # Obtener códigos encoded de los equipos
        home_team_encoded = label_encoders['home_team_name'].transform([home_team])[0]
        away_team_encoded = label_encoders['away_team_name'].transform([away_team])[0]
        
        # print(f"🔢 Códigos: {home_team}={home_team_encoded}, {away_team}={away_team_encoded}")
        
        # Buscar datos en el DataFrame usando los códigos encoded
        home_match = df_data[df_data['home_team_name'] == home_team_encoded]
        away_match = df_data[df_data['away_team_name'] == away_team_encoded]
        
        # print(f"📊 Registros encontrados: Home={len(home_match)}, Away={len(away_match)}")
        
        if home_match.empty or away_match.empty:
            # Buscar como visitante/local respectivamente
            home_match_alt = df_data[df_data['away_team_name'] == home_team_encoded]
            away_match_alt = df_data[df_data['home_team_name'] == away_team_encoded]
            
            if home_match.empty and not home_match_alt.empty:
                # Usar datos como visitante pero invertir las estadísticas
                home_stats = {
                    'home_avg_corners': home_match_alt['away_avg_corners'].mean(),
                    'home_avg_yellow_cards': home_match_alt['away_avg_yellow_cards'].mean(),
                    'home_avg_red_cards': home_match_alt['away_avg_red_cards'].mean(),
                }
            else:
                home_stats = home_match.mean(numeric_only=True)
                
            if away_match.empty and not away_match_alt.empty:
                # Usar datos como local pero invertir las estadísticas  
                away_stats = {
                    'away_avg_corners': away_match_alt['home_avg_corners'].mean(),
                    'away_avg_yellow_cards': away_match_alt['home_avg_yellow_cards'].mean(),
                    'away_avg_red_cards': away_match_alt['home_avg_red_cards'].mean(),
                }
            else:
                away_stats = away_match.mean(numeric_only=True)
        else:
            # Usar promedio de registros si hay varios
            home_stats = home_match.mean(numeric_only=True)
            away_stats = away_match.mean(numeric_only=True)

        # CORRECCIÓN 2: Preparar entrada para el modelo usando los features correctos
        features_modelo = [
            'home_team_name', 'away_team_name', 'league_name', 'season',
            'home_avg_corners', 'home_avg_yellow_cards', 'home_avg_red_cards',
            'away_avg_corners', 'away_avg_yellow_cards', 'away_avg_red_cards',
            'total_avg_corners', 'total_avg_yellow_cards', 'total_avg_red_cards'
        ]

        # Obtener liga del primer registro encontrado
        if not home_match.empty:
            league_encoded = home_match.iloc[0]['league_name']
        elif not away_match.empty:
            league_encoded = away_match.iloc[0]['league_name']
        else:
            league_encoded = 4  # Valor por defecto (puede ser LigaPro)

        # Preparar entrada para el modelo
        entrada = {
            'home_team_name': home_team_encoded,
            'away_team_name': away_team_encoded,
            'league_name': league_encoded,
            'season': season_actual,
            'home_avg_corners': home_stats.get('home_avg_corners', 50.0),
            'home_avg_yellow_cards': home_stats.get('home_avg_yellow_cards', 25.0),
            'home_avg_red_cards': home_stats.get('home_avg_red_cards', 2.0),
            'away_avg_corners': away_stats.get('away_avg_corners', 40.0),
            'away_avg_yellow_cards': away_stats.get('away_avg_yellow_cards', 30.0),
            'away_avg_red_cards': away_stats.get('away_avg_red_cards', 2.5),
            'total_avg_corners': (home_stats.get('home_avg_corners', 50.0) + away_stats.get('away_avg_corners', 40.0)),
            'total_avg_yellow_cards': (home_stats.get('home_avg_yellow_cards', 25.0) + away_stats.get('away_avg_yellow_cards', 30.0)),
            'total_avg_red_cards': (home_stats.get('home_avg_red_cards', 2.0) + away_stats.get('away_avg_red_cards', 2.5))
        }
        
        print(f"📊 Entrada preparada: {entrada}")

    except Exception as e:
        print(f"❌ Error preparando datos: {e}")
        return {'error': f'Error preparando datos: {str(e)}'}

    try:
        # Crear DataFrame con el orden correcto de features
        entrada_df = pd.DataFrame([entrada])[features_modelo]
        entrada_scaled = scaler.transform(entrada_df)

        #Predecir y convertir correctamente
        resultado_pred_num = clf_model.predict(entrada_scaled)[0]  # Número (0, 1, 2)
        resultado_pred = label_encoders['match_result'].inverse_transform([resultado_pred_num])[0]  # String (A, D, H)
        
        #Obtener probabilidades
        probabilidades = clf_model.predict_proba(entrada_scaled)[0]
        clases = clf_model.classes_
        
        #Mapear probabilidades correctamente
        prob_dict = {}
        for i, clase_num in enumerate(clases):
            clase_str = label_encoders['match_result'].inverse_transform([clase_num])[0]
            prob_dict[clase_str] = float(probabilidades[i])

        print(f"🔧 Debug: Predicción numérica: {resultado_pred_num}, Resultado: {resultado_pred}")
        print(f"📊 Probabilidades: {prob_dict}")

    except Exception as e:
        print(f"❌ Error en predicción: {e}")
        return {'error': f'Error en predicción: {str(e)}'}

    # Si es empate, devolver resultado simple
    if resultado_pred == "D":
        return {
            'resultado_modelo': "D",
            'detalle': "Empate detectado. No se generan goles ni estadísticas.",
            'probabilidades': prob_dict,
            'home_goals': 0,
            'away_goals': 0,
            'yellow_cards': 0,
            'red_cards': 0,
            'corners': 0
        }

    try:
        #Predecir estadísticas con regresores
        estadisticas_crudas = {}
        targets = ['home_goals_norm', 'away_goals_norm', 'total_avg_corners', 'total_avg_yellow_cards', 'total_avg_red_cards']
        
        for target in targets:
            if target in regresores:
                estadisticas_crudas[target] = float(regresores[target].predict(entrada_scaled)[0])

        #Goles con distribución Poisson
        home_g = max(0, int(np.random.poisson(max(0.1, estadisticas_crudas.get('home_goals_norm', 1.5)))))
        away_g = max(0, int(np.random.poisson(max(0.1, estadisticas_crudas.get('away_goals_norm', 1.2)))))

        if resultado_pred == "H":
            if home_g <= away_g:
                home_g = away_g + np.random.randint(1, 3)
        elif resultado_pred == "A":
            if away_g <= home_g:
                away_g = home_g + np.random.randint(1, 3)

        #Simulación de estadísticas
        yellow_cards = max(0, int(np.random.normal(
            estadisticas_crudas.get('total_avg_yellow_cards', 50) / 10, 1
        )))
        red_cards = max(0, int(np.random.normal(
            estadisticas_crudas.get('total_avg_red_cards', 3) / 10, 0.5
        )))
        corners = max(0, int(np.random.normal(
            estadisticas_crudas.get('total_avg_corners', 95) / 10, 1.5
        )))

        return {
            'resultado_modelo': resultado_pred,
            'probabilidades': prob_dict,
            'home_goals': home_g,
            'away_goals': away_g,
            'yellow_cards': yellow_cards,
            'red_cards': red_cards,
            'corners': corners,
            'estadisticas_raw': estadisticas_crudas 
        }
        
    except Exception as e:
        print(f"❌ Error generando estadísticas: {e}")
        return {'error': f'Error generando estadísticas: {str(e)}'}

@app.route('/')
def index():
    equipos = obtener_equipos_disponibles()
    print(f"📋 Equipos disponibles: {len(equipos)}")
    return render_template('index.html', equipos=equipos)

@app.route('/predecir', methods=['POST'])
def predecir():
    try:
        data = request.get_json()
        home_team = data.get('home_team')
        away_team = data.get('away_team')
        season = data.get('season', 2024) 
        
        if not home_team or not away_team:
            return jsonify({'error': 'Faltan datos del equipo'}), 400
        
        if home_team == away_team:
            return jsonify({'error': 'Los equipos deben ser diferentes'}), 400
        
        print(f"🎯 Prediciendo: {home_team} vs {away_team} (Temporada {season})")
        
        resultado = predecir_partido_final_v3(home_team, away_team, season)
        
        if 'error' in resultado:
            print(f"❌ Error en modelo: {resultado['error']}")
            return jsonify({'error': resultado['error']}), 400
        
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
        print(f"❌ Error en predicción: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/equipos')
def get_equipos():
    """Endpoint para obtener lista de equipos"""
    try:
        equipos = obtener_equipos_disponibles()
        return jsonify({
            'success': True,
            'equipos': equipos,
            'total': len(equipos)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/test')
def test_modelo():
    """Endpoint de prueba para verificar que los modelos funcionen"""
    try:
        if clf_model is None:
            return jsonify({'error': 'Modelos no cargados'}), 500
        
        # Obtener algunos equipos de ejemplo
        equipos = obtener_equipos_disponibles()
        if len(equipos) < 2:
            return jsonify({'error': 'No hay suficientes equipos'}), 500
        
        # Hacer una predicción de prueba
        home_test = equipos[0]
        away_test = equipos[1] if equipos[1] != equipos[0] else equipos[2]
        
        resultado_test = predecir_partido_final_v3(home_test, away_test, 2025)
        
        return jsonify({
            'success': True,
            'test_prediction': {
                'home_team': home_test,
                'away_team': away_test,
                'resultado': resultado_test
            },
            'equipos_disponibles': len(equipos),
            'modelo_info': {
                'features': len(scaler.feature_names_in_) if hasattr(scaler, 'feature_names_in_') else 'N/A',
                'classes': label_encoders['match_result'].classes_.tolist()
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Error en test: {str(e)}'}), 500

if __name__ == '__main__':
    # Cargar modelos al iniciar
    if cargar_modelos():
        print("🚀 Iniciando servidor Flask...")
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        print("❌ No se pudieron cargar los modelos. Verifica que existan los archivos necesarios:")
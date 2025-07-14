from flask import Flask, render_template, request, jsonify
import joblib

app = Flask(__name__)

# Cargar el modelo y encoders
modelo = joblib.load("modelo_entrenado.pkl")
le_home = joblib.load("le_home.pkl")
le_away = joblib.load("le_away.pkl")
le_winner = joblib.load("le_winner.pkl")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/predecir", methods=["POST"])
def predecir():
    data = request.get_json()
    equipo1 = data.get("equipo1")
    equipo2 = data.get("equipo2")

    try:
        entrada = [[
            le_home.transform([equipo1])[0],
            le_away.transform([equipo2])[0],
            2025  # Temporada fija para predicción
        ]]
        pred = modelo.predict(entrada)[0]
        resultado = le_winner.inverse_transform([pred])[0].upper()

        if resultado == 'HOME':
            ganador = equipo1
        elif resultado == 'AWAY':
            ganador = equipo2
        else:
            ganador = 'Empate'

        return jsonify({"resultado": ganador})
        #return jsonify({"resultado": resultado.upper()})
    except Exception as e:
        return jsonify({"error": "Error al predecir. Verifica los nombres de los equipos."}), 400

if __name__ == "__main__":
    app.run(debug=True)

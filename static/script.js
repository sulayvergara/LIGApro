// Función para cambiar imagen del equipo
function cambiarImagen(equipoSelect, imgElement) {
  const equipoSeleccionado = equipoSelect.value;
  
  if (equipoSeleccionado && equipoSeleccionado !== "Selecciona equipo 1" && equipoSeleccionado !== "Selecciona equipo 2") {
    // Crear nombre de archivo basado en el nombre del equipo
    // Convertir a minúsculas, reemplazar espacios y caracteres especiales
    const nombreArchivo = equipoSeleccionado
      .toLowerCase()
      .replace(/\s+/g, '_')           // Espacios por guiones bajos
      .replace(/[áàäâ]/g, 'a')        // Reemplazar acentos
      .replace(/[éèëê]/g, 'e')
      .replace(/[íìïî]/g, 'i')
      .replace(/[óòöô]/g, 'o')
      .replace(/[úùüû]/g, 'u')
      .replace(/ñ/g, 'n')
      .replace(/[^a-z0-9_]/g, '');    // Eliminar caracteres especiales
    
    const rutaImagen = `/static/assets/${nombreArchivo}.png`;
    
    // Cambiar la imagen
    imgElement.src = rutaImagen;
    imgElement.alt = equipoSeleccionado;
    
    // Manejar error si la imagen no existe
    imgElement.onerror = function() {
      this.src = '/static/assets/placeholder.png';
      this.alt = 'Imagen no disponible';
    };
  } else {
    // Volver a imagen placeholder si no hay selección
    imgElement.src = '/static/assets/placeholder.png';
    imgElement.alt = 'Selecciona un equipo';
  }
}

// Event listeners para los selectores de equipos
document.addEventListener('DOMContentLoaded', function() {
  const equipo1Select = document.getElementById('equipo1');
  const equipo2Select = document.getElementById('equipo2');
  const img1 = document.getElementById('img1');
  const img2 = document.getElementById('img2');
  
  // Agregar event listeners para cambio de selección
  equipo1Select.addEventListener('change', function() {
    cambiarImagen(this, img1);
  });
  
  equipo2Select.addEventListener('change', function() {
    cambiarImagen(this, img2);
  });
});

// Función original de predicción
document.getElementById('predecirBtn').addEventListener('click', async function () {
  const homeTeam = document.getElementById('equipo1').value;
  const awayTeam = document.getElementById('equipo2').value;
  const season = 2024;

  if (!homeTeam || !awayTeam) {
    showError('Por favor selecciona ambos equipos');
    return;
  }

  if (homeTeam === awayTeam) {
    showError('Los equipos deben ser diferentes');
    return;
  }

  showLoading(true);
  hideError();
  hideResults();

  try {
    const response = await fetch('/predecir', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ home_team: homeTeam, away_team: awayTeam, season })
    });

    const data = await response.json();

    if (data.success) {
      displayResults(data);
    } else {
      showError(data.error || 'Error en la predicción');
    }
  } catch (error) {
    showError('Error de conexión: ' + error.message);
  } finally {
    showLoading(false);
  }
});

function showLoading(show) {
  document.getElementById('loading').style.display = show ? 'block' : 'none';
  document.getElementById('predecirBtn').disabled = show;
}

function showError(message) {
  const errorDiv = document.getElementById('errorMessage');
  errorDiv.textContent = message;
  errorDiv.style.display = 'block';
}

function hideError() {
  document.getElementById('errorMessage').style.display = 'none';
}

function hideResults() {
  document.getElementById('resultSection').style.display = 'none';
}

function displayResults(data) {
  const pred = data.prediccion;
  const homeTeam = data.home_team;
  const awayTeam = data.away_team;

  let resultText = '';
  if (pred.resultado_modelo === 'H') {
    resultText = `Gana ${homeTeam}`;
  } else if (pred.resultado_modelo === 'A') {
    resultText = `Gana ${awayTeam}`;
  } else {
    resultText = '🤝 Empate';
  }

  document.getElementById('matchResult').textContent = resultText;
  document.getElementById('scoreDisplay').textContent = `${homeTeam} ${pred.home_goals} - ${pred.away_goals} ${awayTeam}`;
  document.getElementById('yellowCards').textContent = pred.yellow_cards;
  document.getElementById('redCards').textContent = pred.red_cards;
  document.getElementById('corners').textContent = pred.corners;

  const probDiv = document.getElementById('probabilities');
  probDiv.innerHTML = '';
  const labels = { 'H': 'Local', 'D': 'Empate', 'A': 'Visitante' };

  Object.entries(pred.probabilidades).forEach(([key, prob]) => {
    const card = document.createElement('div');
    card.className = 'prob-card';
    card.innerHTML = `
      <div style="font-weight: bold; margin-bottom: 5px;">${labels[key]}</div>
      <div style="font-size: 1.2rem;">${(prob * 100).toFixed(1)}%</div>
    `;
    probDiv.appendChild(card);
  });

  document.getElementById('resultSection').style.display = 'block';
  document.getElementById('resultSection').scrollIntoView({ behavior: 'smooth' });
}
// Función para cambiar imagen del equipo
function cambiarImagen(equipoSelect, imgElement) {
  const equipoSeleccionado = equipoSelect.value;
  
  if (equipoSeleccionado && equipoSeleccionado !== "LOCAL" && equipoSeleccionado !== "VISITANTE") {
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
    
    imgElement.onerror = function() {
      this.src = '/static/assets/placeholder.png';
      this.alt = 'Imagen no disponible';
    };
  } else {
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


  equipo1Select.addEventListener('change', function() {
    cambiarImagen(this, img1);
  });
  
  equipo2Select.addEventListener('change', function() {
    cambiarImagen(this, img2);
  });

  cargarEquipos();
});

async function cargarEquipos() {
  try {
    const response = await fetch('/equipos');
    const data = await response.json();
    
    if (data.success && data.equipos) {
      const equipo1Select = document.getElementById('equipo1');
      const equipo2Select = document.getElementById('equipo2');
      
      equipo1Select.innerHTML = '<option disabled selected>Selecciona equipo Local</option>';
      equipo2Select.innerHTML = '<option disabled selected>Selecciona equipo Visitante</option>';
      
      // Agregar equipos
      data.equipos.forEach(equipo => {
        const option1 = document.createElement('option');
        option1.value = equipo;
        option1.textContent = equipo;
        equipo1Select.appendChild(option1);
        
        const option2 = document.createElement('option');
        option2.value = equipo;
        option2.textContent = equipo;
        equipo2Select.appendChild(option2);
      });
      
      console.log(`✅ Cargados ${data.equipos.length} equipos`);
    }
  } catch (error) {
    console.error('Error cargando equipos:', error);
    showError('Error cargando lista de equipos');
  }
}

document.getElementById('predecirBtn').addEventListener('click', async function () {
  const homeTeam = document.getElementById('equipo1').value;
  const awayTeam = document.getElementById('equipo2').value;
  const versus = document.getElementById('idversus');
  const season = 2024;

  img1.style.width = "200px";
  img1.style.height = "200px";

  img2.style.width = "200px";
  img2.style.height = "200px";

  equipo1.style.width = "200px";
  equipo2.style.width = "200px";
  versus.style.fontSize = "1.6rem";
  predecirBtn.style.fontSize = "1.1rem";

  if (!homeTeam || !awayTeam || homeTeam === "Selecciona equipo 1" || awayTeam === "Selecciona equipo 2") {
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
    console.log(`🎯 Prediciendo: ${homeTeam} vs ${awayTeam}`);
    
    const response = await fetch('/predecir', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        home_team: homeTeam, 
        away_team: awayTeam, 
        season: season 
      })
    });

    const data = await response.json();
    console.log('📊 Respuesta del servidor:', data);

    console.log('📌 Home Team recibido:', data.home_team);
    console.log('📌 Away Team recibido:', data.away_team);

    if (data.success) {
      displayResults(data);
    } else {
      showError(data.error || 'Error en la predicción');
    }
  } catch (error) {
    console.error('Error:', error);
    showError('Error de conexión: ' + error.message);
  } finally {
    showLoading(false);
  }
});

function showLoading(show) {
  const loadingDiv = document.getElementById('loading');
  const btnPredicir = document.getElementById('predecirBtn');
  
  
  if (loadingDiv) loadingDiv.style.display = show ? 'block' : 'none';
  if (btnPredicir) btnPredicir.disabled = show;
}

function showError(message) {
  const errorDiv = document.getElementById('errorMessage');
  if (errorDiv) {
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    
    // Auto-ocultar después de 5 segundos
    setTimeout(() => {
      hideError();
    }, 5000);
  }
  console.error('❌ Error:', message);
}

function hideError() {
  const errorDiv = document.getElementById('errorMessage');
  if (errorDiv) {
    errorDiv.style.display = 'none';
  }
}

function hideResults() {
  const resultDiv = document.getElementById('resultSection');
  if (resultDiv) {
    resultDiv.style.display = 'none';
  }
  const matchResultDiv = document.getElementById('matchResult');
  if (matchResultDiv) {
    matchResultDiv.style.display = 'none';
  }
  
  // Ocultar también la sección de estadísticas del modelo
  const modelStatsDiv = document.getElementById('modelStatsSection');
  if (modelStatsDiv) {
    modelStatsDiv.style.display = 'none';
  }
}

function displayResults(data) {
  const pred = data.prediccion;
  const homeTeam = data.home_team;
  const awayTeam = data.away_team;

  console.log('🎯 Mostrando resultados:', pred);

  let resultText = '';
  let resultClass = '';
  
    if (pred.resultado_modelo === 'H') {
    resultText = `Gana ${homeTeam}`;
    resultClass = 'win-home';
  } else if (pred.resultado_modelo === 'A') {
    resultText = `Gana ${awayTeam}`;
    resultClass = 'win-away';
  } else {
    resultText = 'Empate';
    resultClass = 'draw';
  }

  // Actualizar elementos
  // const matchResultEl = document.getElementById('matchResult');
  const scoreDisplayEl = document.getElementById('scoreDisplay');
  
  // if (matchResultEl) {
  //   matchResultEl.textContent = resultText;
  //   matchResultEl.className = `match-result ${resultClass}`;
  // }
  
  if (scoreDisplayEl) {
  if (pred.expected) {
    scoreDisplayEl.textContent = `${homeTeam} ${pred.expected.home_goals.toFixed(0)} - ${pred.expected.away_goals.toFixed(0)} ${awayTeam}`;
  } else {
    scoreDisplayEl.textContent = `${homeTeam} - ${awayTeam}`;
  }
}
  
  // Actualizar estadísticas
  const stats = [
    { id: 'yellowCards', value: pred.yellow_cards },
    { id: 'redCards', value: pred.red_cards },
    { id: 'corners', value: pred.corners }
  ];
  
  stats.forEach(stat => {
    const element = document.getElementById(stat.id);
    if (element) {
      element.textContent = stat.value || '0';
    }
  });

  // Mostrar probabilidades
// Mostrar probabilidades EN EL ORDEN CORRECTO (H, D, A)
const probDiv = document.getElementById('probabilities');
if (probDiv && pred.probabilidades) {
  probDiv.innerHTML = '';
  const labels = { 'H': 'Local', 'D': 'Empate', 'A': 'Visitante' };
  const colors = { 'H': '#4CAF50', 'D': '#FF9800', 'A': '#2196F3' };
  
  // ✅ ORDEN FIJO: H, D, A (en lugar de usar Object.entries)
  const ordenCorrecto = ['H', 'D', 'A'];
  
  ordenCorrecto.forEach(key => {
    if (pred.probabilidades[key] !== undefined) {
      const prob = pred.probabilidades[key];
      const card = document.createElement('div');
      card.className = 'prob-card';
      card.style.borderLeft = `4px solid ${colors[key]}`;
      
      card.innerHTML = `
        <div style="font-weight: bold; margin-bottom: 5px; color: ${colors[key]};">
          ${labels[key] || key}
        </div>
        <div style="font-size: 1.2rem; font-weight: bold;">
          ${(prob * 100).toFixed(1)}%
        </div>
        <div class="prob-bar">
          <div class="prob-fill" style="width: ${prob * 100}%; background-color: ${colors[key]};"></div>
        </div>
      `;
      probDiv.appendChild(card);
    }
  });
}

  //  MOSTRAR ESTADÍSTICAS DEL MODELO (NUEVA FUNCIONALIDAD)
  if (pred.expected) {
    // Actualizar valores esperados
    const expectedGoalsEl = document.getElementById('expectedGoals');
    const expectedYellowEl = document.getElementById('expectedYellow');
    const expectedRedEl = document.getElementById('expectedRed');
    const expectedCornersEl = document.getElementById('expectedCorners');
    const modelConfidenceEl = document.getElementById('modelConfidence');
    const confidenceCardEl = document.getElementById('confidenceCard');
    
    if (expectedGoalsEl) {
      expectedGoalsEl.textContent = `${pred.expected.home_goals.toFixed(2)} - ${pred.expected.away_goals.toFixed(2)}`;
    }
    
    if (expectedYellowEl) {
      expectedYellowEl.textContent = pred.expected.yellow_cards.toFixed(2);
    }
    
    if (expectedRedEl) {
      expectedRedEl.textContent = pred.expected.red_cards.toFixed(2);
    }
    
    if (expectedCornersEl) {
      expectedCornersEl.textContent = pred.expected.corners.toFixed(2);
    }
    
    // Mostrar confianza si está disponible
    if (pred.confidence && modelConfidenceEl && confidenceCardEl) {
      modelConfidenceEl.textContent = `${(pred.confidence * 100).toFixed(1)}%`;
      confidenceCardEl.style.display = 'block';
    }
    
    // Mostrar la sección de estadísticas del modelo
    const modelStatsSection = document.getElementById('modelStatsSection');
    if (modelStatsSection) {
      modelStatsSection.style.display = 'block';
      console.log('✅ Mostrando estadísticas del modelo');
    }
  } else {
    // Ocultar si no hay datos esperados
    const modelStatsSection = document.getElementById('modelStatsSection');
    if (modelStatsSection) {
      modelStatsSection.style.display = 'none';
      console.log('⚠️ No hay estadísticas del modelo disponibles');
    }
  }
  // Mostrar seccion de resultados
  const matchResultDiv = document.getElementById('matchResult');
  if (matchResultDiv) {
    matchResultDiv.style.display = 'flex';
  }
 
  const resultSection = document.getElementById('resultSection');
  if (resultSection) {
    resultSection.style.display = 'block';
    resultSection.scrollIntoView({ behavior: 'smooth' });
  }
}

// CORRECCIÓN: Función de test para verificar conexión
async function testConexion() {
  try {
    const response = await fetch('/test');
    const data = await response.json();
    console.log('🔧 Test de conexión:', data);
    return data.success;
  } catch (error) {
    console.error('❌ Error en test de conexión:', error);
    return false;
  }
}

// Ejecutar test al cargar la página
document.addEventListener('DOMContentLoaded', function() {
  setTimeout(() => {
    testConexion();
  }, 1000);
});
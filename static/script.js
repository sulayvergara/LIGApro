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

const equipos = {
  "Aucas": "aucas",
  "Barcelona SC": "barcelona",
  "CD Olmedo": "N",
  "Clan Juvenil": "N",
  "Cuniburo": "N",
  "Delfín SC": "delfin",
  "Deportivo Cuenca": "cuenca",
  "Deportivo Quevedo": "N",
  "Deportivo Quito": "N",
  "El Nacional": "nacional",
  "Emelec": "emelec",
  "Fuerza Amarilla": "N",
  "Gualaceo SC": "N",
  "Guayaquil City FC": "N",
  "Imbabura": "N",
  "Independiente del Valle": "idv",
  "LDU de Quito": "ldu",
  "LDU Loja": "N",  
  "LDU Portoviejo": "N",
  "Libertad": "libertad",
  "Macará": "macara",
  "Manta FC": "N",
  "Mushuc Runa SC": "mushuc",
  "Orense SC": "orense",
  "Técnico Universitario": "tecnico",
  "Universidad Catolica": "N",
  "9 de Octubre": "N",
  "Cumbayá": "cumbaya"
};



const select1 = document.getElementById("equipo1");
const select2 = document.getElementById("equipo2");
const img1 = document.getElementById("img1");
const img2 = document.getElementById("img2");
const resultado = document.getElementById("resultado");

// Cargar equipos en los selects
Object.keys(equipos).forEach(nombre => {
  const option1 = document.createElement("option");
  option1.textContent = nombre;
  option1.value = nombre;
  const option2 = option1.cloneNode(true);
  select1.appendChild(option1);
  select2.appendChild(option2);
});

// Imagen equipo 1
select1.addEventListener("change", () => {
  if (select1.value === select2.value) {
    alert("No puedes seleccionar el mismo equipo.");
    select1.selectedIndex = 0;
    img1.src = "/static/assets/placeholder.png";
    return;
  }
  img1.src = `/static/assets/${equipos[select1.value]}.png`;
});

// Imagen equipo 2
select2.addEventListener("change", () => {
  if (select2.value === select1.value) {
    alert("No puedes seleccionar el mismo equipo.");
    select2.selectedIndex = 0;
    img2.src = "/static/assets/placeholder.png";
    return;
  }
  img2.src = `/static/assets/${equipos[select2.value]}.png`;
});

// Predicción real (con modelo en Flask)
document.getElementById("predecirBtn").addEventListener("click", () => {
  const eq1 = select1.value;
  const eq2 = select2.value;

  if (!eq1 || !eq2 || eq1 === eq2) {
    resultado.textContent = "Selecciona dos equipos distintos.";
    return;
  }

  resultado.textContent = "🔄 Calculando...";

  fetch("/predecir", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ equipo1: eq1, equipo2: eq2 })
  })
    .then(res => res.json())
    .then(data => {
      if (data.resultado) {
        resultado.innerHTML = `<span class="animado">🏆 ¡Ganador probable: ${data.resultado}!</span>`;
      } else {
        resultado.textContent = "❌ No se pudo hacer la predicción.";
      }
    })
    .catch(() => {
      resultado.textContent = "❌ Error al contactar con el servidor.";
    });
});

import streamlit as st
import numpy as np
import os

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="AI-Refores CDMX", page_icon="🌲", layout="wide")

# --- BASE DE DATOS DE ESPECIES ---
# Parámetros calibrados y mapeo de imágenes 
ESPECIES = {
    "Pinus hartwegii (Pino de altura)": {
        "ln_alpha": 12.31, "beta": -1.605, "alt_range": (3000, 4200),
        "img": "especies/hartwegii.jpg",
        "desc": "Especie de alta montaña, adaptada a heladas extremas. Marca el límite arbóreo alpino."
    },
    "Pinus pseudostrobus (Pino lacio)": {
        "ln_alpha": 11.85, "beta": -1.540, "alt_range": (1600, 3200),
        "img": "especies/pseudostrobus.jpg",
        "desc": "Pino de rápido crecimiento, requiere buena humedad. Valorado por su madera lacia."
    },
    "Pinus montezumae (Ocote)": {
        "ln_alpha": 12.01, "beta": -1.605, "alt_range": (2400, 3000),
        "img": "especies/montezumae.jpg",
        "desc": "Especie productiva de gran valor maderero en suelos volcánicos profundos."
    },
    "Pinus teocote (Ocote chino)": {
        "ln_alpha": 11.57, "beta": -1.535, "alt_range": (1500, 3000),
        "img": "especies/teocote.jpg",
        "desc": "Muy rústico, ideal para sitios degradados, laderas erosionadas o con poca lluvia."
    },
    "Pinus leiophylla (Chimonque)": {
        "ln_alpha": 11.60, "beta": -1.580, "alt_range": (1600, 3000),
        "img": "especies/leiophylla.jpg",
        "desc": "Resistente a incendios y contaminación urbana; una de las pocas coníferas que rebrota."
    }
}

# --- LÓGICA DEL ALGORITMO ---
def fitness_function(N, temp, prec, altitud, sp_data):
    ahm = (temp + 10) / (prec / 1000)
    factor_clima = max(0.2, 1 - (ahm / 65)) 
    idr_max = np.exp(sp_data["ln_alpha"] + sp_data["beta"] * np.log(25)) * factor_clima
    dr = N / idr_max 
    if 0.35 <= dr <= 0.65:
        score = 100
    elif dr < 0.35:
        score = 100 * (dr / 0.35)
    else:
        score = 100 * np.exp(-5 * (dr - 0.65))
    min_alt, max_alt = sp_data["alt_range"]
    if altitud < min_alt or altitud > max_alt:
        diff = min(abs(altitud - min_alt), abs(altitud - max_alt))
        score -= diff * 0.1
    return max(0.0001, score)

def ejecutar_ag(area_ha, alt, temp, prec, pendiente, sp_name):
    sp_data = ESPECIES[sp_name]
    poblacion = np.random.uniform(400, 2500, 100)
    for _ in range(40):
        scores = np.array([fitness_function(n, temp, prec, alt, sp_data) for n in poblacion])
        nueva_poblacion = # FIX: Lista vacía correctamente inicializada
        nueva_poblacion.append(poblacion[np.argmax(scores)])
        while len(nueva_poblacion) < 100:
            p1 = np.random.choice(poblacion, p=scores/np.sum(scores))
            p2 = np.random.choice(poblacion, p=scores/np.sum(scores))
            hijo = ((p1 + p2) / 2) * np.random.uniform(0.95, 1.05)
            nueva_poblacion.append(hijo)
        poblacion = np.array(nueva_poblacion)
    n_ha = float(poblacion[np.argmax(scores)])
    if pendiente > 5:
        metodo = "Tres Bolillo (Triangulación)"
        total = int(n_ha * 1.155 * area_ha)
    else:
        metodo = "Marco Real (Cuadrícula)"
        total = int(n_ha * area_ha)
    return n_ha, total, metodo

# --- INTERFAZ STREAMLIT ---
st.title("🌲 AI-Refores: Optimización de Densidad con Visualización")
st.markdown("Determinación de densidad óptima para el **Suelo de Conservación (CDMX)**.")

with st.sidebar:
    st.header("📋 Parámetros de Selección")
    especie_sel = st.selectbox("Especie de Pino", list(ESPECIES.keys()))
    
    # Mostrar imagen de la especie en el sidebar si existe
    img_path = ESPECIES[especie_sel]["img"]
    if os.path.exists(img_path):
        st.image(img_path, caption=f"Identificación de {especie_sel}")
    else:
        st.warning(f"Imagen no encontrada en: {img_path}")
    
    st.caption(ESPECIES[especie_sel]["desc"])
    st.divider()
    area_in = st.number_input("Extensión (Hectáreas)", 0.1, 500.0, 10.0)
    alt_in = st.slider("Altitud (msnm)", 1500, 4300, 3000)
    t_in = st.slider("Temp. Media Anual (°C)", 5, 25, 12)
    p_in = st.slider("Precipitación Anual (mm)", 400, 2000, 1100)
    slope_in = st.slider("Pendiente (%)", 0, 60, 10)
    run = st.button("🚀 Optimizar Plantación")

if run:
    n, t, m = ejecutar_ag(area_in, alt_in, t_in, p_in, slope_in, especie_sel)
    st.success(f"¡Optimización para {especie_sel} completada!")
    
    # Layout solicitado: Metrics arriba, diseño abajo
    col1, col2 = st.columns(2)
    col1.metric("Densidad Biológica", f"{n:.2f} árb/ha")
    col2.metric("Total Árboles a Plantar", f"{t:,}")
    
    st.divider()
    st.metric("Diseño Sugerido (por pendiente)", m)
    
    distancia = np.sqrt(10000 / n)
    st.info(f"Distancia recomendada: ~{distancia:.2f} metros entre ejemplares.")
else:
    st.info("Ajuste los valores a la izquierda para iniciar la evolución genética.")

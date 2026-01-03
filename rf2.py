import streamlit as st
import numpy as np
import random
import os

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="AI-Refores CDMX", page_icon="🌲", layout="wide")

# --- BASE DE DATOS DE ESPECIES (Carpeta /images) ---
# Parámetros calibrados según silvicultura de precisión y Reineke 
ESPECIES = {
    "P. hartwegii": {
        "full_name": "Pinus hartwegii (Pino de altura)",
        "ln_alpha": 12.31, "beta": -1.605, "alt_range": (3000, 4200),
        "img": "images/hartwegii.jpg",
        "desc": "Especie de alta montaña, adaptada a heladas extremas. Marca el límite arbóreo alpino de la CDMX."
    },
    "P. pseudostrobus": {
        "full_name": "Pinus pseudostrobus (Pino lacio)",
        "ln_alpha": 11.85, "beta": -1.540, "alt_range": (1600, 3200),
        "img": "images/pinolacio.jpg",
        "desc": "Pino de rápido crecimiento, requiere alta humedad relativa. Valorado por su madera lacia superior."
    },
    "P. montezumae": {
        "full_name": "Pinus montezumae (Ocote)",
        "ln_alpha": 12.01, "beta": -1.605, "alt_range": (2400, 3000),
        "img": "images/pino-moctezuma.jpg",
        "desc": "Especie productiva de gran valor maderero en suelos volcánicos profundos (Andosoles)."
    },
    "P. teocote": {
        "full_name": "Pinus teocote (Ocote chino)",
        "ln_alpha": 11.57, "beta": -1.535, "alt_range": (1500, 3000),
        "img": "images/pinus-teocote.jpg",
        "desc": "Taxón muy rústico y resiliente, ideal para sitios degradados, laderas o zonas con baja precipitación."
    },
    "P. leiophylla": {
        "full_name": "Pinus leiophylla (Chimonque)",
        "ln_alpha": 11.60, "beta": -1.580, "alt_range": (1600, 3000),
        "img": "images/leiophylla04.jpg",
        "desc": "Altamente resistente a la contaminación urbana; es de las pocas coníferas que rebrota tras incendios."
    }
}

# --- LÓGICA DEL ALGORITMO GENÉTICO ---
def fitness_function(N, temp, prec, altitud, sp_data):      
    """Calcula la aptitud biológica basada en Reineke y clima [2]"""
    ahm = (temp + 10) / (prec / 1000) 
    factor_clima = max(0.2, 1 - (ahm / 65)) 
    idr_max = np.exp(sp_data["ln_alpha"] + sp_data["beta"] * np.log(25)) * factor_clima 
    dr = N / idr_max  
    
    if 0.35 <= dr <= 0.65:
        score = 100 # Ventana de Oro
    elif dr < 0.35:
        score = 100 * (dr / 0.35)
    else:
        score = 100 * np.exp(-5 * (dr - 0.65))
        
    min_alt, max_alt = sp_data["alt_range"]
    if altitud < min_alt or altitud > max_alt:
        diff = min(abs(altitud - min_alt), abs(altitud - max_alt))
        score -= diff * 0.1
    return max(0.0001, score)

def seleccion_ruleta_manual(poblacion, scores):
    """Selección proporcional por ruleta manual [2]"""
    fitness_total = sum(scores)
    p_s = [s / fitness_total for s in scores]
    p_acumulada = []
    ac = 0
    for p in p_s:
        ac += p
        p_acumulada.append(ac)
    giro = random.uniform(0, 1)
    for j, p in enumerate(p_acumulada):
        if giro <= p:
            return poblacion[j]
    return poblacion[-1]

def ejecutar_ag(area_ha, alt, temp, prec, pendiente, sp_key):
    sp_data = ESPECIES[sp_key]
    pop_size = 100
    poblacion = np.random.uniform(400, 2500, pop_size)
    p_mutacion = 0.1 
    
    for _ in range(40):
        scores = np.array([fitness_function(n, temp, prec, alt, sp_data) for n in poblacion])
        nueva_poblacion = []
        nueva_poblacion.append(poblacion[np.argmax(scores)]) # Elitismo [3]
        
        while len(nueva_poblacion) < pop_size:
            p1 = seleccion_ruleta_manual(poblacion, scores)
            p2 = seleccion_ruleta_manual(poblacion, scores)
            hijo = (p1 + p2) / 2
            if random.random() < p_mutacion:
                hijo = hijo * random.uniform(0.95, 1.05) # Mutación estocástica
            nueva_poblacion.append(hijo)
        poblacion = np.array(nueva_poblacion)

    n_ha = float(poblacion[np.argmax(scores)])
    if pendiente > 5:
        metodo = "Tres Bolillo (Triangulación)"
        total = int(n_ha * 1.155 * area_ha) # +15.5% según CONAFOR [1]
    else:
        metodo = "Marco Real (Cuadrícula)"
        total = int(n_ha * area_ha)
        
    return n_ha, total, metodo

# --- INTERFAZ STREAMLIT ---
st.title("🌲 AI-Refores: Optimización de Reforestación")
st.markdown("Determinación de densidad ideal para el **Suelo de Conservación (CDMX)** basada en algoritmos genéticos.")

with st.sidebar:
    st.header("Selección de Especie")
    sp_key = st.segmented_control(
        "Elige un Pino:", 
        options=list(ESPECIES.keys()), 
        default="P. hartwegii"
    )
    st.divider()
    
    st.header("⚙️ Parámetros del Terreno")
    st.info("Ingresa los valores con los botones o directamente con el teclado.")
    area_in = st.number_input("Extensión (Hectáreas)", 0.1, 500.0, 10.0, step=0.1)
    alt_in = st.number_input("Altitud (msnm)", 1500, 4500, 3000, step=50)
    t_in = st.number_input("Temp. Media Anual (°C)", 5.0, 30.0, 12.0, step=0.5)
    p_in = st.number_input("Precipitación Anual (mm)", 300, 2500, 1100, step=100)
    slope_in = st.number_input("Pendiente (%)", 0, 80, 10, step=1)
    
    st.divider()
    run_btn = st.button("🚀 Iniciar Optimización")

if run_btn:
    n, t, m = ejecutar_ag(area_in, alt_in, t_in, p_in, slope_in, sp_key)
    
    # 1. Ficha Técnica de la Especie (Main Panel)
    st.subheader(f"📋 Ficha Técnica: {ESPECIES[sp_key]['full_name']}")
    col_img, col_txt = st.columns([4, 5], gap="large")
    
    with col_img:
        img_path = ESPECIES[sp_key]["img"]
        if os.path.exists(img_path):
            st.image(img_path, caption=f"Morfología de {sp_key}", use_container_width=True)
        else:
            st.warning("Aviso: Imagen no detectada en la carpeta del repositorio.")
            
    with col_txt:
        st.markdown(f"**Descripción:** {ESPECIES[sp_key]['desc']}")
        st.write(f"**Estatus Ecológico:** Especie Nativa autorizada para restauración en CDMX.")
        st.info(f"¡Optimización para {sp_key} completada con éxito!")

    st.divider()
    
    # 2. Resultados de la Optimización (Dashboard)
    col1, col2 = st.columns(2)
    col1.metric("Densidad Biológica Sugerida", f"{n:.2f} árb/ha")
    col2.metric("Total de Árboles a Plantar", f"{t:,}")
    
    st.divider()
    st.metric("Diseño Prescrito (según pendiente)", m)
    
    # 3. Recomendaciones Adicionales
    distancia = np.sqrt(10000 / n)
    st.info(f"📍 Distancia recomendada: ~{distancia:.2f} metros entre cada árbol.")
    st.write("**Nota Silvicultural:** El modelo ha ajustado la densidad para maximizar la supervivencia ante el Índice de Calor-Humedad (AHM) del sitio.")

else:
    st.info("Ajusta los parámetros en la barra lateral y presiona el botón. Recuerda que puedes **escribir directamente los valores** para mayor precisión.")

import streamlit as st
import numpy as np

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Reforestación CDMX AI", layout="wide")

# --- PARÁMETROS BIOMÉTRICOS (Pinus hartwegii) ---
LN_ALPHA = 12.01457   
BETA = -1.605         
D_REF = 25.0          

def calcular_idr_max_base():
    return np.exp(LN_ALPHA + BETA * np.log(D_REF))

# --- LÓGICA DEL ALGORITMO GENÉTICO ---

def fitness_function(N, temp_media, prec_anual, altitud):
    # Ajuste Climático (AHM)
    ahm = (temp_media + 10) / (prec_anual / 1000)
    factor_clima = max(0.2, 1 - (ahm / 60)) 
    
    # Densidad Relativa (DR)
    idr_max_sitio = calcular_idr_max_base() * factor_clima
    dr = N / idr_max_sitio
    
    # Lógica de Puntuación (Regla 35-65%) [1]
    if 0.35 <= dr <= 0.65:
        score = 100 
    elif dr < 0.35:
        score = 100 * (dr / 0.35)  
    else:
        score = 100 * np.exp(-5 * (dr - 0.65)) 
        
    # Restricción Altitudinal
    if altitud > 4000:
        score -= (altitud - 4000) * 1.5
        
    return max(0.0001, score)

def seleccion_ruleta(poblacion, scores):
    probabilidades = scores / np.sum(scores)
    return np.random.choice(poblacion, p=probabilidades)

def ejecutar_ag(area_ha, altitud, temp, prec, pendiente):
    pop_size = 100
    generaciones = 40
    poblacion = np.random.uniform(400, 2500, pop_size)
    
    for _ in range(generaciones):
        scores = np.array([fitness_function(n, temp, prec, altitud) for n in poblacion])
        nueva_poblacion =
        
        # Elitismo: Guardar el mejor
        nueva_poblacion.append(poblacion[np.argmax(scores)])
        
        while len(nueva_poblacion) < pop_size:
            p1 = seleccion_ruleta(poblacion, scores)
            p2 = seleccion_ruleta(poblacion, scores)
            hijo = (p1 + p2) / 2 # Cruza aritmética
            hijo *= np.random.uniform(0.95, 1.05) # Mutación 5%
            nueva_poblacion.append(hijo)
            
        poblacion = np.array(nueva_poblacion)

    n_optima_ha = poblacion
    
    # Ajuste por Diseño Geométrico 
    if pendiente > 5:
        diseno = "Tres Bolillo (Triangulación)"
        n_final = n_optima_ha * 1.155 
    else:
        diseno = "Marco Real (Cuadrícula)"
        n_final = n_optima_ha
        
    return n_optima_ha, int(n_final * area_ha), diseno

# --- INTERFAZ DE USUARIO ---

st.title("🌲 AI-Refores: Optimización Genética de Reforestación")
st.markdown("Determinación de densidad óptima para **Suelo de Conservación (CDMX)** basada en silvicultura cuantitativa.")

with st.sidebar:
    st.header("⚙️ Parámetros del Terreno")
    area = st.number_input("Extensión del terreno (Hectáreas)", min_value=0.1, max_value=500.0, value=10.0)
    alt = st.slider("Altitud (msnm)", 2500, 4300, 3850)
    temp = st.slider("Temperatura Media Anual (°C)", 5, 22, 11)
    prec = st.slider("Precipitación Anual (mm)", 400, 2000, 1200)
    slope = st.slider("Pendiente del terreno (%)", 0, 45, 12)
    
    st.divider()
    run_btn = st.button("🚀 Ejecutar Algoritmo Genético")

if run_btn:
    with st.spinner("Evolucionando densidades..."):
        n_ha, total, metodo = ejecutar_ag(area, alt, temp, prec, slope)
    
    st.success("¡Optimización Completada!")
    
    # Dashboard de Resultados
    col1, col2, col3 = st.columns(3)
    col1.metric("Densidad Biológica", f"{n_ha:.2f} árb/ha")
    col2.metric("Total Árboles a Plantar", f"{total}")
    col3.metric("Diseño Sugerido", metodo)
    
    st.divider()
    
    # Recomendaciones Técnicas
    st.subheader("📋 Recomendaciones Técnicas de Establecimiento")
    st.info(f"Para el diseño **{metodo}**, se recomienda un espaciamiento de aproximadamente {np.sqrt(10000/n_ha):.2f} metros entre plantas.")
    
    st.write("""
    - **Especie:** *Pinus hartwegii* (Pino de altura).
    - **Justificación:** La densidad se ajustó automáticamente para evitar el estrés hídrico y el daño por heladas frecuentes en el límite alpino.
    - **Mantenimiento:** Se estima una reposición de planta del 10-15% durante el primer año .
    """)
else:
    st.info("Ajusta los valores en el panel de la izquierda y presiona 'Ejecutar' para obtener la prescripción.")
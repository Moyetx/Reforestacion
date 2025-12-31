import streamlit as st
import numpy as np

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="AI-Refores CDMX", page_icon="🌲", layout="wide")

# --- PARÁMETROS BIOMÉTRICOS (Pinus hartwegii) ---
# Datos obtenidos de investigación silvicultural en México [1]
LN_ALPHA = 12.01457   # Intercepto de Reineke para coníferas mexicanas
BETA = -1.605         # Pendiente universal de autoaclareo [1]
D_REF = 25.0          # Diámetro de referencia estándar (cm)

def calcular_idr_max_base():
    """Calcula la capacidad de carga máxima teórica"""
    return np.exp(LN_ALPHA + BETA * np.log(D_REF))

def fitness_function(N, temp_media, prec_anual, altitud):
    """Evalúa la aptitud biológica basada en clima y densidad relativa"""
    # 1. Ajuste Climático (Índice AHM)
    ahm = (temp_media + 10) / (prec_anual / 1000)
    factor_clima = max(0.2, 1 - (ahm / 60)) 
    
    # 2. Capacidad de carga del sitio ajustada por clima
    idr_max_sitio = calcular_idr_max_base() * factor_clima
    dr = N / idr_max_sitio
    
    # 3. Lógica de Puntuación: Regla del 35-65% [1]
    if 0.35 <= dr <= 0.65:
        score = 100  # Zona óptima de crecimiento constante
    elif dr < 0.35:
        score = 100 * (dr / 0.35)  # Penaliza subutilización
    else:
        # Penaliza riesgo de mortalidad por autoaclareo [1]
        score = 100 * np.exp(-5 * (dr - 0.65)) 
        
    # 4. Restricción Altitudinal (Pinus hartwegii arriba de 4000m)
    if altitud > 4000:
        score -= (altitud - 4000) * 1.5
        
    return max(0.0001, score)

def seleccion_ruleta(poblacion, scores):
    """Selecciona un individuo de forma proporcional a su fitness"""
    probabilidades = scores / np.sum(scores)
    return np.random.choice(poblacion, p=probabilidades)

def ejecutar_ag(area_ha, altitud, temp, prec, pendiente):
    pop_size = 100
    generaciones = 40
    # Inicialización aleatoria entre 400 y 2500 árboles/ha [2]
    poblacion = np.random.uniform(400, 2500, pop_size)
    
    for _ in range(generaciones):
        # Evaluación
        scores = np.array([fitness_function(n, temp, prec, altitud) for n in poblacion])
        
        # FIX: Inicialización correcta de la lista
        nueva_poblacion =
        
        # Elitismo: Mantener al mejor individuo [3]
        mejor_actual = poblacion[np.argmax(scores)]
        nueva_poblacion.append(mejor_actual)
        
        while len(nueva_poblacion) < pop_size:
            p1 = seleccion_ruleta(poblacion, scores)
            p2 = seleccion_ruleta(poblacion, scores)
            # Cruza aritmética y mutación estocástica (+/- 5%)
            hijo = (p1 + p2) / 2
            hijo *= np.random.uniform(0.95, 1.05)
            nueva_poblacion.append(hijo)
            
        poblacion = np.array(nueva_poblacion)

    # Evaluación final para extraer el mejor escalar
    final_scores = np.array([fitness_function(n, temp, prec, altitud) for n in poblacion])
    n_optima_ha = float(poblacion[np.argmax(final_scores)]) # Garantiza que sea un escalar
    
    # Ajuste por Diseño Geométrico [2]
    if pendiente > 5:
        diseno = "Tres Bolillo (Triangulación)"
        n_final_diseno = n_optima_ha * 1.155  # Incremento de 15.5% en densidad
    else:
        diseno = "Marco Real (Cuadrícula)"
        n_final_diseno = n_optima_ha
        
    total_arboles = int(n_final_diseno * area_ha)
    
    return n_optima_ha, total_arboles, diseno

# --- INTERFAZ STREAMLIT ---
st.title("🌲 AI-Refores: Optimización de Reforestación")
st.markdown("Cálculo de densidad ideal para **Suelo de Conservación (CDMX)** basado en algoritmos genéticos.")

with st.sidebar:
    st.header("⚙️ Parámetros de Entrada")
    area_input = st.number_input("Extensión del terreno (Hectáreas)", 0.1, 500.0, 10.0)
    alt_input = st.slider("Altitud (msnm)", 2500, 4300, 3850)
    t_input = st.slider("Temp. Media Anual (°C)", 5, 22, 11)
    p_input = st.slider("Precipitación Anual (mm)", 400, 2000, 1200)
    slope_input = st.slider("Pendiente (%)", 0, 45, 12)
    
    btn = st.button("🚀 Ejecutar Algoritmo Genético")

if btn:
    # Llamada a la función de ejecución
    n_ha, total, metodo = ejecutar_ag(area_input, alt_input, t_input, p_input, slope_input)
    
    st.success("¡Optimización Completada!")
    col1, col2, col3 = st.columns(3)
    col1.metric("Densidad/Hectárea", f"{n_ha:.2f} árb/ha")
    col2.metric("TOTAL DE ÁRBOLES", f"{total}")
    col3.metric("Diseño Sugerido", metodo)
    
    # Recomendación adicional basada en espaciamiento real
    distancia = np.sqrt(10000 / n_ha)
    st.info(f"Distancia de plantación recomendada: ~{distancia:.2f} metros entre ejemplares.")
else:
    st.info("Ajuste los valores a la izquierda y presione 'Ejecutar' para ver la recomendación técnica.")

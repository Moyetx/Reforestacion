import streamlit as st
import numpy as np

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="AI-Refores CDMX", page_icon="🌲", layout="wide")

# --- PARÁMETROS BIOMÉTRICOS (Pinus hartwegii) ---
# Basado en la Ley de Reineke y la Ventana de Oro (35-65%) [1]
LN_ALPHA = 12.01457   # Intercepto para coníferas en México [1]
BETA = -1.605         # Pendiente universal de autoaclareo [1]
D_REF = 25.0          # Diámetro de referencia estándar (cm)

def calcular_idr_max_base():
    """Calcula el IDR máximo teórico absoluto"""
    return np.exp(LN_ALPHA + BETA * np.log(D_REF))

def fitness_function(N, temp_media, prec_anual, altitud):
    """Evalúa la aptitud biológica de la densidad propuesta"""
    # 1. Ajuste Climático (Índice AHM)
    ahm = (temp_media + 10) / (prec_anual / 1000)
    factor_clima = max(0.2, 1 - (ahm / 60)) 
    
    # 2. Capacidad de carga del sitio ajustada por clima
    idr_max_sitio = calcular_idr_max_base() * factor_clima
    dr = N / idr_max_sitio # Densidad Relativa
    
    # 3. Lógica de Puntuación (Regla 35-65%) [1]
    # Penaliza subutilización (<35%) y competencia extrema (>65%)
    if 0.35 <= dr <= 0.65:
        score = 100  
    elif dr < 0.35:
        score = 100 * (dr / 0.35)  
    else:
        score = 100 * np.exp(-5 * (dr - 0.65)) 
        
    # 4. Restricción por Altitud extrema (>4000m)
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
    # Inicialización aleatoria entre 400 y 2500 árboles/ha 
    poblacion = np.random.uniform(400, 2500, pop_size)
    
    for _ in range(generaciones):
        # Evaluación
        scores = np.array([fitness_function(n, temp, prec, altitud) for n in poblacion])
        
        # Inicialización de lista vacía corregida
        nueva_poblacion = []
        
        # Elitismo: Preservar al mejor individuo [3]
        mejor_actual = poblacion[np.argmax(scores)]
        nueva_poblacion.append(mejor_actual)
        
        while len(nueva_poblacion) < pop_size:
            p1 = seleccion_ruleta(poblacion, scores)
            p2 = seleccion_ruleta(poblacion, scores)
            # Cruza aritmética y mutación +/- 5% [4]
            hijo = (p1 + p2) / 2
            hijo *= np.random.uniform(0.95, 1.05)
            nueva_poblacion.append(hijo)
            
        poblacion = np.array(nueva_poblacion)

    # Evaluación final para extraer el mejor valor como número real (escalar)
    final_scores = np.array([fitness_function(n, temp, prec, altitud) for n in poblacion])
    n_ha_final = float(poblacion[np.argmax(final_scores)]) 
    
    # Ajuste por Diseño Geométrico y Pendiente 
    # Si la pendiente es > 5% se recomienda tres bolillo (15.5% más densidad)
    if pendiente > 5:
        diseno = "Tres Bolillo (Triangulación)"
        n_para_conteo = n_ha_final * 1.155 
    else:
        diseno = "Marco Real (Cuadrícula)"
        n_para_conteo = n_ha_final
        
    total_final = int(n_para_conteo * area_ha)
    
    return n_ha_final, total_final, diseno

# --- INTERFAZ DE USUARIO ---
st.title("🌲 AI-Refores: Optimización de Reforestación")
st.markdown("Cálculo de densidad ideal para **Suelo de Conservación (CDMX)** basado en algoritmos genéticos.")

with st.sidebar:
    st.header("⚙️ Parámetros de Entrada")
    area_in = st.number_input("Extensión del terreno (Hectáreas)", 0.1, 500.0, 10.0)
    alt_in = st.slider("Altitud (msnm)", 2500, 4300, 3850)
    t_in = st.slider("Temp. Media Anual (°C)", 5, 22, 11)
    p_in = st.slider("Precipitación Anual (mm)", 400, 2000, 1200)
    slope_in = st.slider("Pendiente (%)", 0, 45, 12)
    
    run_ag = st.button("🚀 Ejecutar Algoritmo Genético")

if run_ag:
    # Ejecución y desempaquetado de resultados
    n_ha, total, metodo = ejecutar_ag(area_in, alt_in, t_in, p_in, slope_in)
    
    st.success("¡Optimización Completada!")
    
    # Renderizado de métricas con valores escalares seguros
    col1, col2, col3 = st.columns(3)
    col1.metric("Densidad por Hectárea", f"{n_ha:.2f} árb/ha")
    col2.metric("Total de Árboles a Plantar", f"{total:,}")
    col3.metric("Diseño Sugerido", metodo)
    
    # Cálculo de distancia entre plantas bajo diseño Tres Bolillo o Marco Real
    distancia = np.sqrt(10000 / n_ha)
    st.info(f"Distancia de plantación recomendada: ~{distancia:.2f} metros entre ejemplares.")
    
    st.write("**Nota Biológica:** La densidad se ajusta automáticamente para maximizar la supervivencia del *Pinus hartwegii* ante heladas y estrés hídrico.")
else:
    st.info("Ajuste los valores en la barra lateral y presione 'Ejecutar' para ver la recomendación técnica.")


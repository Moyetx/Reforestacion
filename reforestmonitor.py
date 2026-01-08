import streamlit as st
import numpy as np
import random
import os
import pandas as pd # Agregamos pandas para la gráfica fácil


# CONFIGURACIÓN DE PÁGINA streamlit
st.set_page_config(page_title="AI-Refores CDMX", layout="wide")

# Diccionarios de especies
ESPECIES = {
    "P. hartwegii": {
        "nombre_completo": "Pinus hartwegii (Pino de altura)",
        "ln_alpha": 12.31, "beta": -1.605, "rango_alt": (3000, 4200),
        "img": "images/hartwegii.jpg",
        "desc": "Especie de alta montaña, adaptada a heladas extremas. Marca el límite arbóreo alpino de la CDMX."
    },
    "P. pseudostrobus": {
        "nombre_completo": "Pinus pseudostrobus (Pino lacio)",
        "ln_alpha": 11.85, "beta": -1.540, "rango_alt": (1600, 3200),
        "img": "images/pinolacio.jpg",
        "desc": "Pino de rápido crecimiento, requiere alta humedad relativa. Valorado por su madera lacia superior."
    },
    "P. montezumae": {
        "nombre_completo": "Pinus montezumae (Ocote)",
        "ln_alpha": 12.01, "beta": -1.605, "rango_alt": (2400, 3000),
        "img": "images/pino-moctezuma.jpg",
        "desc": "Especie productiva de gran valor maderero en suelos volcánicos profundos (Andosoles)."
    },
    "P. teocote": {
        "nombre_completo": "Pinus teocote (Ocote chino)",
        "ln_alpha": 11.57, "beta": -1.535, "rango_alt": (1500, 3000),
        "img": "images/pinus-teocote.jpg",
        "desc": "Taxón muy rústico y resiliente, ideal para sitios degradados, laderas o zonas con baja precipitación."
    },
    "P. leiophylla": {
        "nombre_completo": "Pinus leiophylla (Chimonque)",
        "ln_alpha": 11.60, "beta": -1.580, "rango_alt": (1600, 3000),
        "img": "images/leiophylla04.jpg",
        "desc": "Altamente resistente a la contaminación urbana; es de las pocas coníferas que rebrota tras incendios."
    }
}

# Funcion fitness
def calcular_aptitud(N, temp, prec, altitud, datos_especie):      
    """Calcula la aptitud biológica basada en Reineke langsaeter, ahm y altitud."""
    ahm = (temp + 10) / (prec / 1000)
    factor_clima = max(0.2, 1 - (ahm / 65)) 
    
    idr_max = np.exp(datos_especie["ln_alpha"] + datos_especie["beta"] * np.log(25)) * factor_clima 
    dr = N / idr_max  
    
    if 0.35 <= dr <= 0.65:
        #puntaje = 100
        puntaje = 100 * np.exp(-((dr - 0.5) ** 2) / 0.01)

    elif dr < 0.35:
        puntaje = 100 * (dr / 0.35) 
    else:
        puntaje = 100 * np.exp(-5 * (dr - 0.65)) 
        
    alt_min, alt_max = datos_especie["rango_alt"] 
    if altitud < alt_min or altitud > alt_max:
        diferencia = min(abs(altitud - alt_min), abs(altitud - alt_max)) 
        puntaje -= diferencia * 0.1 
        
    return max(0.0001, puntaje) 

def seleccion_ruleta_manual(poblacion, puntajes):
    aptitud_total = sum(puntajes)
    prob_seleccion = [s / aptitud_total for s in puntajes]
    prob_acumulada = []
    acumulado = 0
    
    for p in prob_seleccion:
        acumulado += p
        prob_acumulada.append(acumulado)
        
    giro = random.uniform(0, 1)
    
    for j, p in enumerate(prob_acumulada):
        if giro <= p:
            return poblacion[j]
            
    return poblacion[-1]

def ejecutar_ag(area_ha, alt, temp, prec, pendiente, clave_especie):
    datos_especie = ESPECIES[clave_especie]
    tam_poblacion = 150 
    poblacion = np.random.uniform(400, 2500, tam_poblacion)
    #prob_mutacion = 0.2
    #prob_mutacion = 0.35 if i < 10 else 0.15

    
    # VARIABLES PARA MONITOREO
    historial_logs = []       # Guardará el texto de "Generación X..."
    historial_fitness = []    # Guardará solo los números para la gráfica
    mejor_fitness_historico = -1
    generacion_convergencia = 0
    
    for i in range(50):
        prob_mutacion = 0.35 if i < 10 else 0.15

        puntajes = np.array([calcular_aptitud(n, temp, prec, alt, datos_especie) for n in poblacion])
        
        # --- LÓGICA DE REPORTE Y CONVERGENCIA ---
        mejor_idx_actual = np.argmax(puntajes)
        mejor_fitness_actual = puntajes[mejor_idx_actual]
        mejor_individuo_actual = poblacion[mejor_idx_actual]
        
        # Guardamos datos para la gráfica
        historial_fitness.append(mejor_fitness_actual)
        
        # Guardamos datos para el texto (Print)
        log = f"Gen {i+1}: Mejor Indiv = {mejor_individuo_actual:.2f} arb/ha | Fitness = {mejor_fitness_actual:.4f}"
        historial_logs.append(log)
        
        # Detectar convergencia (¿Cuándo encontramos este valor óptimo por primera vez?)
        # Como usamos elitismo, el fitness nunca baja. Si sube, actualizamos la generación de convergencia.
        if mejor_fitness_actual > mejor_fitness_historico:
            mejor_fitness_historico = mejor_fitness_actual
            generacion_convergencia = i + 1
        
        # ----------------------------------------

        nueva_poblacion = [] 
        nueva_poblacion.append(poblacion[np.argmax(puntajes)]) 
        
        while len(nueva_poblacion) < tam_poblacion:
            padre1 = seleccion_ruleta_manual(poblacion, puntajes)
            padre2 = seleccion_ruleta_manual(poblacion, puntajes)
            
            hijo = (padre1 + padre2) / 2
            
            if random.random() < prob_mutacion:
                hijo = hijo * random.uniform(0.95, 1.05) 
                
            nueva_poblacion.append(hijo)
            
        poblacion = np.array(nueva_poblacion)

    densidad_final = float(poblacion[np.argmax(puntajes)])
    
    if pendiente > 5:
        metodo = "Tres Bolillo (Triangulación)"
        total_arboles = int(densidad_final * 1.155 * area_ha) 
    else:
        metodo = "Marco Real (Cuadrícula)"
        total_arboles = int(densidad_final * area_ha)
        
    # Retornamos también los historiales
    return densidad_final, total_arboles, metodo, historial_logs, historial_fitness, generacion_convergencia

# INTERFAZ STREAMLIT
st.title("AI-Refores: Optimización de Reforestación")
st.markdown("Determinación de densidad ideal para el **Suelo de Conservación (CDMX)** basada en algoritmos genéticos.")

with st.sidebar:
    st.header("Selección de Especie")
    clave_especie = st.segmented_control(
        "Elige un Pino:", 
        options=list(ESPECIES.keys()), 
        default="P. hartwegii"
    )
    st.divider()
    
    st.header("Parámetros del Terreno")
    st.info("Ingresa los valores con los botones o directamente con el teclado.")
    
    area_usuario = st.number_input("Extensión (Hectáreas)", 0.1, 500.0, 10.0, step=0.1)
    altitud_usuario = st.number_input("Altitud (msnm)", 1500, 4500, 3000, step=50)
    temp_usuario = st.number_input("Temp. Media Anual (°C)", 5.0, 30.0, 12.0, step=0.5)
    precip_usuario = st.number_input("Precipitación Anual (mm)", 300, 2500, 1100, step=100)
    pendiente_usuario = st.number_input("Pendiente (%)", 0, 80, 10, step=1)
    
    st.divider()
    boton_inicio = st.button("Iniciar Optimización")

if boton_inicio:
    # Ejecución del algoritmo (Ahora recibimos más variables)
    densidad_optima, total_plantas, metodo_siembra, logs, fit_history, gen_conv = ejecutar_ag(
        area_usuario, altitud_usuario, temp_usuario, precip_usuario, pendiente_usuario, clave_especie
    )
    
    # 1. Ficha Técnica
    st.subheader(f"Ficha Técnica: {ESPECIES[clave_especie]['nombre_completo']}")
    col_imagen, col_texto = st.columns([4, 5], gap="large")
    
    with col_imagen:
        ruta_imagen = ESPECIES[clave_especie]["img"]
        if os.path.exists(ruta_imagen):
            st.image(ruta_imagen, caption=f"Morfología de {clave_especie}", use_container_width=True)
        else:
            st.warning("Aviso: Imagen no detectada en la carpeta del repositorio.")
            
    with col_texto:
        st.markdown(f"**Descripción:** {ESPECIES[clave_especie]['desc']}")
        st.write(f"**Estatus Ecológico:** Especie Nativa autorizada para restauración en CDMX.")
        st.info(f"¡Optimización para {clave_especie} completada con éxito!")

    st.divider()
    
    # 2. Resultados
    col1, col2 = st.columns(2)
    col1.metric("Densidad Biológica Sugerida", f"{densidad_optima:.2f} árb/ha")
    col2.metric("Total de Árboles a Plantar", f"{total_plantas:,}")
    
    st.divider()
    
    # --- SECCIÓN NUEVA: MONITOR DE EVOLUCIÓN ---
    st.subheader("visualizador")
    
    # Mensaje de convergencia
    if gen_conv < 39:
        st.success(f" El algoritmo convergió (encontró su mejor solución estable) en la **Generación {gen_conv}**.")
    else:
        st.warning(f" El algoritmo siguió encontrando mejoras hasta la última generación ({gen_conv}).")

    # Gráfica de convergencia
    chart_data = pd.DataFrame(fit_history, columns=["Aptitud (Fitness)"])
    st.line_chart(chart_data)
    st.caption("Gráfica: Muestra cómo mejora la 'Aptitud' del mejor individuo a través de las generaciones.")

    # Expander con los "Prints" (Logs)
    with st.expander("Ver registro detallado por Generación (Logs)"):
        for linea in logs:
            st.text(linea) # st.text imprime con fuente tipo consola
    # -------------------------------------------
    
    st.divider()
    st.metric("Diseño Prescrito (según pendiente)", metodo_siembra)
    distancia_siembra = np.sqrt(10000 / densidad_optima)
    st.info(f"Distancia recomendada: ~{distancia_siembra:.2f} metros entre cada árbol.")
    st.write("**Nota Silvicultural:** El modelo ha ajustado la densidad para maximizar la supervivencia ante el Índice de Calor-Humedad (AHM) del sitio.")

else:
    st.info("Ajusta los parámetros en la barra lateral y presiona el botón. Recuerda que puedes **escribir directamente los valores** para mayor precisión.")

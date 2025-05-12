import streamlit as st
import sqlite3
import time
from datetime import datetime, timedelta
import pandas as pd

# ----------------- CONSTANTES -----------------
MAX_JUGADORES = 3
DB_NAME = "resultados.db"

# ----------------- FUNCIONES DE FECHA MEJORADAS -----------------
def safe_parse_datetime(dt_str):
    """Analiza una cadena de fecha de manera segura con múltiples formatos"""
    if dt_str is None:
        return None
    if isinstance(dt_str, datetime):
        return dt_str
    
    # Formatos a probar (ordenados de más específico a más general)
    formats = [
        "%Y-%m-%d %H:%M:%S.%f",  # Con microsegundos
        "%Y-%m-%d %H:%M:%S",      # Sin microsegundos
        "%Y-%m-%d %H:%M",         # Sin segundos
        "%Y-%m-%d"                # Solo fecha
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(dt_str, fmt)
        except (ValueError, TypeError):
            continue
    
    # Si todos los formatos fallan, devuelve None y registra el error
    st.error(f"Formato de fecha no reconocido: {dt_str}")
    return None

def format_timedelta(td):
    """Formatea un timedelta a HH:MM:SS"""
    if td is None:
        return "00:00:00"
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

# ----------------- INICIALIZAR BASE DE DATOS -----------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resultados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS juego_activo (
            id INTEGER PRIMARY KEY DEFAULT 1 CHECK (id = 1),
            enunciado TEXT NOT NULL,
            duracion INTEGER NOT NULL,
            tiempo_inicio TEXT,  # Almacenado como texto ISO
            activo BOOLEAN DEFAULT 0
        )
    """)
    
    conn.commit()
    conn.close()

# ----------------- FUNCIONES DE BASE DE DATOS -----------------
def obtener_resultados():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute(f"""
        SELECT nombre, timestamp 
        FROM resultados 
        ORDER BY timestamp ASC 
        LIMIT {MAX_JUGADORES}
    """)
    
    resultados = cursor.fetchall()
    conn.close()
    
    # Convertir las fechas de manera segura
    parsed_results = []
    for nombre, timestamp in resultados:
        parsed_time = safe_parse_datetime(timestamp)
        if parsed_time is not None:
            parsed_results.append((nombre, parsed_time))
    
    return parsed_results

def obtener_estado_juego():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT enunciado, duracion, tiempo_inicio FROM juego_activo WHERE activo = 1")
    juego = cursor.fetchone()
    conn.close()
    
    if juego:
        enunciado, duracion, tiempo_inicio_str = juego
        tiempo_inicio = safe_parse_datetime(tiempo_inicio_str)
        return (enunciado, duracion, tiempo_inicio)
    return None

def iniciar_juego(enunciado, duracion):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Usamos formato ISO para almacenar la fecha
    tiempo_inicio_iso = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT OR REPLACE INTO juego_activo 
        (id, enunciado, duracion, tiempo_inicio, activo)
        VALUES (1, ?, ?, ?, 1)
    """, (enunciado, duracion, tiempo_inicio_iso))
    
    conn.commit()
    conn.close()
    reiniciar_resultados()

# ----------------- PANTALLA DE INICIO MEJORADA -----------------
def mostrar_inicio():
    st.title("🏆 Juego de Programación Competitiva")
    
    st.markdown("""
        <style>
            .result-table {
                width: 100%;
                border-collapse: collapse;
            }
            .result-table th {
                background-color: #f2f2f2;
                text-align: left;
                padding: 8px;
            }
            .result-table td {
                padding: 8px;
                border-bottom: 1px solid #ddd;
            }
        </style>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👨‍🏫 Modo Docente", key="docente_btn"):
            st.session_state.pantalla = "docente"
    with col2:
        if st.button("👩‍🎓 Modo Estudiante", key="estudiante_btn"):
            st.session_state.pantalla = "estudiante"
    
    # Mostrar últimos resultados si existen
    resultados = obtener_resultados()
    if resultados:
        st.subheader("🏅 Podio Actual")
        
        # Crear tabla de posiciones
        html = """
        <table class="result-table">
            <tr>
                <th>Posición</th>
                <th>Nombre</th>
                <th>Hora de Finalización</th>
            </tr>
        """
        
        for i, (nombre, timestamp) in enumerate(resultados, start=1):
            tiempo_str = timestamp.strftime("%H:%M:%S") if timestamp else "N/A"
            
            medal = ""
            if i == 1: medal = "🥇"
            elif i == 2: medal = "🥈"
            elif i == 3: medal = "🥉"
            
            html += f"""
            <tr>
                <td>{medal} {i}º</td>
                <td>{nombre}</td>
                <td>{tiempo_str}</td>
            </tr>
            """
        
        html += "</table>"
        st.markdown(html, unsafe_allow_html=True)

# ----------------- MODO ESTUDIANTE MEJORADO -----------------
def modo_estudiante():
    st.header("👩‍🎓 Modo Competidor")
    
    juego = obtener_estado_juego()
    
    if not juego or not juego[2]:  # Si no hay juego activo
        st.warning("⌛ Esperando a que el docente inicie el juego...")
        return
    
    enunciado, duracion, tiempo_inicio = juego
    
    st.subheader("📋 Enunciado del Problema")
    st.markdown(f"```\n{enunciado}\n```")
    
    # Mostrar tiempo restante
    tiempo_restante = (tiempo_inicio + timedelta(minutes=duracion)) - datetime.now()
    
    if tiempo_restante.total_seconds() > 0:
        st.metric("⏳ Tiempo restante", value=format_timedelta(tiempo_restante))
    else:
        st.error("⌛ El tiempo se ha terminado!")
    
    # Verificar si ya hay 3 participantes
    resultados = obtener_resultados()
    bloqueado = len(resultados) >= MAX_JUGADORES
    
    if bloqueado:
        st.error("❌ El juego ya tiene los 3 primeros finalistas. No se aceptan más participantes.")
    else:
        with st.form("form_participante"):
            nombre = st.text_input("👤 Nombre completo", placeholder="Ingrese su nombre completo")
            
            enviado = st.form_submit_button(
                "🏁 Finalizar y Registrar", 
                disabled=tiempo_restante.total_seconds() <= 0 or bloqueado
            )
            
            if enviado:
                if not nombre.strip():
                    st.error("Debe ingresar su nombre")
                else:
                    exito = insertar_resultado(nombre.strip())
                    if exito:
                        st.success(f"🎉 ¡Registrado como participante #{len(resultados)+1}!")
                        st.rerun()
                    else:
                        st.error("❌ Ya se han registrado los 3 primeros participantes")

    # Mostrar podio actual
    if resultados:
        st.subheader("🏆 Podio Actual")
        
        # Usamos pandas para mostrar la tabla de forma más robusta
        df = pd.DataFrame([
            {
                "Posición": f"{'🥇' if i==1 else '🥈' if i==2 else '🥉'} {i}º",
                "Nombre": nombre,
                "Hora": timestamp.strftime("%H:%M:%S") if timestamp else "N/A"
            }
            for i, (nombre, timestamp) in enumerate(resultados, start=1)
        ])
        
        st.dataframe(df, hide_index=True, use_container_width=True)

# ----------------- APLICACIÓN PRINCIPAL -----------------
def main():
    init_db()
    
    if "pantalla" not in st.session_state:
        st.session_state.pantalla = None
    
    if st.session_state.pantalla is None:
        mostrar_inicio()
    elif st.session_state.pantalla == "docente":
        modo_docente()
    elif st.session_state.pantalla == "estudiante":
        modo_estudiante()

if __name__ == "__main__":
    main()
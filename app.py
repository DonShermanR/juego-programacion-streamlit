import streamlit as st
import sqlite3
import time
from datetime import datetime, timedelta
import pandas as pd

# ----------------- CONSTANTES -----------------
MAX_JUGADORES = 3
DB_NAME = "resultados.db"

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
            tiempo_inicio DATETIME,
            activo BOOLEAN DEFAULT 0
        )
    """)
    
    conn.commit()
    conn.close()

# ----------------- FUNCIONES DE BASE DE DATOS -----------------
def insertar_resultado(nombre):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM resultados")
    count = cursor.fetchone()[0]
    
    if count < MAX_JUGADORES:
        cursor.execute(
            "INSERT INTO resultados (nombre) VALUES (?)",
            (nombre,)
        )
        conn.commit()
        resultado = True
    else:
        resultado = False
    
    conn.close()
    return resultado

def obtener_resultados():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT nombre, timestamp 
        FROM resultados 
        ORDER BY timestamp ASC 
        LIMIT ?
    """, (MAX_JUGADORES,))
    
    resultados = cursor.fetchall()
    conn.close()
    return resultados

def reiniciar_resultados():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM resultados")
    conn.commit()
    conn.close()

def iniciar_juego(enunciado, duracion):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT OR REPLACE INTO juego_activo 
        (id, enunciado, duracion, tiempo_inicio, activo)
        VALUES (1, ?, ?, ?, 1)
    """, (enunciado, duracion, datetime.now()))
    
    conn.commit()
    conn.close()
    reiniciar_resultados()

def obtener_estado_juego():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT enunciado, duracion, tiempo_inicio FROM juego_activo WHERE activo = 1")
    juego = cursor.fetchone()
    
    conn.close()
    return juego

def finalizar_juego():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("UPDATE juego_activo SET activo = 0 WHERE id = 1")
    conn.commit()
    conn.close()

# ----------------- INICIALIZAR SESSION STATE -----------------
def init_session_state():
    if "pantalla" not in st.session_state:
        st.session_state.pantalla = None
    
    # Obtener estado del juego de la base de datos
    juego = obtener_estado_juego()
    
    if juego:
        st.session_state.problema = juego[0]
        st.session_state.duracion = juego[1]
        st.session_state.tiempo_inicio = datetime.strptime(juego[2], "%Y-%m-%d %H:%M:%S.%f") if isinstance(juego[2], str) else juego[2]
    else:
        st.session_state.problema = ""
        st.session_state.duracion = 5
        st.session_state.tiempo_inicio = None

# ----------------- PANTALLA DE INICIO -----------------
def mostrar_inicio():
    st.title("🏆 Juego de Programación Competitiva")
    
    st.markdown("""
        <style>
            .big-font {
                font-size:18px !important;
            }
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
            .locked {
                color: #ff4b4b;
                font-weight: bold;
            }
        </style>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👨‍🏫 Modo Docente", key="docente_btn", help="Configurar el juego"):
            st.session_state.pantalla = "docente"
    with col2:
        if st.button("👩‍🎓 Modo Estudiante", key="estudiante_btn", help="Participar en el juego"):
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
            tiempo = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f") if isinstance(timestamp, str) else timestamp
            tiempo_str = tiempo.strftime("%H:%M:%S")
            
            html += f"""
            <tr>
                <td>{i}º</td>
                <td>{nombre}</td>
                <td>{tiempo_str}</td>
            </tr>
            """
            
            if i >= MAX_JUGADORES:
                break
        
        html += "</table>"
        st.markdown(html, unsafe_allow_html=True)

# ----------------- MODO DOCENTE -----------------
def modo_docente():
    st.header("👨‍🏫 Panel del Docente")
    
    tab1, tab2 = st.tabs(["⚙️ Configurar Juego", "📊 Resultados"])
    
    with tab1:
        st.subheader("Configuración del Juego")
        
        enunciado = st.text_area(
            "Enunciado del problema", 
            st.session_state.problema, 
            height=150,
            placeholder="Describa el problema de programación..."
        )
        
        duracion = st.slider(
            "⏳ Duración (minutos)", 
            1, 120, 
            st.session_state.duracion
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🟢 Iniciar Juego", type="primary"):
                if not enunciado.strip():
                    st.error("Debe ingresar un enunciado para el problema.")
                else:
                    iniciar_juego(enunciado, duracion)
                    st.session_state.problema = enunciado
                    st.session_state.duracion = duracion
                    st.session_state.tiempo_inicio = datetime.now()
                    st.success("✅ Juego iniciado correctamente!")
                    st.balloons()
        
        with col2:
            if st.button("⏹ Detener Juego"):
                finalizar_juego()
                st.session_state.tiempo_inicio = None
                st.success("Juego detenido")
                st.rerun()
    
    with tab2:
        st.subheader("Resultados en Tiempo Real")
        
        if st.session_state.tiempo_inicio:
            tiempo_restante = (st.session_state.tiempo_inicio + timedelta(minutes=st.session_state.duracion)) - datetime.now()
            
            if tiempo_restante.total_seconds() > 0:
                st.metric("⏳ Tiempo restante", value=str(tiempo_restante).split(".")[0])
            else:
                st.error("⌛ El tiempo ha finalizado")
        
        resultados = obtener_resultados()
        if resultados:
            df = pd.DataFrame(resultados, columns=["Nombre", "Fecha/Hora"])
            df["Posición"] = range(1, len(df)+1)
            st.dataframe(df[["Posición", "Nombre", "Fecha/Hora"]], hide_index=True)
        else:
            st.info("No hay participantes aún.")

# ----------------- MODO ESTUDIANTE -----------------
def modo_estudiante():
    st.header("👩‍🎓 Modo Competidor")
    
    juego = obtener_estado_juego()
    
    if not juego or not juego[2]:  # Si no hay juego activo
        st.warning("⌛ Esperando a que el docente inicie el juego...")
        st.image("https://via.placeholder.com/600x200?text=Esperando+inicio+del+juego", use_column_width=True)
        return
    
    # Actualizar estado desde la base de datos
    st.session_state.problema = juego[0]
    st.session_state.duracion = juego[1]
    st.session_state.tiempo_inicio = datetime.strptime(juego[2], "%Y-%m-%d %H:%M:%S.%f") if isinstance(juego[2], str) else juego[2]
    
    st.subheader("📋 Enunciado del Problema")
    st.markdown(f"```\n{st.session_state.problema}\n```")
    
    # Mostrar tiempo restante
    tiempo_restante = (st.session_state.tiempo_inicio + timedelta(minutes=st.session_state.duracion)) - datetime.now()
    
    if tiempo_restante.total_seconds() > 0:
        st.metric("⏳ Tiempo restante", value=str(tiempo_restante).split(".")[0])
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
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("❌ Ya se han registrado los 3 primeros participantes")

    # Mostrar podio actual
    if resultados:
        st.subheader("🏆 Podio Actual")
        
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
            tiempo = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f") if isinstance(timestamp, str) else timestamp
            tiempo_str = tiempo.strftime("%H:%M:%S")
            
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

# ----------------- APLICACIÓN PRINCIPAL -----------------
def main():
    init_db()
    init_session_state()
    
    if st.session_state.pantalla is None:
        mostrar_inicio()
    elif st.session_state.pantalla == "docente":
        modo_docente()
    elif st.session_state.pantalla == "estudiante":
        modo_estudiante()

if __name__ == "__main__":
    main()
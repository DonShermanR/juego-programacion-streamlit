import streamlit as st
import sqlite3
import time
from datetime import datetime, timedelta
import pandas as pd
import re

# ----------------- CONSTANTES -----------------
MAX_JUGADORES = 3
DB_NAME = "resultados.db"

# ----------------- FUNCIONES DE SEGURIDAD -----------------
def sanitize_input(text):
    """Limpia el texto para evitar problemas con SQL"""
    if text is None:
        return ""
    return re.sub(r'[#;\\\'"\-]', '', str(text))

def format_timedelta(td):
    """Formatea un timedelta a HH:MM:SS"""
    if td is None:
        return "00:00:00"
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

# ----------------- FUNCIONES DE BASE DE DATOS -----------------
def init_db():
    """Inicializa la base de datos con las tablas necesarias"""
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
            tiempo_inicio TEXT,
            activo BOOLEAN DEFAULT 0
        )
    """)
    
    conn.commit()
    conn.close()

def insertar_resultado(nombre):
    """Inserta un nuevo resultado en la base de datos"""
    nombre_limpio = sanitize_input(nombre)
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT COUNT(*) FROM resultados")
        count = cursor.fetchone()[0]
        
        if count < MAX_JUGADORES:
            cursor.execute(
                "INSERT INTO resultados (nombre) VALUES (?)",
                (nombre_limpio,)
            )
            conn.commit()
            return True
        return False
    except sqlite3.Error as e:
        st.error(f"Error de base de datos: {e}")
        return False
    finally:
        conn.close()

def obtener_resultados():
    """Obtiene los resultados de la base de datos"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT nombre, timestamp 
            FROM resultados 
            ORDER BY timestamp ASC 
            LIMIT ?
        """, (MAX_JUGADORES,))
        
        return cursor.fetchall()
    except sqlite3.Error as e:
        st.error(f"Error al obtener resultados: {e}")
        return []
    finally:
        conn.close()

def reiniciar_resultados():
    """Elimina todos los resultados de la base de datos"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM resultados")
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"Error al reiniciar resultados: {e}")
    finally:
        conn.close()

def iniciar_juego(enunciado, duracion):
    """Inicia un nuevo juego en la base de datos"""
    enunciado_limpio = sanitize_input(enunciado)
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        tiempo_inicio_iso = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT OR REPLACE INTO juego_activo 
            (id, enunciado, duracion, tiempo_inicio, activo)
            VALUES (1, ?, ?, ?, 1)
        """, (enunciado_limpio, duracion, tiempo_inicio_iso))
        
        conn.commit()
        reiniciar_resultados()
        return True
    except sqlite3.Error as e:
        st.error(f"Error al iniciar juego: {e}")
        return False
    finally:
        conn.close()

def obtener_estado_juego():
    """Obtiene el estado actual del juego desde la base de datos"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT enunciado, duracion, tiempo_inicio FROM juego_activo WHERE activo = 1")
        juego = cursor.fetchone()
        
        if juego:
            enunciado, duracion, tiempo_inicio_str = juego
            try:
                tiempo_inicio = datetime.fromisoformat(tiempo_inicio_str)
                return (enunciado, duracion, tiempo_inicio)
            except ValueError:
                st.error("Formato de fecha inválido en la base de datos")
                return None
        return None
    except sqlite3.Error as e:
        st.error(f"Error al obtener estado del juego: {e}")
        return None
    finally:
        conn.close()

def finalizar_juego():
    """Finaliza el juego actual en la base de datos"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        cursor.execute("UPDATE juego_activo SET activo = 0 WHERE id = 1")
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Error al finalizar juego: {e}")
        return False
    finally:
        conn.close()

# ----------------- PANTALLAS DE LA APLICACIÓN -----------------
def mostrar_inicio():
    """Muestra la pantalla de inicio de la aplicación"""
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
    
    resultados = obtener_resultados()
    if resultados:
        st.subheader("🏅 Podio Actual")
        
        df = pd.DataFrame([
            {
                "Posición": f"{'🥇' if i==1 else '🥈' if i==2 else '🥉'} {i}º",
                "Nombre": nombre,
                "Hora": datetime.fromisoformat(timestamp).strftime("%H:%M:%S") if isinstance(timestamp, str) else timestamp.strftime("%H:%M:%S")
            }
            for i, (nombre, timestamp) in enumerate(resultados, start=1)
        ])
        
        st.dataframe(df, hide_index=True, use_container_width=True)

def modo_docente():
    """Muestra el panel de control del docente"""
    st.header("👨‍🏫 Panel del Docente")
    
    tab1, tab2 = st.tabs(["⚙️ Configurar Juego", "📊 Resultados"])
    
    with tab1:
        st.subheader("Configuración del Juego")
        
        enunciado = st.text_area(
            "Enunciado del problema", 
            st.session_state.get("problema", ""), 
            height=150,
            placeholder="Describa el problema de programación..."
        )
        
        duracion = st.slider(
            "⏳ Duración (minutos)", 
            1, 120, 
            st.session_state.get("duracion", 5)
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🟢 Iniciar Juego", type="primary"):
                if not enunciado.strip():
                    st.error("Debe ingresar un enunciado para el problema.")
                else:
                    if iniciar_juego(enunciado, duracion):
                        st.session_state.problema = enunciado
                        st.session_state.duracion = duracion
                        st.session_state.tiempo_inicio = datetime.now()
                        st.success("✅ Juego iniciado correctamente!")
                        st.balloons()
        
        with col2:
            if st.button("⏹ Detener Juego"):
                if finalizar_juego():
                    st.session_state.tiempo_inicio = None
                    st.success("Juego detenido")
                    time.sleep(1)
                    st.rerun()
    
    with tab2:
        st.subheader("Resultados en Tiempo Real")
        
        juego = obtener_estado_juego()
        if juego and juego[2]:
            tiempo_restante = (juego[2] + timedelta(minutes=juego[1])) - datetime.now()
            
            if tiempo_restante.total_seconds() > 0:
                st.metric("⏳ Tiempo restante", value=format_timedelta(tiempo_restante))
            else:
                st.error("⌛ El tiempo ha finalizado")
        
        resultados = obtener_resultados()
        if resultados:
            df = pd.DataFrame(resultados, columns=["Nombre", "Fecha/Hora"])
            df["Posición"] = range(1, len(df)+1)
            st.dataframe(df[["Posición", "Nombre", "Fecha/Hora"]], hide_index=True)
        else:
            st.info("No hay participantes aún.")

def modo_estudiante():
    """Muestra el panel del estudiante"""
    st.header("👩‍🎓 Modo Competidor")
    
    juego = obtener_estado_juego()
    
    if not juego or not juego[2]:
        st.warning("⌛ Esperando a que el docente inicie el juego...")
        return
    
    enunciado, duracion, tiempo_inicio = juego
    
    st.subheader("📋 Enunciado del Problema")
    st.markdown(f"```\n{enunciado}\n```")
    
    tiempo_restante = (tiempo_inicio + timedelta(minutes=duracion)) - datetime.now()
    
    if tiempo_restante.total_seconds() > 0:
        st.metric("⏳ Tiempo restante", value=format_timedelta(tiempo_restante))
    else:
        st.error("⌛ El tiempo se ha terminado!")
    
    resultados = obtener_resultados()
    bloqueado = len(resultados) >= MAX_JUGADORES
    
    if bloqueado:
        st.error("❌ El juego ya tiene los 3 primeros finalistas. No se aceptan más participantes.")
    else:
        with st.form("form_participante"):
            nombre = st.text_input("👤 Nombre completo", 
                                 placeholder="Ingrese su nombre completo",
                                 max_chars=50)
            
            if st.form_submit_button("🏁 Finalizar y Registrar"):
                if not nombre.strip():
                    st.error("Debe ingresar su nombre")
                elif tiempo_restante.total_seconds() <= 0:
                    st.error("El tiempo ha terminado, no se pueden enviar más soluciones")
                else:
                    if insertar_resultado(nombre.strip()):
                        st.success("🎉 ¡Registro exitoso!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Ya se han registrado los 3 primeros participantes")

    if resultados:
        st.subheader("🏆 Podio Actual")
        
        df = pd.DataFrame([
            {
                "Posición": f"{'🥇' if i==1 else '🥈' if i==2 else '🥉'} {i}º",
                "Nombre": nombre,
                "Hora": datetime.fromisoformat(timestamp).strftime("%H:%M:%S") if isinstance(timestamp, str) else timestamp.strftime("%H:%M:%S")
            }
            for i, (nombre, timestamp) in enumerate(resultados, start=1)
        ])
        
        st.dataframe(df, hide_index=True, use_container_width=True)

# ----------------- APLICACIÓN PRINCIPAL -----------------
def main():
    """Función principal de la aplicación"""
    init_db()
    
    # Inicialización del estado de la sesión
    if "pantalla" not in st.session_state:
        st.session_state.pantalla = None
    if "problema" not in st.session_state:
        st.session_state.problema = ""
    if "duracion" not in st.session_state:
        st.session_state.duracion = 5
    if "tiempo_inicio" not in st.session_state:
        st.session_state.tiempo_inicio = None
    
    # Navegación entre pantallas
    if st.session_state.pantalla is None:
        mostrar_inicio()
    elif st.session_state.pantalla == "docente":
        modo_docente()
    elif st.session_state.pantalla == "estudiante":
        modo_estudiante()

if __name__ == "__main__":
    main()
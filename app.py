import streamlit as st
import sqlite3
import time
from datetime import datetime, timedelta
import hashlib
import pandas as pd

# ----------------- CONSTANTES -----------------
MAX_JUGADORES = 5
DB_NAME = "resultados.db"

# ----------------- INICIALIZAR BASE DE DATOS MEJORADA -----------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Tabla de resultados
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resultados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            solucion TEXT,
            correcto BOOLEAN DEFAULT 0,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabla de problemas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS problemas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            enunciado TEXT NOT NULL,
            solucion_hash TEXT NOT NULL,
            duracion INTEGER NOT NULL,
            activo BOOLEAN DEFAULT 0,
            fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

# ----------------- FUNCIONES DE BASE DE DATOS MEJORADAS -----------------
def insertar_resultado(nombre, solucion="", correcto=False):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM resultados")
    count = cursor.fetchone()[0]
    
    if count < MAX_JUGADORES:
        cursor.execute(
            "INSERT INTO resultados (nombre, solucion, correcto) VALUES (?, ?, ?)",
            (nombre, solucion, correcto)
        )
        conn.commit()
    
    conn.close()

def obtener_resultados():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT nombre, solucion, correcto, timestamp 
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

def guardar_problema(enunciado, solucion_hash, duracion):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Desactivar todos los problemas anteriores
    cursor.execute("UPDATE problemas SET activo = 0")
    
    # Insertar nuevo problema activo
    cursor.execute(
        "INSERT INTO problemas (enunciado, solucion_hash, duracion, activo) VALUES (?, ?, ?, 1)",
        (enunciado, solucion_hash, duracion)
    )
    
    conn.commit()
    conn.close()

def obtener_problema_activo():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT enunciado, solucion_hash, duracion FROM problemas WHERE activo = 1")
    problema = cursor.fetchone()
    
    conn.close()
    return problema

def hash_solucion(solucion):
    return hashlib.sha256(solucion.encode()).hexdigest()

# ----------------- INICIALIZAR SESSION STATE MEJORADO -----------------
def init_session_state():
    if "pantalla" not in st.session_state:
        st.session_state.pantalla = None
    
    if "problema" not in st.session_state:
        problema = obtener_problema_activo()
        if problema:
            st.session_state.problema = problema[0]
            st.session_state.solucion_hash = problema[1]
            st.session_state.duracion = problema[2]
        else:
            st.session_state.problema = ""
            st.session_state.solucion_hash = ""
            st.session_state.duracion = 5
    
    if "tiempo_inicio" not in st.session_state:
        st.session_state.tiempo_inicio = None
    
    if "mostrar_solucion" not in st.session_state:
        st.session_state.mostrar_solucion = False

# ----------------- PANTALLA DE INICIO MEJORADA -----------------
def mostrar_inicio():
    st.title("🧠 Juego de Programación Competitiva")
    st.markdown("""
        <style>
            .big-button {
                padding: 20px;
                text-align: center;
                font-size: 20px;
                margin: 10px 0;
            }
            .result-table {
                width: 100%;
                border-collapse: collapse;
            }
            .result-table th, .result-table td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }
            .result-table tr:nth-child(even) {
                background-color: #f2f2f2;
            }
        </style>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👨‍🏫 Modo Docente", key="docente_btn", help="Acceso para configurar el juego"):
            st.session_state.pantalla = "docente"
    with col2:
        if st.button("👩‍🎓 Modo Estudiante", key="estudiante_btn", help="Acceso para participar en el juego"):
            st.session_state.pantalla = "estudiante"
    
    # Mostrar últimos resultados si existen
    resultados = obtener_resultados()
    if resultados:
        st.subheader("🏆 Últimos Resultados")
        df = pd.DataFrame(resultados, columns=["Nombre", "Solución", "Correcto", "Fecha/Hora"])
        df["Correcto"] = df["Correcto"].apply(lambda x: "✅" if x else "❌")
        st.dataframe(df[["Nombre", "Correcto", "Fecha/Hora"]], hide_index=True)

# ----------------- MODO DOCENTE MEJORADO -----------------
def modo_docente():
    st.header("👨‍🏫 Panel del Docente")
    
    tab1, tab2 = st.tabs(["📝 Configurar Juego", "📊 Resultados"])
    
    with tab1:
        st.subheader("Configuración del Problema")
        
        enunciado = st.text_area(
            "Enunciado del problema", 
            st.session_state.problema, 
            height=150,
            placeholder="Describa el problema de programación que los estudiantes deben resolver..."
        )
        
        solucion = st.text_area(
            "Solución esperada (solo para verificación)", 
            height=150,
            placeholder="Escriba la solución correcta para validar las respuestas..."
        )
        
        col1, col2 = st.columns(2)
        with col1:
            duracion = st.slider(
                "⏳ Duración (minutos)", 
                1, 60, 
                st.session_state.duracion if "duracion" in st.session_state else 5
            )
        
        with col2:
            st.write("")
            st.write("")
            iniciar = st.button("🟢 Iniciar Juego", type="primary")
        
        if iniciar:
            if not enunciado.strip():
                st.error("Debe ingresar un enunciado para el problema.")
            elif not solucion.strip():
                st.error("Debe proporcionar una solución para verificar las respuestas.")
            else:
                # Guardar problema en la base de datos
                solucion_hash = hash_solucion(solucion)
                guardar_problema(enunciado, solucion_hash, duracion)
                
                # Actualizar estado
                st.session_state.problema = enunciado
                st.session_state.solucion_hash = solucion_hash
                st.session_state.duracion = duracion
                st.session_state.tiempo_inicio = datetime.now()
                reiniciar_resultados()
                
                st.success("✅ Juego iniciado correctamente!")
                st.balloons()
    
    with tab2:
        st.subheader("Resultados del Juego")
        
        if st.session_state.tiempo_inicio:
            tiempo_restante = (st.session_state.tiempo_inicio + timedelta(minutes=st.session_state.duracion)) - datetime.now()
            
            if tiempo_restante.total_seconds() > 0:
                st.markdown(f"### ⏳ Tiempo restante: `{str(tiempo_restante).split('.')[0]}`")
                time.sleep(1)
                st.rerun()
            else:
                st.error("⏰ El tiempo ha finalizado.")
        
        resultados = obtener_resultados()
        if resultados:
            st.subheader("🏅 Ranking de Participantes")
            
            for i, (nombre, solucion, correcto, timestamp) in enumerate(resultados, start=1):
                emoji = "✅" if correcto else "❌"
                st.write(f"{i}. {emoji} {nombre} - {timestamp}")
                
                if st.session_state.mostrar_solucion:
                    with st.expander(f"Ver solución de {nombre}"):
                        st.code(solucion, language="python")
        else:
            st.info("No hay resultados aún.")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Reiniciar Juego"):
                reiniciar_resultados()
                st.session_state.tiempo_inicio = None
                st.rerun()
        
        with col2:
            st.session_state.mostrar_solucion = st.toggle("Mostrar soluciones")

# ----------------- MODO ESTUDIANTE MEJORADO -----------------
def modo_estudiante():
    st.header("👩‍🎓 Modo Estudiante")
    
    if not st.session_state.problema or not st.session_state.tiempo_inicio:
        st.warning("Esperando a que el docente inicie el juego...")
        st.image("https://via.placeholder.com/600x200?text=Esperando+inicio+del+juego", use_column_width=True)
        return
    
    st.subheader("📖 Enunciado del Problema")
    st.markdown(f"```\n{st.session_state.problema}\n```")
    
    # Mostrar tiempo restante
    tiempo_restante = (st.session_state.tiempo_inicio + timedelta(minutes=st.session_state.duracion)) - datetime.now()
    
    if tiempo_restante.total_seconds() > 0:
        st.metric("⏳ Tiempo restante", value=str(tiempo_restante).split(".")[0])
    else:
        st.error("⏰ El tiempo se ha terminado!")
    
    with st.form("form_solucion"):
        nombre = st.text_input("👤 Nombre completo", placeholder="Ingrese su nombre completo")
        
        solucion = st.text_area(
            "💻 Su solución", 
            height=300,
            placeholder="Escriba aquí su código solución...",
            help="Puede escribir código en cualquier lenguaje, pero asegúrese de que resuelva el problema planteado."
        )
        
        enviado = st.form_submit_button("🚀 Enviar solución")
        
        if enviado:
            if not nombre.strip():
                st.error("Debe ingresar su nombre")
            elif not solucion.strip():
                st.error("Debe escribir una solución")
            elif tiempo_restante.total_seconds() <= 0:
                st.error("El tiempo ha terminado, no se pueden enviar más soluciones")
            else:
                # Verificar si la solución es correcta
                solucion_correcta = hash_solucion(solucion) == st.session_state.solucion_hash
                insertar_resultado(nombre, solucion, solucion_correcta)
                
                if solucion_correcta:
                    st.success("🎉 ¡Solución correcta! Bien hecho!")
                    st.balloons()
                else:
                    st.warning("⚠️ Solución enviada, pero no coincide con la solución esperada.")
                
                st.rerun()

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
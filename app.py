import streamlit as st
import sqlite3
import time
from datetime import datetime, timedelta

# Inicializar la base de datos SQLite
def init_db():
    conn = sqlite3.connect("resultados.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resultados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

# Insertar un resultado
def insertar_resultado(nombre):
    conn = sqlite3.connect("resultados.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM resultados")
    count = cursor.fetchone()[0]
    if count < 3:  # Solo se aceptan 3 resultados
        cursor.execute("INSERT INTO resultados (nombre) VALUES (?)", (nombre,))
        conn.commit()
    conn.close()

# Obtener resultados
def obtener_resultados():
    conn = sqlite3.connect("resultados.db")
    cursor = conn.cursor()
    cursor.execute("SELECT nombre, timestamp FROM resultados ORDER BY timestamp ASC LIMIT 3")
    resultados = cursor.fetchall()
    conn.close()
    return resultados

# Resetear base de datos
def reiniciar_resultados():
    conn = sqlite3.connect("resultados.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM resultados")
    conn.commit()
    conn.close()

# Inicializar session_state
if "pantalla" not in st.session_state:
    st.session_state.pantalla = None
if "problema" not in st.session_state:
    st.session_state.problema = ""
if "tiempo_inicio" not in st.session_state:
    st.session_state.tiempo_inicio = None
if "duracion" not in st.session_state:
    st.session_state.duracion = 5  # duración por defecto

init_db()

# ---------------------- PANTALLA DE INICIO -------------------------
st.title("🧠 Juego de Programación")

if st.session_state.pantalla is None:
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👨‍🏫 Docente"):
            st.session_state.pantalla = "docente"
    with col2:
        if st.button("👩‍🎓 Estudiante"):
            st.session_state.pantalla = "estudiante"

# ---------------------- DOCENTE -------------------------
elif st.session_state.pantalla == "docente":
    st.header("👨‍🏫 Modo Docente")

    st.subheader("📝 Ingrese el enunciado del problema")
    st.session_state.problema = st.text_area("Problema", st.session_state.problema, height=100)

    col1, col2 = st.columns(2)
    with col1:
        st.session_state.duracion = st.slider("⏳ Tiempo de resolución (minutos)", 1, 30, st.session_state.duracion)
    with col2:
        if st.button("🟢 Iniciar juego"):
            st.session_state.tiempo_inicio = datetime.now()
            reiniciar_resultados()
            st.success("✅ Juego iniciado")

    if st.session_state.tiempo_inicio:
        tiempo_restante = (st.session_state.tiempo_inicio + timedelta(minutes=st.session_state.duracion)) - datetime.now()
        if tiempo_restante.total_seconds() > 0:
            st.info(f"⏱ Tiempo restante: {str(tiempo_restante).split('.')[0]}")
        else:
            st.warning("⏳ Tiempo finalizado")

    st.subheader("🏁 Resultados:")
    resultados = obtener_resultados()
    for i, (nombre, timestamp) in enumerate(resultados, start=1):
        st.success(f"{i}. {nombre} ({timestamp})")

    if st.button("🔄 Reiniciar juego"):
        reiniciar_resultados()
        st.session_state.tiempo_inicio = None
        st.session_state.problema = ""
        st.session_state.duracion = 5
        st.session_state.pantalla = None
        st.rerun()

# ---------------------- ESTUDIANTE -------------------------
elif st.session_state.pantalla == "estudiante":
    st.header("👩‍🎓 Modo Estudiante")

    if st.session_state.problema == "" or st.session_state.tiempo_inicio is None:
        st.warning("⛔ Aún no se ha iniciado ningún juego.")
        if st.button("⬅️ Volver"):
            st.session_state.pantalla = None
            st.rerun()
    else:
        st.subheader("📘 Problema")
        st.markdown(f"### {st.session_state.problema}")

        tiempo_restante = (st.session_state.tiempo_inicio + timedelta(minutes=st.session_state.duracion)) - datetime.now()
        if tiempo_restante.total_seconds() > 0:
            st.info(f"⏱ Tiempo restante: {str(tiempo_restante).split('.')[0]}")
        else:
            st.error("⛔ El tiempo se ha terminado")

        nombre = st.text_input("✍️ Escriba su nombre y apellido")

        if st.button("✅ Terminé"):
            if nombre.strip() == "":
                st.warning("⚠️ Debe ingresar su nombre.")
            elif tiempo_restante.total_seconds() <= 0:
                st.error("⚠️ Tiempo terminado. No se puede registrar.")
            else:
                insertar_resultado(nombre.strip())
                st.success("🎉 ¡Respuesta registrada!")
                st.rerun()

        if st.button("⬅️ Volver"):
            st.session_state.pantalla = None
            st.rerun()

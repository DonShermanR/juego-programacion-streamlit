import streamlit as st
import time

# Inicialización segura del estado de sesión
if "posiciones" not in st.session_state:
    st.session_state["posiciones"] = []

if "problema" not in st.session_state:
    st.session_state["problema"] = ""

if "start_time" not in st.session_state:
    st.session_state["start_time"] = None

# Función para reiniciar el juego
def reiniciar_juego():
    st.session_state["posiciones"] = []
    st.session_state["problema"] = ""
    st.session_state["start_time"] = None
    st.experimental_rerun()

# Título principal
st.title("Juego de Programación 🎯")

# Sección del problema
st.subheader("🧩 Enunciado del problema")

# Text area para ingresar o mostrar el problema
problema = st.text_area("Escribe el problema aquí:", value=st.session_state["problema"], height=150, key="problema_area")

# Botón para iniciar el problema
if st.button("🚀 Iniciar ejercicio"):
    st.session_state["problema"] = problema
    st.session_state["start_time"] = time.time()
    st.success("¡Ejercicio iniciado!")

# Mostrar enunciado si ya fue definido
if st.session_state["problema"]:
    st.info(f"📝 Enunciado actual:\n\n{st.session_state['problema']}")

# Temporizador (solo si se inició el ejercicio)
if st.session_state["start_time"]:
    tiempo_transcurrido = int(time.time() - st.session_state["start_time"])
    minutos = tiempo_transcurrido // 60
    segundos = tiempo_transcurrido % 60
    st.markdown(f"⏱️ Tiempo transcurrido: **{minutos:02d}:{segundos:02d}**")

st.divider()

# Ingreso del nombre del estudiante
st.subheader("✅ Marca cuando termines")
nombre = st.text_input("Tu nombre:", max_chars=50)

# Lista de posiciones
st.subheader("🏆 Posiciones actuales:")
for i, participante in enumerate(st.session_state["posiciones"]):
    col1, col2 = st.columns([4, 1])
    with col1:
        st.write(f"{i+1}. {participante}")
    with col2:
        if st.button("❌", key=f"del_{i}"):
            st.session_state["posiciones"].pop(i)
            st.experimental_rerun()

# Botón para registrar finalización del estudiante
if st.button("¡Terminé! ✅"):
    if not nombre:
        st.warning("Por favor, escribe tu nombre antes de presionar el botón.")
    elif nombre in st.session_state["posiciones"]:
        st.info("Ya estás en la lista.")
    elif len(st.session_state["posiciones"]) >= 5:
        st.error("Ya hay 5 estudiantes en la lista.")
    else:
        st.session_state["posiciones"].append(nombre)
        st.success(f"¡Registrado, {nombre}! Estás en la posición #{len(st.session_state['posiciones'])}")

# Botón para reiniciar todo
st.divider()
if st.button("🔁 Reiniciar todo (nuevo problema)"):
    reiniciar_juego()

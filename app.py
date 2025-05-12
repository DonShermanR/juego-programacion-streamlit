import streamlit as st
import sqlite3
import time
from datetime import datetime, timedelta
import pandas as pd
import re

# ----------------- CONSTANTES -----------------
MAX_JUGADORES = 3
DB_NAME = "resultados.db"

# ----------------- FUNCIONES DE SEGURIDAD SQL -----------------
def sanitize_input(text):
    """Limpia el texto para evitar problemas con SQL"""
    if text is None:
        return ""
    # Eliminar caracteres problemáticos
    return re.sub(r'[#;\\-]', '', str(text))

# ----------------- INICIALIZAR BASE DE DATOS -----------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Usar parámetros en lugar de concatenar SQL
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

# ----------------- FUNCIONES DE BASE DE DATOS SEGURAS -----------------
def insertar_resultado(nombre):
    """Versión segura de insertar resultado"""
    nombre_limpio = sanitize_input(nombre)
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        # Usar parámetros para evitar inyección SQL
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
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        # Usar parámetros en lugar de f-strings
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

# ----------------- MODO ESTUDIANTE (parte modificada) -----------------
def modo_estudiante():
    st.header("👩‍🎓 Modo Competidor")
    
    juego = obtener_estado_juego()
    
    if not juego or not juego[2]:
        st.warning("⌛ Esperando a que el docente inicie el juego...")
        return
    
    with st.form("form_participante"):
        nombre = st.text_input("👤 Nombre completo", 
                             placeholder="Ingrese su nombre completo",
                             max_chars=50)  # Limitar longitud
        
        if st.form_submit_button("🏁 Finalizar y Registrar"):
            if not nombre.strip():
                st.error("Debe ingresar su nombre")
            else:
                # Insertar nombre sanitizado
                if insertar_resultado(nombre.strip()):
                    st.success("¡Registro exitoso!")
                    st.rerun()
                else:
                    st.error("No se pudo registrar. Intente nuevamente.")

# ----------------- APLICACIÓN PRINCIPAL -----------------
def main():
    init_db()
    
    # Configuración inicial segura
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
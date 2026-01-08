import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import os

# Configuración básica
st.set_page_config(page_title="CSED Rescate", layout="wide")

# Estilo rápido
st.markdown("<style>.stApp {background-color: #f0f2f6;}</style>", unsafe_allow_html=True)

# --- CARGA DE DOCUMENTOS ---
@st.cache_resource
def cargar_documentos():
    texto_total = ""
    archivos = [f for f in os.listdir('.') if f.lower().endswith('.pdf')]
    if not archivos:
        return "No se encontraron archivos PDF.", 0
    
    for f in archivos:
        try:
            reader = PdfReader(f)
            # Solo leemos las primeras 10 páginas de cada uno para no saturar la memoria
            for i in range(min(len(reader.pages), 10)):
                texto_total += f"\n ORIGEN {f}: " + reader.pages[i].extract_text()
        except:
            continue
    return texto_total, len(archivos)

contexto, num_docs = cargar_documentos()

# --- INTERFAZ ---
st.title("🎓 Asistente CSED - Efrén Luis Pérez")
st.sidebar.header("Configuración Crítica")

# API KEY
api_key = st.sidebar.text_input("🔑 Pega aquí tu API KEY (sin comillas)", type="password")

if st.sidebar.button("🗑️ Limpiar Memoria"):
    st.cache_resource.clear()
    st.rerun()

st.sidebar.write(f"📚 Documentos cargados: {num_docs}")

# --- LÓGICA DE INTELIGENCIA ---
if api_key:
    try:
        genai.configure(api_key=api_key)
        # Probamos el modelo más básico y universal para evitar el error 404
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        pregunta = st.chat_input("Escribe aquí tu duda (sobre fechas, alumnos o correcciones)...")
        
        if pregunta:
            with st.spinner("Consultando con la normativa CSED..."):
                prompt_maestro = f"""
                Eres Efrén Luis Pérez, tutor del CSED. 
                Usa este contexto de los archivos subidos para responder:
                {contexto[:30000]}
                
                Pregunta del usuario: {pregunta}
                """
                response = model.generate_content(prompt_maestro)
                st.chat_message("assistant").write(response.text)
                
    except Exception as e:
        error_str = str(e)
        if "404" in error_str:
            st.error("❌ Error 404: Tu cuenta de Google aún no tiene acceso al modelo 1.5 Pro. Prueba a cambiar 'gemini-1.5-pro' por 'gemini-1.0-pro' en el código.")
        elif "API_KEY_INVALID" in error_str:
            st.error("❌ Clave API no válida. Asegúrate de que es la de 'Credenciales' de Google Cloud.")
        else:
            st.error(f"Ocurrió un error: {error_str}")
else:
    st.info("Introduce tu API Key en la izquierda para empezar.")
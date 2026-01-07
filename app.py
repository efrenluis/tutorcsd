import streamlit as st
import pandas as pd
import google.generativeai as genai
from pypdf import PdfReader
import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="CSED Manager | Tutor Pro", layout="wide")

# --- CONOCIMIENTO INCRUSTADO (Prompts de Sistema por Temática) ---
SYS_ACADEMICO = "Eres un experto académico del CSED. Responde dudas sobre temario, rúbricas y criterios de evaluación. Fuente: Guías Didácticas."
SYS_TUTORIA = "Eres un orientador pedagógico. Responde sobre seguimiento, alumnos inactivos, motivación y conflictos. Fuente: Manual Tutor."
SYS_TECNICO = "Eres soporte técnico Moodle. Responde sobre Turnitin, acceso, bloqueos y configuración. Fuente: Manuales Técnicos."
SYS_GENERAL = "Eres el asistente administrativo del curso. Coordinador: Víctor Martínez. Examen: 8 Feb. Responde sobre actas y plazos."

# --- ESTADO ---
if 'students' not in st.session_state: st.session_state.students = pd.DataFrame(columns=["Nombre", "Tareas", "Riesgo", "Plagio", "IA%", "Sim%", "Notas"])
if 'chat_history' not in st.session_state: st.session_state.chat_history = []

# --- SIDEBAR ---
with st.sidebar:
    st.title("CSED Manager")
    api_key = st.text_input("🔑 API Key", type="password")
    if api_key: genai.configure(api_key=api_key)
    page = st.radio("Menú", ["Dashboard", "CRM Alumnos", "Corrector IA", "Chats Temáticos", "Actas", "Diario"])

# --- FUNCIONES ---
def get_ai(prompt):
    if not api_key: return "⚠️ Falta API Key"
    try: return genai.GenerativeModel('gemini-1.5-flash').generate_content(prompt).text
    except Exception as e: return f"Error: {e}"

# --- PÁGINAS ---
if page == "Dashboard":
    st.title("Panel de Control")
    st.info(f"Tutor: Efrén Luis Pérez | Coord: Víctor Martínez | Examen: 8 Feb")
    # Métricas...

elif page == "CRM Alumnos":
    st.title("Gestión de Alumnos")
    with st.expander("📥 Importar Lista (Excel)"):
        txt = st.text_area("Pega nombres aquí")
        if st.button("Procesar"):
            # Lógica de importación...
            pass
    
    st.data_editor(st.session_state.students, num_rows="dynamic", use_container_width=True)

elif page == "Chats Temáticos":
    st.title("💬 Consultas Especializadas")
    
    # SELECTOR DE TEMÁTICA
    tematica = st.selectbox("Selecciona el experto:", ["🎓 Académico", "🤝 Tutoría", "💻 Técnico", "🌐 General"])
    
    # Asignar System Prompt según selección
    sys_prompt = ""
    if "Académico" in tematica: sys_prompt = SYS_ACADEMICO
    elif "Tutoría" in tematica: sys_prompt = SYS_TUTORIA
    elif "Técnico" in tematica: sys_prompt = SYS_TECNICO
    else: sys_prompt = SYS_GENERAL
    
    st.caption(f"Contexto activo: {sys_prompt}")
    
    q = st.chat_input("Escribe tu duda...")
    if q:
        final_prompt = f"{sys_prompt}\n\nPREGUNTA USUARIO: {q}"
        ans = get_ai(final_prompt)
        st.write(ans)

# ... (Resto de módulos Corrector y Actas igual que versiones anteriores) ...
# ---------------------------------------------------------
# CSED MANAGER PRO - LAUNCHER DE EMERGENCIA
# Copia esto en Google Colab y dale al Play.
# ---------------------------------------------------------

import os
# 1. INSTALACIÓN DE LIBRERÍAS
print("⏳ Instalando dependencias (1 min)...")
os.system("pip install streamlit google-generativeai pypdf pandas pyngrok")

# 2. CÓDIGO DE LA APP (APP.PY)
code = """
import streamlit as st
import pandas as pd
import google.generativeai as genai
from pypdf import PdfReader
import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="CSED Manager Pro", page_icon="🎓", layout="wide")

# --- ESTILOS CSS ---
st.markdown('''
<style>
    .stApp { background-color: #f8fafc; }
    h1, h2, h3 { color: #003399; font-family: sans-serif; }
    .stButton>button { background-color: #003399; color: white; border-radius: 8px; }
    .metric-card { background: white; padding: 15px; border-radius: 10px; border-left: 5px solid #003399; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
</style>
''', unsafe_allow_html=True)

# --- ESTADO ---
if 'students' not in st.session_state:
    st.session_state.students = pd.DataFrame(columns=["Nombre", "Tareas_Hechas", "Riesgo", "Plagio", "IA_Pct", "Sim_Pct", "Notas"])
if 'journal' not in st.session_state:
    st.session_state.journal = []

# --- DATOS FIJOS ---
COORD = "Víctor Martínez Majolero"
TUTOR = "Efrén Luis Pérez"
EXAMEN = "Semana del 8 de Febrero"

# --- SIDEBAR ---
with st.sidebar:
    st.title("CSED Manager")
    st.caption(f"Coord: {COORD}")
    
    api_key = st.text_input("🔑 API Key Gemini", type="password")
    if api_key: genai.configure(api_key=api_key)
    
    page = st.radio("Menú", ["Panel Principal", "Gestión Alumnos (CRM)", "Corrector IA", "Gestor Actas", "Diario"])

# --- FUNCIONES ---
def get_ai(prompt):
    if not api_key: return "⚠️ Falta API Key"
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        return model.generate_content(prompt).text
    except Exception as e: return f"Error: {e}"

def extract_pdf(file):
    reader = PdfReader(file)
    return "".join([p.extract_text() for p in reader.pages])

# --- PÁGINAS ---

# 1. PANEL
if page == "Panel Principal":
    st.header("📊 Panel de Control")
    df = st.session_state.students
    
    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="metric-card"><h3>{len(df)}</h3><p>Alumnos</p></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card" style="border-color:red"><h3>{len(df[df["Riesgo"]])}</h3><p>Riesgo</p></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card" style="border-color:orange"><h3>{len(df[df["Plagio"]])}</h3><p>Plagios</p></div>', unsafe_allow_html=True)

# 2. ALUMNOS
elif page == "Gestión Alumnos (CRM)":
    st.header("👥 Base de Datos Alumnos")
    
    with st.expander("📥 IMPORTAR LISTA (Pegar desde Excel)", expanded=len(st.session_state.students)==0):
        st.write("Pega la lista de nombres (uno por línea):")
        names_input = st.text_area("Nombres")
        if st.button("Procesar Lista"):
            names = [n.strip().upper() for n in names_input.split('\\n') if n.strip()]
            new_df = pd.DataFrame([{"Nombre": n, "Tareas_Hechas": 0, "Riesgo": False, "Plagio": False, "IA_Pct": 0, "Sim_Pct": 0, "Notas": ""} for n in names])
            st.session_state.students = pd.concat([st.session_state.students, new_df], ignore_index=True)
            st.success(f"{len(names)} alumnos importados.")
            st.rerun()
            
    hito = st.number_input("Tareas esperadas a hoy:", 5)
    
    edited = st.data_editor(
        st.session_state.students,
        column_config={
            "Riesgo": st.column_config.CheckboxColumn("⚠️ Riesgo", default=False),
            "Plagio": st.column_config.CheckboxColumn("🚫 Plagio", default=False),
            "IA_Pct": st.column_config.NumberColumn("% IA", min_value=0, max_value=100),
            "Sim_Pct": st.column_config.NumberColumn("% Sim", min_value=0, max_value=100),
            "Tareas_Hechas": st.column_config.NumberColumn("Entregas"),
        },
        use_container_width=True,
        num_rows="dynamic",
        hide_index=True
    )
    st.session_state.students = edited

# 3. CORRECTOR
elif page == "Corrector IA":
    st.header("✨ Corrector Inteligente")
    
    c1, c2 = st.columns(2)
    mode = c1.radio("Modo", ["📄 TAREA (PDF)", "💬 FORO (Texto)"])
    act = c2.selectbox("Actividad", ["T1", "T2", "T3", "T4", "T9", "T14", "Foro T1", "Foro T14"])
    tone = st.select_slider("Tono", ["Normativo", "Sándwich", "Motivador"])
    
    content = ""
    if "PDF" in mode:
        f = st.file_uploader("Sube PDF", type="pdf")
        if f: content = extract_pdf(f)
    else:
        content = st.text_area("Texto Foro", height=200)
        
    if st.button("Corregir", type="primary"):
        if not content: st.error("Falta contenido")
        else:
            with st.spinner("Procesando..."):
                p = f'''ROL: Tutor CSED ({TUTOR}). TAREA: {act}. TONO: {tone}.
                INSTRUCCIONES: 1. Tabla Notas. 2. Feedback Sándwich. 3. OBLIGATORIO: Feedback Enriquecido.
                CONTENIDO: {content[:20000]}'''
                st.markdown(get_ai(p))

# 4. ACTAS
elif page == "Gestor Actas":
    st.header("📑 Generador Actas")
    
    c1, c2, c3 = st.columns(3)
    sem = c1.text_input("Semana", "3")
    hrs = c2.number_input("Horas", 15)
    fec = c3.date_input("Fecha")
    
    if st.button("Generar Informe"):
        df = st.session_state.students
        issues = df[(df['Riesgo']) | (df['Plagio']) | (df['Notas'] != "")]
        tbl = issues.to_markdown(index=False)
        logs = "\\n".join([f"- {l['date']}: {l['text']}" for l in st.session_state.journal[-5:]])
        
        p = f'''GENERA ACTA CSED (NUEVO FORMATO).
        Coord: {COORD}. Tutor: {TUTOR}. Semana: {sem}. Horas: {hrs}.
        INCRUSTA ESTA TABLA DE ALUMNOS:
        {tbl}
        DIARIO:
        {logs}'''
        st.markdown(get_ai(p))

# 5. DIARIO
elif page == "Diario":
    st.header("📔 Diario")
    d = st.date_input("Fecha")
    t = st.text_input("Incidencia")
    if st.button("Guardar"):
        st.session_state.journal.insert(0, {"date": d, "text": t})
        st.success("Guardado")
    for l in st.session_state.journal:
        st.write(f"**{l['date']}**: {l['text']}")
"""

with open("app.py", "w") as f:
    f.write(code)

# 3. EJECUCIÓN
import urllib
print("\\n==================================================================")
print("⚠️ TU CONTRASEÑA ES:", urllib.request.urlopen('https://ipv4.icanhazip.com').read().decode('utf8').strip())
print("==================================================================\\n")
print("Haz clic en el enlace de abajo ('your url is'):")
os.system("streamlit run app.py & npx localtunnel --port 8501")
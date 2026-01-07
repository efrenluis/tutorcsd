import streamlit as st
import pandas as pd
import google.generativeai as genai
from pypdf import PdfReader
import io
import datetime

# --- CONFIGURACIÓN E IDENTIDAD VISUAL ---
st.set_page_config(
    page_title="CSED Manager Pro",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS Corporativos (Azul CSD)
st.markdown("""
<style>
    .stApp { background-color: #f8fafc; }
    .main-header { font-size: 2rem; color: #003399; font-weight: 800; margin-bottom: 1rem; }
    .sub-header { font-size: 1.2rem; color: #1e3a8a; font-weight: 600; margin-top: 1rem; }
    .card { background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 1rem; }
    .metric-value { font-size: 2rem; font-weight: bold; color: #0f172a; }
    .metric-label { font-size: 0.9rem; color: #64748b; text-transform: uppercase; font-weight: 700; }
    /* Botones */
    .stButton>button { background-color: #003399; color: white; border-radius: 6px; font-weight: 600; border: none; }
    .stButton>button:hover { background-color: #1e40af; }
</style>
""", unsafe_allow_html=True)

# --- CONSTANTES DEL CURSO ---
COORD_DEF = "Víctor Martínez Majolero"
TUTOR_DEF = "Efrén Luis Pérez"
EXAMEN_DEF = "Semana del 8 de Febrero"

# --- ESTADO (PERSISTENCIA) ---
if 'students' not in st.session_state:
    st.session_state.students = pd.DataFrame(columns=["Nombre", "Tareas", "Riesgo", "Plagio", "IA_Pct", "Sim_Pct", "Notas"])
if 'journal' not in st.session_state:
    st.session_state.journal = []

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/teacher.png", width=60)
    st.markdown("### CSED Manager V9")
    
    # API KEY
    api_key = st.text_input("🔑 API Key Gemini", type="password")
    if api_key:
        genai.configure(api_key=api_key)
        st.success("Conectado")
    else:
        st.warning("Desconectado")
        
    st.divider()
    page = st.radio("Navegación", ["Panel Principal", "Gestión Alumnos (CRM)", "Corrector IA", "Gestor de Actas", "Diario de Bitácora"])
    
    st.divider()
    st.caption(f"Coord: {COORD_DEF}\nExamen: {EXAMEN_DEF}")

# --- FUNCIONES ---
def get_ai_response(prompt):
    if not api_key: return "⚠️ Error: Falta API Key."
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        return model.generate_content(prompt).text
    except Exception as e:
        return f"Error: {e}"

def extract_pdf(file):
    reader = PdfReader(file)
    return "".join([p.extract_text() for p in reader.pages])

# --- PÁGINAS ---

# 1. DASHBOARD
if page == "Panel Principal":
    st.markdown('<div class="main-header">Panel de Control</div>', unsafe_allow_html=True)
    
    df = st.session_state.students
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="card"><div class="metric-label">Total Alumnos</div><div class="metric-value">{len(df)}</div></div>', unsafe_allow_html=True)
    with c2:
        risk = len(df[df['Riesgo']==True])
        st.markdown(f'<div class="card" style="border-left: 5px solid #ef4444;"><div class="metric-label">En Riesgo</div><div class="metric-value" style="color:#ef4444">{risk}</div></div>', unsafe_allow_html=True)
    with c3:
        plag = len(df[df['Plagio']==True])
        st.markdown(f'<div class="card" style="border-left: 5px solid #eab308;"><div class="metric-label">Plagios</div><div class="metric-value" style="color:#eab308">{plag}</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="card"><div class="metric-label">Próximo Hito</div><div class="metric-value" style="font-size:1.2rem">8 Feb<br>Examen</div></div>', unsafe_allow_html=True)

    # Accesos directos
    col_a, col_b = st.columns(2)
    with col_a:
        with st.container(border=True):
            st.markdown("### 🚀 Corrección Rápida")
            st.caption("Accede al corrector inteligente para tareas y foros.")
            if st.button("Ir al Corrector"):
                st.info("Selecciona 'Corrector IA' en el menú lateral.")
    with col_b:
        with st.container(border=True):
            st.markdown("### 📝 Nueva Entrada Diario")
            st.caption("Registra una incidencia rápida con fecha de hoy.")
            quick_note = st.text_input("Nota rápida", key="quick_n")
            if st.button("Guardar Nota"):
                st.session_state.journal.insert(0, {"date": datetime.date.today(), "text": quick_note})
                st.success("Guardado.")

# 2. ALUMNOS
elif page == "Gestión Alumnos (CRM)":
    st.markdown('<div class="main-header">Base de Datos de Alumnos</div>', unsafe_allow_html=True)
    
    # Importador
    with st.expander("📥 IMPORTAR LISTA (Copiar desde Excel)", expanded=len(st.session_state.students)==0):
        st.write("Pega la lista de nombres (uno por línea):")
        names_input = st.text_area("Nombres")
        if st.button("Procesar Lista"):
            names = [n.strip().upper() for n in names_input.split('\n') if n.strip()]
            new_df = pd.DataFrame([{"Nombre": n, "Tareas": 0, "Riesgo": False, "Plagio": False, "IA_Pct": 0, "Sim_Pct": 0, "Notas": ""} for n in names])
            st.session_state.students = pd.concat([st.session_state.students, new_df], ignore_index=True)
            st.rerun()
            
    # Edición y Ritmo
    st.markdown("### Seguimiento")
    hito = st.number_input("Tareas esperadas a fecha de hoy:", value=5, step=1)
    
    # Editor
    edited = st.data_editor(
        st.session_state.students,
        column_config={
            "Riesgo": st.column_config.CheckboxColumn("⚠️ Riesgo", default=False),
            "Plagio": st.column_config.CheckboxColumn("🚫 Plagio", default=False),
            "IA_Pct": st.column_config.NumberColumn("% IA", min_value=0, max_value=100),
            "Sim_Pct": st.column_config.NumberColumn("% Sim", min_value=0, max_value=100),
            "Tareas": st.column_config.NumberColumn("Entregas", min_value=0),
        },
        use_container_width=True,
        num_rows="dynamic",
        hide_index=True
    )
    st.session_state.students = edited

# 3. CORRECTOR
elif page == "Corrector IA":
    st.markdown('<div class="main-header">Corrector Inteligente</div>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    mode = c1.radio("Modo:", ["📄 TAREA (PDF)", "💬 FORO (Texto)"], horizontal=True)
    act = c2.selectbox("Actividad:", ["T1: Valores", "T2: Líderes", "T3: Instituciones", "T4: Ayudas", "T9: DESA", "T14: Rugby", "Foro T1", "Foro T14"])
    tone = st.select_slider("Tono:", ["Normativo", "Constructivo (Sándwich)", "Motivador"])
    
    content = ""
    if "PDF" in mode:
        f = st.file_uploader("Sube PDF", type="pdf")
        if f: content = extract_pdf(f)
    else:
        content = st.text_area("Pega el texto del foro:", height=200)
        
    if st.button("✨ CORREGIR TAREA", type="primary"):
        if not content:
            st.error("No hay contenido.")
        else:
            with st.spinner("Procesando..."):
                p = f"""ROL: Tutor CSED ({TUTOR_DEF}). TAREA: {act}. TONO: {tone}.
                INSTRUCCIONES: 1. Tabla de Notas (Rúbrica oficial). 2. Feedback Sándwich. 3. OBLIGATORIO: Feedback Enriquecido (Dato curioso/externo).
                CONTENIDO: {content[:20000]}"""
                st.markdown(get_ai_response(p))

# 4. ACTAS
elif page == "Gestor de Actas":
    st.markdown('<div class="main-header">Generador de Actas (Nuevo Formato)</div>', unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    sem = c1.text_input("Semana", "3")
    hrs = c2.number_input("Horas", 15)
    fec = c3.date_input("Fecha Acta")
    
    # Cruce de datos automático
    df = st.session_state.students
    issues = df[(df['Riesgo']) | (df['Plagio']) | (df['Notas'] != "")]
    
    st.info(f"Se incluirán automáticamente {len(issues)} alumnos con incidencias en el acta.")
    
    if st.button("📄 GENERAR INFORME"):
        with st.spinner("Redactando..."):
            tbl = issues.to_markdown(index=False)
            logs = "\n".join([f"- {l['date']}: {l['text']}" for l in st.session_state.journal[-10:]])
            
            p = f"""GENERA ACTA CSED (NUEVO FORMATO).
            Coord: {COORD_DEF}. Tutor: {TUTOR_DEF}. Semana: {sem}. Horas: {hrs}. Fecha: {fec}.
            
            DATOS ALUMNOS (Incrustar tabla tal cual):
            {tbl}
            
            ANÁLISIS DIARIO:
            {logs}
            
            Formato: Markdown profesional.
            """
            st.markdown(get_ai_response(p))

# 5. DIARIO
elif page == "Diario de Bitácora":
    st.markdown('<div class="main-header">Diario del Tutor</div>', unsafe_allow_html=True)
    
    c1, c2 = st.columns([1,3])
    d = c1.date_input("Fecha Suceso")
    t = c2.text_input("Incidencia")
    
    if st.button("Añadir"):
        st.session_state.journal.insert(0, {"date": d, "text": t})
        st.success("Guardado")
        
    st.subheader("Historial")
    for l in st.session_state.journal:
        st.markdown(f"**{l['date']}**: {l['text']}")
        st.divider()
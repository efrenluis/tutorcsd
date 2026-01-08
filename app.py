import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import os

# ==============================================================================
# 1. CONFIGURACIÓN DE LA PÁGINA
# ==============================================================================
st.set_page_config(
    page_title="App Tutor CSED - Gestión Integral",
    page_icon="🎓",
    layout="wide"
)

# Estilos visuales profesionales
st.markdown("""
<style>
    .stApp { background-color: #f4f6f9; }
    h1, h2, h3 { color: #003366; font-family: 'Segoe UI', sans-serif; }
    .stButton>button { background-color: #003366; color: white; border-radius: 8px; font-weight: bold;}
    .stButton>button:hover { background-color: #002244; }
    .info-box { background-color: white; padding: 20px; border-radius: 10px; border-left: 5px solid #003366; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. LÓGICA DE CARGA DE ARCHIVOS (CLASIFICACIÓN INTELIGENTE)
# ==============================================================================

@st.cache_resource
def load_all_pdfs():
    """
    Lee todos los PDFs del directorio y los clasifica en 3 categorías:
    1. DATOS_REALES (06_...): Fechas y alumnos actuales.
    2. ESTILO_REFERENCIA (01_...): Modelos de redacción antiguos.
    3. CONOCIMIENTO (00, 02, 03, 04, 05...): Normativa, guías, rúbricas.
    """
    context = {
        "DATOS_REALES": "",
        "CONOCIMIENTO_NORMATIVO": "",
        "ESTILO_REFERENCIA": ""
    }
    
    files = [f for f in os.listdir('.') if f.endswith('.pdf')]
    
    if not files:
        return None

    count = 0
    for filename in files:
        try:
            reader = PdfReader(filename)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            
            # Clasificación según tus instrucciones
            if filename.startswith("06_VARIABLES"):
                context["DATOS_REALES"] += f"\n--- ARCHIVO VITAL: {filename} ---\n{text}"
            elif filename.startswith("01_MODELO"):
                context["ESTILO_REFERENCIA"] += f"\n--- MODELO DE ESTILO (NO USAR DATOS): {filename} ---\n{text}"
            else:
                # Aquí entran 00, 02, 03, 04, 05 (Importantes para el conocimiento)
                context["CONOCIMIENTO_NORMATIVO"] += f"\n--- FUENTE DE CONOCIMIENTO: {filename} ---\n{text}"
            
            count += 1
        except Exception as e:
            print(f"Error leyendo {filename}: {e}")
            
    return context, count

# Cargar contexto
with st.spinner("Cargando base de conocimiento CSED (Guías, Rúbricas, Variables)..."):
    knowledge_base, file_count = load_all_pdfs()

if file_count:
    st.toast(f"✅ Sistema cargado con éxito. {file_count} documentos procesados.", icon="📚")
else:
    st.error("⚠️ No se detectaron archivos PDF. Asegúrate de subirlos al mismo directorio.")

# ==============================================================================
# 3. CEREBRO IA (GEMINI)
# ==============================================================================

def ask_gemini(prompt, api_key, system_role):
    if not api_key:
        return "⚠️ Error: Falta la API Key. Introdúcela en el menú lateral."
    
    try:
        genai.configure(api_key="AIzaSyDyOMEup6TRFGKvrHFdRp7iOKun8ortVLE")
        
        # PROMPT DE SISTEMA MAESTRO (Aquí definimos la jerarquía)
        master_prompt = f"""
        {system_role}
        
        TIENES ACCESO A 3 TIPOS DE FUENTES DE INFORMACIÓN. SIGUE ESTA JERARQUÍA ESTRICTA:
        
        1. [PRIORIDAD MÁXIMA - LA VERDAD ACTUAL] -> Usa el texto bajo 'DATOS_REALES' (archivos 06_VARIABLES).
           - De aquí saca SIEMPRE: fechas, nombres de alumnos, nombre del tutor actual, plazos vigentes.
           
        2. [PRIORIDAD ALTA - CONOCIMIENTO TÉCNICO] -> Usa el texto bajo 'CONOCIMIENTO_NORMATIVO' (archivos 00, 02, 03, 04, 05).
           - De aquí saca: Rúbricas de corrección, manuales de Moodle, contenido del temario, protocolos de actuación.
           - Si te preguntan "cómo se corrige" o "qué dice la guía", mira AQUÍ.
           
        3. [SOLO REFERENCIA DE ESTILO] -> Usa el texto bajo 'ESTILO_REFERENCIA' (archivos 01_MODELO).
           - Úsalos SOLO para imitar el tono, el formato de las actas o correos.
           - IGNORA CUALQUIER FECHA O NOMBRE que aparezca aquí, son del pasado.
        
        =========================================
        CONTENIDO CARGADO DEL SISTEMA:
        
        [DATOS_REALES]:
        {knowledge_base.get('DATOS_REALES', 'No cargado')}
        
        [CONOCIMIENTO_NORMATIVO]:
        {knowledge_base.get('CONOCIMIENTO_NORMATIVO', 'No cargado')[:50000]}  # Limitado para optimizar token window si es muy grande
        
        [ESTILO_REFERENCIA]:
        {knowledge_base.get('ESTILO_REFERENCIA', 'No cargado')[:10000]}
        =========================================
        
        PREGUNTA DEL USUARIO: {prompt}
        """
        
        model = genai.GenerativeModel('models/gemini-1.5-flash')
        response = model.generate_content(master_prompt)
        return response.text
    except Exception as e:
        return f"Error conectando con Gemini: {str(e)}"

# ==============================================================================
# 4. INTERFAZ DE USUARIO
# ==============================================================================

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2991/2991148.png", width=70)
    st.title("Tutor IA CSED")
    
    api_key = st.text_input("🔑 API Key Gemini", type="password")
    
    menu = st.radio("SECCIONES", ["Panel Principal", "Corrector Tareas", "Chat Experto", "Generador Documentos"])
    
    st.info("ℹ️ Los archivos 06_VARIABLES definen el curso actual.")

# --- SECCIÓN 1: PANEL PRINCIPAL ---
if menu == "Panel Principal":
    st.header("📊 Dashboard del Curso Actual")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="info-box">
        <h4>Base de Conocimiento Activa</h4>
        <p>El sistema ha procesado guías, rúbricas y variables.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if st.button("🔄 Analizar Fechas Clave (06_VARIABLES)"):
            with st.spinner("Consultando archivos 06..."):
                res = ask_gemini("Extrae del archivo 06_VARIABLES las fechas de inicio, examen y cierre. Haz una lista.", api_key, "Eres un asistente administrativo.")
                st.success(res)

# --- SECCIÓN 2: CORRECTOR DE TAREAS ---
elif menu == "Corrector Tareas":
    st.header("📝 Corrección Oficial (Rúbricas CSED)")
    st.info("Este módulo usa los archivos 05_EVALUACION para aplicar las rúbricas correctas.")
    
    tarea = st.selectbox("Selecciona Actividad:", ["T1: Valores", "T2: Líderes", "T3: Instituciones", "T14: Rugby", "Foro General"])
    alumno_text = st.text_area("Pega aquí el contenido o respuesta del alumno:", height=200)
    
    if st.button("Corregir Tarea"):
        role = "Eres el Corrector Oficial CSED. Usa las Rúbricas de los archivos 05_EVALUACION. Formato: 1.Identificación, 2.Evaluación Rúbrica, 3.Nota, 4.Feedback Enriquecido."
        with st.spinner("Aplicando rúbrica..."):
            res = ask_gemini(f"Corrige la tarea: {tarea}. Contenido alumno: {alumno_text}", api_key, role)
            st.markdown(res)

# --- SECCIÓN 3: CHAT EXPERTO ---
elif menu == "Chat Experto":
    st.header("💬 Consultas al Manual y Guía")
    
    mode = st.selectbox("Modo de Consulta:", ["Tutoría (Guía Didáctica 03)", "Técnico (Manual Moodle 02)", "Gestión (Protocolos 00/06)"])
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input("Pregunta sobre normativa, fechas o procedimientos..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)
        
        # Definir roles según archivos
        sys_msg = "Eres un asistente experto CSED."
        if "Técnico" in mode:
            sys_msg = "Eres experto en Moodle. Basa tus respuestas en los archivos 02_MOODLE."
        elif "Tutoría" in mode:
            sys_msg = "Eres tutor pedagógico. Basa tus respuestas en 03_CURSO (Guías y Temas)."
            
        with st.spinner("Consultando fuentes..."):
            response = ask_gemini(prompt, api_key, sys_msg)
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.chat_message("assistant").write(response)

# --- SECCIÓN 4: GENERADOR DOCUMENTOS ---
elif menu == "Generador Documentos":
    st.header("📑 Generador de Actas y Correos")
    st.markdown("Genera documentos usando el **estilo** de los archivos `01_MODELO` pero con los **datos** de `06_VARIABLES`.")
    
    tipo = st.radio("Generar:", ["Acta Semanal", "Correo Bienvenida", "Informe Plagio"])
    
    if st.button("Generar Borrador"):
        prompt_gen = f"Genera un {tipo}. Usa el ESTILO de redacción de los archivos 01_MODELO, pero usa los DATOS REALES (fechas, nombres) de 06_VARIABLES."
        res = ask_gemini(prompt_gen, api_key, "Eres secretario administrativo CSED.")
        st.text_area("Resultado:", value=res, height=400)
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
    Lee todos los PDFs del directorio y los clasifica.
    """
    context = {
        "DATOS_REALES": "",
        "CONOCIMIENTO_NORMATIVO": "",
        "ESTILO_REFERENCIA": ""
    }
    
    # Lista archivos en el directorio actual
    files = [f for f in os.listdir('.') if f.lower().endswith('.pdf')]
    
    if not files:
        return None, 0

    count = 0
    for filename in files:
        try:
            reader = PdfReader(filename)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            
            # Clasificación por prefijos
            if filename.startswith("06_VARIABLES"):
                context["DATOS_REALES"] += f"\n--- ARCHIVO VITAL ACTUAL: {filename} ---\n{text}"
            elif filename.startswith("01_MODELO"):
                context["ESTILO_REFERENCIA"] += f"\n--- MODELO PASADO (ESTILO): {filename} ---\n{text}"
            else:
                # Archivos 00, 02, 03, 04, 05
                context["CONOCIMIENTO_NORMATIVO"] += f"\n--- NORMATIVA/GUÍA: {filename} ---\n{text}"
            
            count += 1
        except Exception as e:
            st.error(f"Error leyendo {filename}: {e}")
            
    return context, count

# Cargar contexto al arrancar
with st.spinner("Cargando base de conocimiento CSED..."):
    knowledge_base, file_count = load_all_pdfs()

if file_count > 0:
    st.toast(f"✅ {file_count} documentos cargados.", icon="📚")
else:
    st.error("⚠️ No se detectaron archivos PDF en el repositorio.")

# ==============================================================================
# 3. CEREBRO IA (CONEXIÓN ROBUSTA)
# ==============================================================================

def ask_gemini(prompt, api_key, system_role):
    if not api_key:
        return "⚠️ Error: Introduce la clave API en el menú lateral."
    
    try:
        # Configuración de la API Key
        genai.configure(api_key=api_key)
        
        # Selección de modelo: Usamos la ruta completa para evitar el error 404
        # El modelo 'gemini-1.5-flash' es el ideal para esta tarea.
        model = genai.GenerativeModel('models/gemini-1.5-flash')
        
        # Construcción del prompt maestro con jerarquía de datos
        master_prompt = f"""
        {system_role}
        
        INSTRUCCIONES DE CONTEXTO:
        1. Tu identidad es Efrén Luis Pérez, tutor del CSED.
        2. Los datos de 'DATOS_REALES' mandan sobre fechas y alumnos (Curso actual).
        3. Los datos de 'ESTILO_REFERENCIA' son solo para copiar el tono de voz.
        4. Usa 'CONOCIMIENTO_NORMATIVO' para rúbricas y manuales.
        
        --- DATOS ACTUALES (06_VARIABLES) ---
        {knowledge_base['DATOS_REALES'] if knowledge_base else 'No hay datos'}
        
        --- CONOCIMIENTO ACADÉMICO (00, 02, 03, 04, 05) ---
        {knowledge_base['CONOCIMIENTO_NORMATIVO'][:30000] if knowledge_base else 'No hay datos'}
        
        --- MODELOS DE ESTILO (01_MODELO) ---
        {knowledge_base['ESTILO_REFERENCIA'][:10000] if knowledge_base else 'No hay datos'}
        
        PREGUNTA DEL USUARIO: {prompt}
        """
        
        response = model.generate_content(master_prompt)
        return response.text
    except Exception as e:
        return f"Error conectando con Gemini: {str(e)}"

# ==============================================================================
# 4. INTERFAZ DE USUARIO (SIDEBAR Y SECCIONES)
# ==============================================================================

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2991/2991148.png", width=70)
    st.title("Tutor IA CSED")
    
    # Campo para la API Key (Sin comillas al pegar)
    user_key = st.text_input("🔑 API Key Gemini", type="password", help="Pega la clave de Google Cloud y pulsa ENTER.")
    
    menu = st.radio("SECCIONES", ["Panel Principal", "Corrector Tareas", "Chat Experto", "Generador Documentos"])
    
    if st.button("🗑️ Limpiar Memoria (Cache)"):
        st.cache_resource.clear()
        st.rerun()

# --- PANEL PRINCIPAL ---
if menu == "Panel Principal":
    st.header("📊 Dashboard del Curso")
    st.markdown(f"""
    <div class="info-box">
    <h4>Estado del Sistema</h4>
    <p>Archivos detectados en el servidor: <b>{file_count}</b></p>
    <p>Tutor actual: <b>Efrén Luis Pérez</b></p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("📅 Extraer fechas clave actuales"):
        with st.spinner("Buscando en 06_VARIABLES..."):
            res = ask_gemini("Dime la fecha de inicio de curso y la del examen según los archivos 06.", user_key, "Eres un asistente administrativo.")
            st.info(res)

# --- CORRECTOR ---
elif menu == "Corrector Tareas":
    st.header("📝 Corrector de Actividades")
    tarea = st.text_input("¿Qué tarea vas a corregir?")
    alumno = st.text_area("Pega aquí el texto del alumno:", height=250)
    
    if st.button("Corregir con Rúbrica"):
        with st.spinner("Analizando..."):
            res = ask_gemini(f"Tarea: {tarea}. Contenido: {alumno}", user_key, "Eres el Corrector CSED. Usa la técnica sándwich y el formato oficial de 7 puntos.")
            st.markdown(res)

# --- CHAT ---
elif menu == "Chat Experto":
    st.header("💬 Consulta de Normativa y Manuales")
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    if p := st.chat_input("Pregúntame cualquier duda técnica o académica..."):
        st.session_state.messages.append({"role": "user", "content": p})
        st.chat_message("user").write(p)
        with st.spinner("Consultando PDFs..."):
            r = ask_gemini(p, user_key, "Eres un tutor experto en el Bloque Común Nivel 1.")
            st.session_state.messages.append({"role": "assistant", "content": r})
            st.chat_message("assistant").write(r)

# --- GENERADOR ---
elif menu == "Generador Documentos":
    st.header("📑 Generador de Documentos Oficiales")
    tipo = st.selectbox("Documento a generar:", ["Acta Semanal", "Correo de Bienvenida", "Mensaje de Apertura de Bloque"])
    
    if st.button("Generar Borrador"):
        with st.spinner("Redactando..."):
            res = ask_gemini(f"Genera un {tipo} con los datos del curso actual.", user_key, "Usa el estilo de los archivos 01_MODELO.")
            st.text_area("Resultado:", value=res, height=350)
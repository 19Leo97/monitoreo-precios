import os
import psycopg2
from crewai import Agent, Task, Crew, Process, LLM
from langchain_openai import AzureChatOpenAI
import requests
from dotenv import load_dotenv

load_dotenv()

# 1. Configuración de variables de entorno para Azure OpenAI
# Reemplaza con tus datos reales obtenidos del portal de Azure
os.environ["AZURE_OPENAI_API_KEY"] = os.getenv("AZURE_OPENAI_API_KEY")
os.environ["AZURE_OPENAI_ENDPOINT"] = os.getenv("AZURE_OPENAI_ENDPOINT")

# 2. Inicializar el LLM de Azure en CrewAI
llm = LLM(
    model="openai/gpt-5.4-mini", 
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    base_url=os.environ["AZURE_OPENAI_ENDPOINT"],
)

# 3. Función matemática/herramienta local para simular la lectura de SQL
def obtener_alertas_sql():
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="retail_db",
            user="admin",
            password="MiPasswordSecreto123",
            port="5432"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT id_producto, producto, precio_competidor, precio_interno, porcentaje_desviacion FROM analisis_precios_competencia WHERE alerta_critica = 'SÍ';")
        filas = cursor.fetchall()
        cursor.close()
        conn.close()
        
        resultado = []
        for f in filas:
            resultado.append(f"Producto: {f[1]} (ID: {f[0]}) | Precio Interno: {f[3]} | Competidor: {f[2]} | Desviación: {f[4]}%")
        return "\n".join(resultado) if resultado else "No se encontraron alertas críticas hoy."
    except Exception as e:
        return f"Error al conectar a SQL: {str(e)}"

# Obtenemos los datos de la base de datos que procesó PySpark
datos_alertas = obtener_alertas_sql()

print("================ INICIO DATOS ALERTAS =================\n" ,datos_alertas, "\n================ FIN DATOS ALERTAS =================\n")

# 4. Definición de Agentes
analista_datos = Agent(
    role='Analista de Datos de Retail',
    goal='Compilar y estructurar reportes sobre productos desalineados con el mercado.',
    backstory='Eres un experto en identificar pérdidas de margen basándote en desviaciones de precios procesadas por Big Data.',
    verbose=True,
    llm=llm
)

estratega_precios = Agent(
    role='Director Estratégico de Precios y Mercadeo',
    goal='Tomar decisiones de negocio basadas en reportes de competencia y redactar correos de acción inmediatos.',
    backstory='Eres un estratega comercial con años de experiencia en retail. Sabes cuándo bajar precios para competir o cuándo mantener el margen.',
    verbose=True,
    llm=llm
)

# 5. Definición de Tareas
tarea_analisis = Task(
    description=f"Revisa la siguiente información de alertas críticas extraída de la base de datos:\n{datos_alertas}\nGenera un resumen limpio con los puntos más críticos.",
    expected_output="Un reporte ejecutivo resumido que identifique claramente qué productos están en riesgo comercial debido a la competencia.",
    agent=analista_datos
)

tarea_estrategia = Task(
    description="Toma el resumen del analista y redacta un correo electrónico profesional dirigido al Gerente de Categorías. El correo debe proponer una acción concreta (ej. bajar precio para igualar, o crear un combo de productos) y justificarla brevemente. (Mi nombre es David Ortiz, el nombre de la Empresa es iAutomate)",
    expected_output="El borrador de un correo electrónico en formato profesional listo para enviar, con saludo, cuerpo estratégico y firma.",
    agent=estratega_precios
)

# 6. Orquestación del Equipo (Crew)
equipo_ia = Crew(
    agents=[analista_datos, estratega_precios],
    tasks=[tarea_analisis, tarea_estrategia],
    process=Process.sequential
)

# Ejecutar el flujo de agentes
print("🤖 Iniciando la sesión de agentes CrewAI...")
resultado_final = equipo_ia.kickoff()

print("\n================ CORREO ESTRATÉGICO GENERADO POR IA ================\n")
print(resultado_final)


# 8. Enviar el resultado a n8n para que dispare el correo
webhook_url = os.getenv("N8N_WEBHOOK_URL")

payload = {
    "correo": str(resultado_final)
}

try:
    respuesta = requests.post(webhook_url, json=payload)
    if respuesta.status_code == 200:
        print("📧 Alerta enviada exitosamente a n8n para su distribución por correo.")
    else:
        print(f"⚠️ n8n respondió con código {respuesta.status_code}: {respuesta.text}")
except Exception as e:
    print(f"❌ Error al conectar con el webhook de n8n: {e}")

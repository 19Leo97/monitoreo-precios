# 🚀 Sistema End-to-End de Monitoreo Inteligente de Precios y Competencia

Proyecto personal de portafolio que implementa una arquitectura moderna de datos, automatización e Inteligencia Artificial para detectar desalineaciones de precios frente a la competencia, procesar los datos a escala y generar recomendaciones comerciales de forma autónoma mediante agentes de IA.

> **Nota de alcance:** este proyecto usa datos de competidores **simulados** (generados en un nodo de código dentro de n8n) con el objetivo de demostrar el patrón arquitectónico completo (ingesta → procesamiento distribuido → persistencia → IA → automatización → BI), no de hacer web scraping real. El stack fue elegido para reflejar herramientas usadas en entornos empresariales de retail/datos a gran escala.

---

## 🛠 Stack Tecnológico

| Categoría | Herramienta |
|---|---|
| Orquestación / Ingesta | n8n |
| API simulada | REST API (Webhook n8n + JavaScript) |
| Procesamiento de Big Data | PySpark |
| Base de datos | PostgreSQL (contenedor Docker) |
| Contenerización | Docker / Docker Compose |
| Inteligencia Artificial | Azure AI Foundry + CrewAI (agentes autónomos) |
| Automatización de notificaciones | n8n (Webhook + Gmail) |
| Visualización de negocio | Power BI Desktop + Power Query |
| Control de versiones | Git |

---

## 🏗 Arquitectura del Sistema

```
[ Local - Docker ]
  n8n (Webhook: API simulada) 
        │
        ▼
  n8n (Ingesta programada → guarda JSON en /data)
        │
        ▼
  PySpark (procesamiento_precios.py)
     - Cruza catálogo interno vs. precios de competencia
     - Calcula diferencia y % de desviación
     - Marca alertas críticas (> 5%)
        │
        ▼
  PostgreSQL (tabla: analisis_precios_competencia)
        │
        ▼
[ Azure - Nube ]
  Azure AI Foundry (modelo desplegado)
        │
        ▼
  CrewAI (agentes_precio.py)
     - Agente Analista de Datos → lee SQL
     - Agente Estratega de Precios → redacta recomendación
        │
        ▼
  n8n (Webhook → Gmail) → Correo con reporte ejecutivo
        │
        ▼
[ Power Platform ]
  Power BI Desktop + Power Query → Dashboard de negocio
```

**📸 [Insertar aquí captura del diagrama de arquitectura / infraestructura Docker corriendo]**

---

## 📂 Estructura del repositorio

```
proyecto-monitoreo-precios/
├── data/
│   └── datos_competencia.json
├── src/
│   ├── pyspark_jobs/
│   │   ├── procesamiento_precios.py
│   │   └── postgresql-42.7.3.jar
│   └── crewai_agents/
│       └── agentes_precio.py
├── docker-compose.yml
├── Reporte_Monitoreo_Precios.pbix
└── README.md
```

---

## 📊 Fases del proyecto

### Fase 1 — Entorno local (Docker + Git)

Se creó la estructura del repositorio con `git init` y se levantó el entorno base con Docker Compose, incluyendo un contenedor de **PostgreSQL** (base de datos `retail_db`) y uno de **n8n** (orquestador local), ambos con volúmenes persistentes.

**📸 [Insertar captura: `docker compose up -d` corriendo exitosamente]**
**📸 [Insertar captura: n8n abierto en `localhost:5678`]**

---

### Fase 2 — Ingesta y procesamiento de Big Data (n8n + REST API + PySpark)

**Qué se construyó:**
- Un **Webhook en n8n** que simula una REST API de precios de competidores, devolviendo un JSON con 5 productos.
- Un segundo workflow (`Ingesta_Precios`) que consulta esa API cada cierto tiempo y guarda el resultado como archivo JSON en la carpeta `/data`.
- Un script en **PySpark** (`procesamiento_precios.py`) que:
  - Lee el JSON generado por n8n.
  - Simula un catálogo interno de precios.
  - Cruza ambos datasets (`JOIN`) y calcula la diferencia de precio y el % de desviación.
  - Marca como `alerta_critica = 'SÍ'` los productos con desviación mayor al 5%.
  - Persiste el resultado en la tabla `analisis_precios_competencia` de PostgreSQL vía JDBC.

**🔧 Ajustes y problemas resueltos:**
- El nodo final del Webhook solo devolvía 1 registro en lugar de los 5 simulados. Se solucionó configurando la opción **"Respond with all incoming items"** en el nodo de respuesta.
- Al escribir el archivo JSON desde n8n hacia disco, fue necesario agregar un **nodo de código en JavaScript** adicional que tomara todos los ítems (`$input.all()`), los convirtiera a string y luego a buffer en base64, para poder enviarlos como archivo binario al nodo de escritura.
- El nodo **Write Files** fallaba por permisos. Se resolvió modificando el `docker-compose.yml` de n8n, agregando las variables de entorno `N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS=false` y `N8N_RESTRICT_FILE_ACCESS_TO=/data`, y montando un volumen local `./data:/data`.
- Al ejecutar PySpark en Windows sin Docker (por limitaciones de compatibilidad de Spark con contenedores en este caso), fue necesario instalar manualmente **`winutils.exe`** (compatible con Hadoop 3.3.5) y configurar las variables de entorno `HADOOP_HOME` y `PATH` para evitar errores clásicos de Spark en Windows.

**📸 [Insertar captura: workflow de n8n con el Webhook y nodos de ingesta]**
**📸 [Insertar captura: consola con el resultado del script `procesamiento_precios.py` (tabla `df_resultado.show()`)]**

---

### Fase 3 — Agentes de IA (Azure AI Foundry + CrewAI)

**Qué se construyó:**
- Un recurso de **Azure AI Foundry** con un modelo desplegado, consumido mediante la cuenta de prueba gratuita/créditos de Azure.
- Un script (`agentes_precio.py`) con dos agentes construidos en **CrewAI**:
  - **Analista de Datos**: se conecta a PostgreSQL y extrae los productos con `alerta_critica = 'SÍ'`.
  - **Estratega de Precios**: redacta un correo ejecutivo con una recomendación de negocio concreta (igualar precio, crear combo, etc.).
- El flujo se orquesta de forma secuencial (`Process.sequential`).

**🔧 Ajustes y problemas resueltos:**
- Ninguno de los modelos tenía cuota disponible en el nivel gratuito inicial de Azure AI Foundry. Fue necesario **actualizar la suscripción a Pay-as-you-go** y **solicitar cuota manualmente** para poder desplegar un modelo.
- El código original planteaba usar `langchain-openai` como puente entre CrewAI y Azure OpenAI. Finalmente se adaptó el script para usar la **integración nativa de LLM de CrewAI**, sin depender de esa librería intermedia.

**📸 [Insertar captura: recurso de Azure AI Foundry con el modelo desplegado]**
**📸 [Insertar captura: consola con la interacción de los agentes / correo generado]**

---

### Fase 4 — Automatización y visualización de negocio

**Paso 1-2 — Power BI + Power Query:**
- Se conectó **Power BI Desktop** a la base de datos PostgreSQL local en modo Importar.
- En **Power Query** se ajustó el tipo de dato de `porcentaje_desviacion` y se creó una columna condicional **Severidad Alerta** ("Crítica (Acción IA)" / "Normal (Bajo control)").
- Se construyó un dashboard con tarjeta de conteo de alertas críticas, gráfico de barras de `diferencia_precio` por producto y una tabla detallada. Guardado como `Reporte_Monitoreo_Precios.pbix`.

**📸 [Insertar captura: dashboard de Power BI]**

**Paso 3 — Automatización del envío de alertas (con n8n, en lugar de Power Automate):**

En vez de usar Power Automate, se decidió reutilizar **n8n** para cerrar el ciclo completo del proyecto (detección → decisión de IA → notificación), evitando depender de una plataforma adicional.

**Qué se construyó:**
- Un nuevo workflow en n8n (`Envio_Alertas_IA`) con un nodo **Webhook** (`POST /alerta-precios`).
- Un nodo **Gmail** conectado vía OAuth2, configurado para enviar el correo con el reporte generado por los agentes de CrewAI.
- Se modificó `agentes_precio.py` para que, al finalizar la ejecución de los agentes, haga una petición `POST` al webhook de n8n con el contenido del correo generado.

**🔧 Ajustes y problemas resueltos:**
- El correo llegaba como texto plano, perdiendo el formato Markdown (negrillas `**texto**` y saltos de línea) generado por el agente de IA. Se resolvió agregando una expresión de JavaScript en el campo de mensaje del nodo Gmail que convierte el formato Markdown a HTML antes del envío:
  ```javascript
  {{ $json["body"]["correo"].replace(/\*\*(.*?)\*\*/g, '<b>$1</b>').replace(/\n/g, '<br>') }}
  ```

**📸 [Insertar captura: workflow de n8n `Envio_Alertas_IA` con nodos Webhook → Gmail]**
**📸 [Insertar captura: correo recibido con formato (negrillas y saltos de línea) correctamente renderizado]**

---

## 🔐 Consideraciones de seguridad

> Las credenciales de PostgreSQL y las claves de Azure OpenAI se manejaron como variables de entorno / archivo `.env` (excluido del repositorio mediante `.gitignore`). Ninguna credencial real está incluida en este código fuente.

---

## ⚙️ Cómo ejecutar el proyecto localmente

```bash
# 1. Clonar el repositorio
git clone <url-del-repositorio>
cd proyecto-monitoreo-precios

# 2. Levantar la infraestructura local
docker compose up -d

# 3. Instalar dependencias de Python
pip install pyspark psycopg2-binary crewai requests python-dotenv

# 4. Configurar en n8n (localhost:5678):
#    - Workflow del Webhook simulador de la API
#    - Workflow de ingesta (Ingesta_Precios)
#    - Workflow de envío de alertas (Envio_Alertas_IA) con nodo Gmail

# 5. Ejecutar el procesamiento de datos
python src/pyspark_jobs/procesamiento_precios.py

# 6. Ejecutar los agentes de IA (genera y envía el reporte)
python src/crewai_agents/agentes_precio.py

# 7. Abrir el dashboard
# Reporte_Monitoreo_Precios.pbix con Power BI Desktop
```

---

## 📈 Posibles mejoras futuras

- Reemplazar la API simulada por una fuente de datos real (scraping autorizado o API pública de precios).
- Migrar el procesamiento de PySpark local a un clúster administrado (Azure Databricks / Synapse) para reflejar un entorno productivo real.
- Agregar pruebas automatizadas (unit tests) al script de PySpark.
- Desplegar los contenedores en Azure Container Apps para tener el flujo corriendo en la nube de forma continua.

---

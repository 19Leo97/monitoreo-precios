import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Forzar a PySpark a usar el mismo intérprete de Python en driver y workers
os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, when, round

# 1. Obtener la ruta absoluta del driver JAR
current_dir = os.path.dirname(os.path.abspath(__file__))
jar_path = os.path.join(current_dir, "postgresql-42.7.3.jar")

# 2. Inicializar la sesión de Spark incluyendo el JAR local
spark = SparkSession.builder \
    .appName("MonitoreoPreciosRetail") \
    .config("spark.jars", jar_path) \
    .getOrCreate()

print("🚀 Spark inicializado exitosamente.")

# 3. Simular el Catálogo de Precios Interno de Nuestra Empresa
# En un escenario real, esto vendría de otra tabla de nuestra base de datos
datos_internos = [
    ("PROD001", 460.00, "Tecnología"),
    ("PROD002", 710.00, "Tecnología"),
    ("PROD003", 89.99, "Hogar"),
    ("PROD004", 65.00, "Audio")
]
columnas_internas = ["id_producto", "precio_interno", "categoria"]
df_interno = spark.createDataFrame(datos_internos, columnas_internas)

# 4. Leer el JSON generado por n8n desde la carpeta de datos compartida
# Subimos un nivel desde src/pyspark_jobs/ para llegar a /data
ruta_json = os.path.abspath(os.path.join(current_dir, "../../data/datos_competencia.json"))
print(f"📖 Leyendo datos desde: {ruta_json}")

df_competencia = spark.read.option("multiline", "true").json(ruta_json)

df_competencia.show()

# 5. Transformación de Datos (Lógica de Big Data)
# Combinamos nuestro catálogo con los precios del competidor mediante un JOIN
df_analisis = df_competencia.join(df_interno, on="id_producto", how="inner")

# Calculamos la diferencia de precio y el porcentaje de desviación
df_resultado = df_analisis.withColumn(
    "diferencia_precio", round(col("precio_interno") - col("precio_competidor"), 2)
).withColumn(
    "porcentaje_desviacion", round((col("diferencia_precio") / col("precio_interno")) * 100, 2)
).withColumn(
    "alerta_critica", when(col("porcentaje_desviacion") > 5.0, lit("SÍ")).otherwise(lit("NO"))
)

print("📊 Vista previa del análisis de precios:")
df_resultado.show()

# 6. Configuración de conexión a PostgreSQL en Docker
url_db = f"jdbc:postgresql://{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
propiedades_db = {
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "driver": "org.postgresql.Driver"
}

# 7. Guardar el resultado en la base de datos (Sobrescribe o añade)
print("💾 Guardando análisis en PostgreSQL...")
df_resultado.write.jdbc(
    url=url_db, 
    table="analisis_precios_competencia", 
    mode="overwrite", 
    properties=propiedades_db
)

print("✅ Datos guardados exitosamente en la tabla 'analisis_precios_competencia'.")

# Cerrar sesión de Spark
spark.stop()

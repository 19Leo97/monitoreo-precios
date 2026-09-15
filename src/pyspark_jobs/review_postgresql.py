import pandas as pd
from sqlalchemy import create_engine

# Cadena de conexión a tu PostgreSQL en Docker
engine = create_engine("postgresql://admin:MiPasswordSecreto123@localhost:5432/retail_db")

# Consultar la tabla guardada por Spark
df_verificacion = pd.read_sql("SELECT * FROM analisis_precios_competencia;", engine)

print("--- DATOS ALMACENADOS EN POSTGRESQL ---")
print(df_verificacion.head())
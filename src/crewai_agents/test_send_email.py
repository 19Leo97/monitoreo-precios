import requests

resultado_final = "**Asunto:** Acción inmediata de pricing – Audífonos Bluetooth PROD004 Estimado/a Gerente de Categorías, Con base en el último reporte de competitividad, quiero poner a su consideración una acción inmediata sobre **Audífonos Bluetooth (PROD004)**. Actualmente nuestro precio interno se encuentra en **$65.00**, mientras que el competidor directo está en **$59.99**, lo que representa una desviación de **7.71%** por encima del mercado. Dado que se trata de una **alerta crítica**, recomiendo **ajustar el precio interno para igualarlo al competidor en $59.99**, o al menos acercarlo de forma inmediata a ese nivel. Esta corrección ayudaría a reducir el riesgo de pérdida de conversión y nos permitiría defender mejor la participación del producto en la categoría. La brecha actual incrementa la probabilidad de desvío de ventas hacia la competencia y puede impactar negativamente la rotación, por lo que considero prioritario actuar sin demora. Si existe una necesidad de proteger margen, podríamos evaluar posteriormente una estrategia complementaria de valor, pero en el corto plazo la prioridad debe ser recuperar competitividad en precio. Quedo atento a su validación para proceder con el ajuste correspondiente. Saludos cordiales, **[Tu Nombre]** Director Estratégico de Precios y Mercadeo **[Empresa]**"

# 8. Enviar el resultado a n8n para que dispare el correo
webhook_url = "http://localhost:5678/webhook-test/alerta-precios"

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
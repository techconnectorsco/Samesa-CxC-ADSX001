from datetime import datetime

status_global_ejecution = {
    "fecha_ejecucion": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    "tiempo_ejecucion": None,
    "clientes_procesados": 0,
    "total_documentos_procesados": 0,
    "reportes_generados": 0,
    "emails_exitosos": 0,
    "emails_fallidos": 0,
    "tipo_ejecucion": "Automatica",
    "fuente": "Samesa-CxC-ADSX001 Automation",
    "monto_total_usd": 0.00,
    "monto_total_colones": 0.00,
    "observaciones": "",
}
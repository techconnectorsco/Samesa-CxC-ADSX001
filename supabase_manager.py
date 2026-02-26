import os
from datetime import datetime, timezone
from conexion_supabase import supabase_db, subir_archivo_bucket

# Este ID lo sacaremos de la base de datos (el que te pedí arriba)
# Opcionalmente puedes ponerlo en tu .env como ID_RPA_SAMESA
ID_RPA_SAMESA = "1b5d79a2-542d-47af-b86a-f43eee21b3c3"

def verificar_estado_rpa():
    """
    Consulta si el RPA está activo en Supabase.
    Por ahora, siempre devuelve True para no interrumpir el flujo.
    """
    try:
        # LÓGICA PARA FUTURO:
        # res = supabase_db.table("automatizaciones").select("esta_activa").eq("id", ID_RPA_SAMESA).single().execute()
        # return res.data["esta_activa"]
        
        print("ℹ️ Verificando estado del RPA: Forzado a ACTIVO (Simulado)")
        return True 
    except Exception as e:
        print(f"⚠️ Error verificando estado: {e}. Continuando por defecto...")
        return True

def finalizar_y_reportar(status_global, ruta_pdf_local=None):
    """
    Función maestra para:
    1. Subir log PDF (si existe)
    2. Consolidar métricas
    3. Registrar ejecución en Supabase
    """
    print("📤 Iniciando reporte final a Supabase...")
    
    url_log_publica = None
    if ruta_pdf_local and os.path.exists(ruta_pdf_local):
        nombre_archivo_nube = f"Samesa/logs/log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        url_log_publica = subir_archivo_bucket("logs-rpa", ruta_pdf_local, nombre_archivo_nube)

    # Preparar datos para la tabla 'ejecuciones'
    # Adaptamos los nombres de tu status_global a la tabla de Supabase
    datos_ejecucion = {
        "automatizacion_id": ID_RPA_SAMESA,
        "fecha_inicio": datetime.now(timezone.utc).isoformat(), # O usar la de status_global si prefieres
        "fecha_fin": datetime.now(timezone.utc).isoformat(),
        "estado": "Exitoso" if status_global.get("emails_fallidos", 0) == 0 else "Con Advertencias",
        "metricas": status_global, # Aquí va el jsonb completo con clientes_procesados, montos, etc.
        "log_salida": url_log_publica or status_global.get("observaciones", ""),
        "causa_error": None
    }

    try:
        res = supabase_db.table("ejecuciones").insert(datos_ejecucion).execute()
        print("✅ Ejecución reportada correctamente en Supabase.")
        return res.data
    except Exception as e:
        print(f"❌ Error al insertar ejecución: {e}")
        return None
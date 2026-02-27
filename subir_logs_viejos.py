import os
import re
from datetime import datetime
from conexion_supabase import supabase_db, subir_archivo_bucket

# ID único de la automatización Samesa CxC
ID_RPA_SAMESA = "1b5d79a2-542d-47af-b86a-f43eee21b3c3"

# Ruta exacta donde pusiste todos los PDFs
CARPETA_LOGS = r"D:\Users\Usuario\Desktop\EC-SAMESA\Samesa-CxC-ADSX001\logs_viejos"

def sincronizar_logs():
    print("🚀 Iniciando sincronización de PDFs históricos...")

    # 1. Descargar historial de la base de datos para comparar las fechas
    print("📥 Consultando historial en Supabase...")
    res = supabase_db.table("ejecuciones").select("id, fecha_inicio, log_salida").eq("automatizacion_id", ID_RPA_SAMESA).execute()
    ejecuciones = res.data
    
    # Agrupamos por fecha (YYYY-MM-DD)
    mapa_ejecuciones = {}
    for ej in ejecuciones:
        # Tomamos solo los primeros 10 caracteres: "2025-01-01T10:00:00" -> "2025-01-01"
        fecha_str = ej["fecha_inicio"][:10] 
        if fecha_str not in mapa_ejecuciones:
            mapa_ejecuciones[fecha_str] = []
        mapa_ejecuciones[fecha_str].append(ej)

    # 2. Leer la carpeta de los PDFs
    if not os.path.exists(CARPETA_LOGS):
        print(f"❌ No se encontró la carpeta: {CARPETA_LOGS}")
        return

    archivos_pdf = [f for f in os.listdir(CARPETA_LOGS) if f.lower().endswith(".pdf")]
    print(f"📁 Encontrados {len(archivos_pdf)} archivos PDF.\n")

    # 3. Procesar cada archivo
    for archivo in archivos_pdf:
        # Extraer la fecha del nombre (ej: email_logs_01-01-25.pdf -> 01-01-25)
        match = re.search(r"(\d{2}-\d{2}-\d{2})", archivo)
        if not match:
            print(f"⚠️ Ignorando '{archivo}' (No se detectó fecha DD-MM-YY en el nombre).")
            continue
            
        fecha_archivo = match.group(1)
        
        try:
            # Convertir '01-01-25' a formato de base de datos '2025-01-01'
            dt = datetime.strptime(fecha_archivo, "%d-%m-%y")
            fecha_busqueda = dt.strftime("%Y-%m-%d")
        except Exception as e:
            print(f"⚠️ Error leyendo fecha de '{archivo}': {e}")
            continue

        # 4. Validar si hubo ejecución ese día
        ejecuciones_del_dia = mapa_ejecuciones.get(fecha_busqueda, [])
        if not ejecuciones_del_dia:
            print(f"⏭️ Saltando '{archivo}': No hay registros en BD el día {fecha_busqueda}.")
            continue

        # 5. Subir el archivo al Storage
        ruta_local = os.path.join(CARPETA_LOGS, archivo)
        # Carpeta ordenada en Supabase: Samesa/logs/historico/2025/01/archivo.pdf
        nombre_en_nube = f"Samesa/logs/historico/{dt.strftime('%Y/%m')}/{archivo}"
        
        print(f"☁️ Subiendo '{archivo}' al Storage...")
        url_publica = subir_archivo_bucket("logs-rpa", ruta_local, nombre_en_nube)
        
        if not url_publica:
            print(f"❌ Falló la subida de '{archivo}'.")
            continue

        # 6. Vincular el enlace a la ejecución
        for ej in ejecuciones_del_dia:
            # Si ya tiene un link válido de Storage, no lo pisamos
            if ej.get("log_salida") and str(ej.get("log_salida")).startswith("http"):
                continue
                
            try:
                supabase_db.table("ejecuciones").update({"log_salida": url_publica}).eq("id", ej["id"]).execute()
                print(f"  ✅ Base de datos actualizada para el día {fecha_busqueda}")
            except Exception as e:
                print(f"  ❌ Error actualizando BD: {e}")

    print("\n🏁 ¡Sincronización de PDFs históricos terminada exitosamente!")

if __name__ == "__main__":
    sincronizar_logs()
import pandas as pd
import re
import os
from datetime import datetime
from conexion_supabase import supabase_db

# ID único de la automatización Samesa CxC
ID_RPA_SAMESA = "1b5d79a2-542d-47af-b86a-f43eee21b3c3"

def parse_tiempo_viejo(tiempo_str):
    """Convierte formatos como '1 min 8.72 sec' a segundos flotantes."""
    try:
        if pd.isna(tiempo_str) or tiempo_str == "": return 0.0
        partes = re.findall(r"(\d+\.?\d*)", str(tiempo_str))
        if len(partes) == 2:
            return float(partes[0]) * 60 + float(partes[1])
        elif len(partes) == 1:
            return float(partes[0])
        return 0.0
    except:
        return 0.0

def migrar_datos():
    print("🚀 Iniciando migración directa desde archivos Excel...")

    ruta_data_1 = r"D:\Users\Usuario\Desktop\EC-SAMESA\Samesa-CxC-ADSX001\DATA_1.xlsx"
    ruta_data_samesa = r"D:\Users\Usuario\Desktop\EC-SAMESA\Samesa-CxC-ADSX001\DATA SAMESA.xlsx"

    try:
        # 1. Cargar DATA SAMESA (Sistema Actual)
        print(f"📖 Leyendo {os.path.basename(ruta_data_samesa)}...")
        df_nuevo = pd.read_excel(ruta_data_samesa)
        df_nuevo.columns = [str(col).strip() for col in df_nuevo.columns]
        
        # Buscar columna de fecha
        col_fecha_n = next((c for c in df_nuevo.columns if 'fecha' in c.lower()), None)
        df_nuevo['fecha_dt'] = pd.to_datetime(df_nuevo[col_fecha_n])
        
        # Fecha donde empieza el archivo nuevo
        fecha_corte = df_nuevo['fecha_dt'].min()
        print(f"📅 Fecha de corte detectada: {fecha_corte}")

        # 2. Cargar DATA_1 (Sistema Viejo)
        print(f"📖 Leyendo {os.path.basename(ruta_data_1)}...")
        df_viejo = pd.read_excel(ruta_data_1)
        df_viejo.columns = [str(col).strip() for col in df_viejo.columns]
        
        col_fecha_v = next((c for c in df_viejo.columns if 'fecha' in c.lower()), None)
        df_viejo['fecha_dt'] = pd.to_datetime(df_viejo[col_fecha_v])
        
        # Filtrar historial viejo (solo lo anterior a la fecha de corte)
        df_viejo_filtrado = df_viejo[df_viejo['fecha_dt'] < fecha_corte].copy()
        
    except Exception as e:
        print(f"❌ Error al procesar los archivos Excel: {e}")
        return

    registros_para_subir = []

    # --- PROCESAR DATA_1 (HISTÓRICO VIEJO) ---
    print(f"📦 Procesando {len(df_viejo_filtrado)} registros de DATA_1...")
    col_cli = next((c for c in df_viejo.columns if 'atendidos' in c.lower()), None)
    col_tiempo = next((c for c in df_viejo.columns if 'tiempo' in c.lower()), None)

    for _, row in df_viejo_filtrado.iterrows():
        cli_val = str(row.get(col_cli, '')).strip().lower()
        if cli_val in ['nan', '', 'false', '0', 'none']:
            continue
        
        try:
            cant_clientes = int(float(row[col_cli]))
            segundos = parse_tiempo_viejo(row[col_tiempo])
            
            registros_para_subir.append({
                "automatizacion_id": ID_RPA_SAMESA,
                "fecha_inicio": row['fecha_dt'].isoformat(),
                "fecha_fin": row['fecha_dt'].isoformat(),
                "estado": "Exitoso",
                "metricas": {
                    "fuente": "Samesa-CxC-ADSX001 Histórico (v1)",
                    "clientes_procesados": cant_clientes,
                    "emails_exitosos": cant_clientes,
                    "tiempo_ejecucion": segundos,
                    "monto_total_usd": 0.0,
                    "monto_total_colones": 0.0
                },
                "log_salida": "Migración histórica Excel (v1)"
            })
        except: continue

    # --- PROCESAR DATA SAMESA (HISTÓRICO ACTUAL) ---
    print(f"📦 Procesando {len(df_nuevo)} registros de DATA SAMESA...")
    for _, row in df_nuevo.iterrows():
        obs = str(row.get('observaciones', '')).lower()
        if "no hubo clientes" in obs or "no se envia nada" in obs:
            continue
            
        try:
            def get_val(keywords, default=0):
                col = next((c for c in df_nuevo.columns if all(k in c.lower() for k in keywords)), None)
                val = row[col] if col else default
                return 0 if pd.isna(val) else val

            registros_para_subir.append({
                "automatizacion_id": ID_RPA_SAMESA,
                "fecha_inicio": row['fecha_dt'].isoformat(),
                "fecha_fin": row['fecha_dt'].isoformat(),
                "estado": "Exitoso" if int(get_val(['emails', 'fallidos'])) == 0 else "Con Advertencias",
                "metricas": {
                    "fuente": get_val(['fuente'], "Samesa RPA"),
                    "clientes_procesados": int(get_val(['clientes', 'numero'])),
                    "total_documentos_procesados": int(get_val(['documentos'])),
                    "emails_exitosos": int(get_val(['emails', 'exitosos'])),
                    "emails_fallidos": int(get_val(['emails', 'fallidos'])),
                    "monto_total_usd": round(float(get_val(['monto', 'usd'])), 2),
                    "monto_total_colones": round(float(get_val(['monto', 'colones'])), 2),
                    "tiempo_ejecucion": float(get_val(['tiempo']))
                },
                "log_salida": f"Migrado: {row.get('observaciones', '')}"
            })
        except: continue

    # --- SUBIDA FINAL A SUPABASE ---
    total = len(registros_para_subir)
    print(f"✅ Total final a migrar: {total}")
    
    if registros_para_subir:
        for i in range(0, total, 50):
            batch = registros_para_subir[i:i+50]
            try:
                supabase_db.table("ejecuciones").insert(batch).execute()
                print(f"✔️ Bloque {i//50 + 1} enviado.")
            except Exception as e:
                print(f"❌ Error subiendo bloque: {e}")

    print("🏁 ¡Proceso terminado! Ya puedes revisar Supabase.")

if __name__ == "__main__":
    migrar_datos()
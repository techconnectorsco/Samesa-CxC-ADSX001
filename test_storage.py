import os
from conexion_supabase import subir_archivo_bucket

# Datos para la prueba
BUCKET_NAME = "logs-rpa"
ARCHIVO_LOCAL = "test.pdf"
# Lo guardamos en una carpeta con el nombre del bot para ir organizando
RUTA_DESTINO = "Samesa/pruebas/test_conexion.pdf"

print(f"🚀 Iniciando subida de {ARCHIVO_LOCAL} a Supabase Storage...")

if os.path.exists(ARCHIVO_LOCAL):
    url_resultado = subir_archivo_bucket(
        nombre_bucket=BUCKET_NAME,
        ruta_archivo_local=ARCHIVO_LOCAL,
        ruta_destino_supabase=RUTA_DESTINO
    )

    if url_resultado:
        print(f"✅ ¡Éxito! El archivo ya está en la nube.")
        print(f"🔗 URL Pública: {url_resultado}")
    else:
        print("❌ La subida falló. Revisa los mensajes de error anteriores.")
else:
    print(f"⚠️ Error: No encontré el archivo '{ARCHIVO_LOCAL}' en la raíz del proyecto.")
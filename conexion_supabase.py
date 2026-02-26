import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

def obtener_cliente_supabase() -> Client:
    """
    Inicializa y retorna el cliente de conexión a Supabase.
    """
    url: str = os.environ.get("SUPABASE_URL")
    # Usamos la Service Role Key para tener permisos de administrador en el entorno backend (RPA)
    key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    
    if not url or not key:
        raise ValueError("Error: Faltan las credenciales SUPABASE_URL o SUPABASE_SERVICE_ROLE_KEY en el archivo .env")
        
    # Crear y retornar el cliente
    cliente: Client = create_client(url, key)
    return cliente

def subir_archivo_bucket(nombre_bucket: str, ruta_archivo_local: str, ruta_destino_supabase: str):
    """
    Sube un archivo a un bucket de Supabase Storage.
    """
    try:
        with open(ruta_archivo_local, 'rb') as f:
            # Usamos la instancia global supabase_db que ya tienes creada arriba
            respuesta = supabase_db.storage.from_(nombre_bucket).upload(
                file=f,
                path=ruta_destino_supabase,
                file_options={"content-type": "application/pdf"}
            )
        
        # Obtenemos la URL pública para guardarla luego en la tabla ejecuciones
        url_publica = supabase_db.storage.from_(nombre_bucket).get_public_url(ruta_destino_supabase)
        print(f"✅ Archivo subido exitosamente: {url_publica}")
        return url_publica

    except Exception as e:
        # Si el error es porque el archivo ya existe, puedes manejarlo aquí
        print(f"❌ Error al subir archivo a Supabase Storage: {e}")
        return None

# Inicializamos una instancia global que podremos importar en otros archivos
supabase_db = obtener_cliente_supabase()
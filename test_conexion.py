from conexion_supabase import supabase_db

print("Iniciando prueba de conexión a Supabase...")

try:
    # Hacemos una consulta mínima: traer solo 1 ID de tu tabla 'automatizaciones'
    respuesta = supabase_db.table("automatizaciones").select("id").limit(1).execute()
    
    print("✅ Conexión exitosa. El cliente de Supabase respondió correctamente.")
    print(f"Respuesta de la BD: {respuesta.data}")
    
except Exception as e:
    print(f"❌ Falló la conexión: {e}")
import os
from shareplum import Site
from shareplum import Office365
from shareplum.site import Version
from decouple import config
from datetime import datetime  # Para obtener la fecha actual

# Autenticación con Office365 (usuario y contraseña de aplicación)
username = config('SAMESA_EMAIL')
app_password = config('SAMESA_EMAIL_PASS')
site_url = "https://gruposamesa.sharepoint.com/sites/contabilidad"
base_folder_path = "Documentos compartidos/General/Asistente Digital Estado de Cuenta/Estados de cuentas enviados/Periodo 2025"


def upload_file_to_sharepoint(client_name, file_path, file_type, ):
    """
    Sube un archivo a la subcarpeta dinámica en SharePoint según su tipo y el mes actual.
    Se asume que las carpetas PDF y EXCEL ya están creadas dentro de cada mes.

    Args:
        file_path (str): La ruta local del archivo que se va a subir.
        file_type (str): Tipo de archivo ('pdf' o 'excel').
    """
    try:
        # Validar que el archivo exista antes de intentar subirlo
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"El archivo no existe: {file_path}")
        
        # Obtener el mes actual en formato de nombre de mes (Ej. 'Enero')
        today = datetime.now()
        mes_actual = today.strftime("%B")  # Nombre del mes completo en inglés
        mes_dict = {
            'January': 'Enero', 'February': 'Febrero', 'March': 'Marzo', 'April': 'Abril',
            'May': 'Mayo', 'June': 'Junio', 'July': 'Julio', 'August': 'Agosto', 'September': 'Septiembre',
            'October': 'Octubre', 'November': 'Noviembre', 'December': 'Diciembre'
        }
        mes_actual_es = mes_dict[mes_actual]  # Traducir al español
        
        # Determinar el nombre de la subcarpeta según el tipo de archivo
        if file_type.lower() == 'pdf':
            subfolder_name = "PDF"
        elif file_type.lower() == 'excel':
            subfolder_name = "EXCEL"
        else:
            raise ValueError("El tipo de archivo debe ser 'pdf' o 'excel'")

        # Definir la ruta completa a la carpeta dentro del mes y tipo de archivo
        full_folder_path = f"{base_folder_path}/{mes_actual_es}/{subfolder_name}"
        
        # Autenticación con Office 365
        authcookie = Office365('https://gruposamesa.sharepoint.com', 
                               username=username, 
                               password=app_password).GetCookies()
        
        # Acceder al sitio de SharePoint
        site = Site(site_url, version=Version.v365, authcookie=authcookie)
        print("Conexión al Drive establecida!")
        # Intentar acceder a la subcarpeta
        try:
            target_folder = site.Folder(full_folder_path)
            # Verificar si se puede acceder a la carpeta leyendo metadatos
            # _ = target_folder.properties  # Forzar la carga de propiedades para validar existencia
        except Exception:
            print(f"La carpeta '{full_folder_path}' no existe. Asegúrese de que la carpeta esté creada manualmente.")
            return

        # Leer el contenido del archivo
        file_name = os.path.basename(file_path)

        # Obtener la fecha actual en formato dd-mm-yyyy
        today_str = today.strftime("%d-%m-%Y")

        # Separar el nombre del archivo de su extensión
        name, extension = os.path.splitext(file_name)

        if file_type == 'excel':
            # Crear el nombre del archivo con la fecha antes de la extensión
            file_name_with_date = f"E.C.{client_name}_{today_str}{extension}"
        else :
            file_name_with_date = f"{name}_{today_str}{extension}"

        with open(file_path, "rb") as file:
            file_content = file.read()
        
        # Subir el archivo a SharePoint con el nuevo nombre
        target_folder.upload_file(file_content, file_name_with_date)
        print('Archivo subido al sharepoint...')
        #print(f"Archivo '{file_name_with_date}' subido correctamente a la carpeta '{full_folder_path}'.")
    
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Error al subir el archivo: {e}")

# main.py
import pyodbc
import pandas as pd
from generarpdf import generar_estado_de_cuenta_pdf_por_cliente_y_moneda
from db_connection import get_db_connection

from datetime import datetime
from email.message import EmailMessage
import os
import smtplib
from fpdf import FPDF
from decouple import config
import time
import requests
from global_status import status_global_ejecution
from google_sheet_log import registrar_ejecucion



def obtener_datos_combinados():
    """
    Obtiene los datos combinados de las tablas de la base de datos.

    :return: pd.DataFrame con los datos combinados.
    """
    # Query para obtener datos de facturas
    query_facturas = """
    SELECT
        OINV.DocNum AS "Número Factura",
        OINV.CardCode AS "Código Cliente",
        OINV.CardName AS Cliente,
        OINV.DocDate AS "Fecha Factura",
        OINV.DocDueDate AS "Fecha Vencimiento",
        OINV.DocCur AS Moneda,
        OINV.DocTotal AS "Monto Total CRC",
        OINV.PaidToDate AS "Monto Pagado CRC",
        (OINV.DocTotal - OINV.PaidToDate) AS "Monto Pendiente CRC",
        OINV.DocTotalFC AS "Monto Total USD",
        OINV.PaidFC AS "Monto Pagado USD",
        (OINV.DocTotalFC - OINV.PaidFC) AS "Monto Pendiente USD",
        OINV.NumAtCard AS "Recibo"
    FROM 
        dbo.OINV
    WHERE
        OINV.DocDate >= '2024-01-01'
        AND OINV.DocTotal > OINV.PaidToDate
        AND OINV.Canceled = 'N'
    ORDER BY
        OINV.CardName;
    """

    # Query para obtener datos de clientes
    query_clientes = """
    SELECT 
        CardCode AS "Código Cliente",
        GroupCode AS "Código Grupo",
        U_NVT_CorreoEC AS "Correo Electrónico",
        U_NVT_DiasTramite AS "Días de Trámite",
        LicTradNum AS "Cedula Juridica"
    FROM 
        dbo.OCRD
    WHERE 
        GroupCode = 100;
    """

    try:

        # Obtener conexión
        conn = get_db_connection()

        # Obtener datos de facturas
        df_facturas = pd.read_sql(query_facturas, conn)

        # Obtener datos de clientes
        df_clientes = pd.read_sql(query_clientes, conn)

        # Cerrar conexión
        conn.close()

        # Combinar ambos DataFrames en uno solo utilizando la columna "Código Cliente"
        df_combinado = pd.merge(df_facturas, df_clientes, on="Código Cliente", how="inner")

        return df_combinado
    
    except Exception as e:
        print(f"Error al obtener los datos de la base de datos: {e}")
        return None

def send_log_by_email(recipient_email):
    """Envía el archivo de log (PDF) a un correo específico."""
    
    today = datetime.now().strftime('%d-%m-%y')
    current_directory = os.path.dirname(os.path.abspath(__file__))
    parent_directory = os.path.abspath(os.path.join(current_directory, ".."))
    log_folder = os.path.join(parent_directory, f"Email_Logs_E.C._{today}")
    log_path = os.path.join(log_folder, f"email_logs_{today}.pdf")
    
    # Crear el mensaje de correo
    from_email = config('SAMESA_EMAIL')
    password = config('SAMESA_EMAIL_PASS')
    
    # Email body (HTML format)
    body = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: 'Segoe UI', Arial, sans-serif;
                color: #333333;
                background-color: #f3f4f6;
                margin: 0;
                padding: 30px;
            }}
            .container {{
                max-width: 700px;
                margin: auto;
                background-color: #ffffff;
                border-radius: 10px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
                padding: 30px;
            }}
            h2 {{
                color: #0078D7;
                text-align: center;
                border-bottom: 3px solid #0078D7;
                padding-bottom: 10px;
                margin-bottom: 25px;
            }}
            p {{
                font-size: 15px;
                line-height: 1.6;
            }}
            .button {{
                display: inline-block;
                background-color: #0078D7;
                color: white;
                text-decoration: none;
                padding: 12px 20px;
                border-radius: 6px;
                font-weight: bold;
                margin-top: 25px;
            }}
            .footer {{
                text-align: center;
                font-size: 13px;
                color: #777;
                margin-top: 35px;
                padding-top: 15px;
                border-top: 1px solid #e5e7eb;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>📊 Registro de Correos Enviados - SAMESA</h2>

            <p>Estimado equipo,</p>
            <p>
                Adjunto se encuentra el archivo con el registro de los correos enviados 
                correspondientes al estado de cuenta del día <strong>{datetime.now().strftime('%d/%m/%Y')}</strong>.
            </p>

            <p>
                Por favor revise la información adjunta y, en caso de detectar 
                cualquier error, incidencia o inconsistencia, puede reportarlo 
                directamente mediante el siguiente formulario:
            </p>

            <div style="text-align: center; margin-top: 25px;">
                <a href="https://forms.gle/974zsGY3jtFRcxVG9" target="_blank"
                style="display: inline-block;
                        background-color: #0078D7;
                        color: #ffffff !important;
                        text-decoration: none;
                        padding: 12px 24px;
                        border-radius: 6px;
                        font-weight: bold;
                        font-size: 15px;
                        box-shadow: 0 2px 6px rgba(0,0,0,0.15);">
                    🧾 Reportar incidencia o error
                </a>
            </div>

            <p>Saludos cordiales</p>

            <div class="footer">
                <p>Este correo fue generado automáticamente por el asistente digital de 
                <strong>SAMESA</strong>.</p>
                <p>No responda directamente a este mensaje. Si requiere soporte adicional, 
                utilice el formulario anterior o contacte al equipo técnico.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Crear el mensaje
    email = EmailMessage()
    email['From'] = from_email
    email['To'] = recipient_email
    email['Subject'] = f"Registro de Correos Enviados - {today}"
    email.set_content(body, subtype='html')

    # Adjuntar el archivo PDF del log
    try:
        with open(log_path, 'rb') as log_file:
            email.add_attachment(
                log_file.read(),
                maintype='application',
                subtype='pdf',
                filename=os.path.basename(log_path)
            )
    except FileNotFoundError:
        print(f"Error: El archivo de log no se encuentra en la ruta '{log_path}'.")
        return
    except Exception as e:
        print(f"Error al adjuntar el archivo de log: {e}")
        return

    # Enviar el correo
    try:
        with smtplib.SMTP('smtp.office365.com', 587) as smtp:  # Usar SSL para seguridad
            smtp.ehlo()  # Saludar al servidor
            smtp.starttls()
            smtp.login(from_email, password)
            smtp.send_message(email)
        print(f"Correo de log enviado a {recipient_email}")
    except smtplib.SMTPException as e:
        print(f"Error enviando correo de log a {recipient_email}: {e}")



def send_execution_time_to_make(execution_time, clientes_atendidos):
    """Envía el tiempo de ejecución al Webhook de Make"""
    # URL del Webhook de Make
    WEBHOOK_URL = "https://hook.eu2.make.com/lhzxe7wsmyp7grdwq17jepke8myjgovg"
    minutes, seconds = divmod(execution_time, 60)
    formatted_time = f"{int(minutes)} min {seconds:.2f} sec"
    
    payload = {
        "FECHA": time.strftime("%Y-%m-%d %H:%M:%S"),
        "TIEMPO_EJECUCION": formatted_time,
        "CLIENTES_ATENDIDOS" : clientes_atendidos
    }
    
    response = requests.post(WEBHOOK_URL, json=payload)

    if response.status_code == 200:
        print("Tiempo de ejecución enviado correctamente a Make ✅")
    else:
        print(f"Error al enviar datos a Make ❌: {response.text}")

def medir_tiempo(func):
    def wrapper(*args, **kwargs):
        inicio = time.time()
        resultado = func(*args, **kwargs)
        fin = time.time()
        duracion = fin - inicio
        print(f"⏱️ '{func.__name__}' ejecutada en {duracion:.2f} segundos")
        return duracion
    return wrapper

@medir_tiempo
def main() -> None:
    """ejecucion principal del codigo"""
    start_time = time.time()

    print('Inciando Automatización...')
    df = obtener_datos_combinados()
    #df = pd.read_excel("prueba.xlsx")
    clientes_atendidos = generar_estado_de_cuenta_pdf_por_cliente_y_moneda(df)

    # Lista de correos electrónicos
    recipient_emails = ["cxc@samesacr.com", "dramirez@samesacr.com", "devs@techconnectors.co"]

    #Enviar el archivo log a cada uno de los correos electrónicos
    if clientes_atendidos == False:
        print('no se envia nada porque no hay clientes')
    else:
        for recipient_email in recipient_emails:
            send_log_by_email(recipient_email)
    
    end_time = time.time()
    elapsed_time = end_time - start_time

    # Enviar datos al Webhook de Make
    hoy = datetime.today().weekday()

    if hoy < 5:  # 0 a 4 = lunes a viernes
        pass
        #send_execution_time_to_make(elapsed_time, clientes_atendidos)
    else:
        print("Hoy es fin de semana. No se ejecuta nada 🚫")
    

if __name__ == "__main__":
    try:
        result_time = main()
        print("✅ Proceso completado exitosamente.", result_time)
        status_global_ejecution["tiempo_ejecucion"] = result_time
        hoy = datetime.today().weekday()
        if hoy < 5:
            registrar_ejecucion(status_global_ejecution)
        else:
            None
        #test_sharepoint_connection()
    except Exception as e:
        print(f"❌ Error crítico en ejecución: {e}")

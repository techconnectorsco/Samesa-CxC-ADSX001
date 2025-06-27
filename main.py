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
                    font-family: 'Arial', sans-serif;
                    color: #333333;
                    background-color: #f4f4f4;
                }}
                .container {{
                    width: 80%;
                    margin: 20px auto;
                    background-color: #ffffff;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);
                }}
                .content {{
                    font-size: 14px;
                    line-height: 1.5;
                }}
                .footer {{
                    text-align: center;
                    font-size: 12px;
                    color: #666666;
                    margin-top: 10px;
                    padding-top: 10px;
                    border-top: 1px solid #e0e0e0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="content">
                    <p>Adjunto se encuentra el archivo con los registros de los correos enviados para el estado de cuenta de hoy.</p>
                    <p>Saludos.</p>
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

def main():
    """ejecucion principal del codigo"""
    start_time = time.time()

    print('Inciando Automatización...')
    df = obtener_datos_combinados()
    #df = pd.read_excel("prueba.xlsx")
    clientes_atendidos = generar_estado_de_cuenta_pdf_por_cliente_y_moneda(df)

    # Lista de correos electrónicos
    recipient_emails = ["cxc@samesacr.com", "dramirez@samesacr.com", "devs@techconnectors.co"]

    #Enviar el archivo log a cada uno de los correos electrónicos
    for recipient_email in recipient_emails:
        send_log_by_email(recipient_email)
    
    end_time = time.time()
    elapsed_time = end_time - start_time

    # Enviar datos al Webhook de Make
    hoy = datetime.today().weekday()

    if hoy < 5:  # 0 a 4 = lunes a viernes
        send_execution_time_to_make(elapsed_time, clientes_atendidos)
    else:
        print("Hoy es fin de semana. No se ejecuta nada 🚫")
    

if __name__ == "__main__":
    main()

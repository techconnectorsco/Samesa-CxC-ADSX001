from datetime import datetime
from email.message import EmailMessage
import os
import smtplib
from fpdf import FPDF
from decouple import config
from sendToSharepoint import upload_file_to_sharepoint

class EmailLogPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.headers_added = False  # Flag para controlar si los encabezados ya se añadieron

    def header(self):
         if not self.headers_added:  # Solo agregar encabezados si aún no se han agregado
            self.image('SAMESA_LOG.jpg', 5, self.get_y(), 60)
            self.set_font('Arial', 'B', 14)
            self.cell(0, 8, 'Control de Correos Enviados', ln=1, align='C')
            self.cell(0, 6, 'Agencia Aduanal SAMESA S.A.', ln=1, align='C')


            current_datetime = datetime.now()
            self.set_font('Arial', '', 10)
            fecha_hora = f'Fecha: {current_datetime.strftime("%d/%m/%Y")}  Hora: {current_datetime.strftime("%I:%M %p")}'
            self.set_xy(-70, self.get_y())
            self.cell(60, 10, fecha_hora, 0, 1, 'R')

            self.ln(2)
            font_size = 14

            self.set_font('Arial', 'B', font_size)
            self.cell(0, 10, 'Estado de Cuenta Enviados', ln=1, align='C')

             # Añadir los encabezados solo una vez
            self.ln(2)
            self.set_font('Arial', 'B', 10)
            self.cell(90, 10, "Email", border=1, align='C')
            self.cell(35, 10, "Estado de Envío", border=1, align='C')
            self.cell(65, 10, "Error", border=1, align='C')
            self.ln(10)
            
            # Marcar que los encabezados han sido añadidos
            self.headers_added = True

        

    def footer(self):
        """
        Adds a custom footer to the PDF.

        The footer includes:
        - A horizontal line separating the content from the footer section.
        - The page number displayed on the bottom-left in the format 'Página X de {nb}'.
        - The company email ('estados@samesacr.com') aligned to the bottom-right.

        This method ensures that each page in the PDF has consistent footer information.
        """ 
        self.set_y(-15)
        self.set_draw_color(0)
        self.set_line_width(0.3)
        self.line(6, self.get_y(), 200, self.get_y())
        self.set_y(-12)
        self.set_font('Arial', 'B', 10)
        self.cell(0, 10, f'Página {self.page_no()} de {{nb}}', 0, 0, 'L')
        self.cell(0, 10, 'estados@samesacr.com', 0, 0, 'R')


    def add_log_entry(self, email, status, error_message=None):
        """
        Add a log entry to the PDF table immediately.
        
        Args:
            email (str): Email address to which the message was sent.
            status (str): 'Si' if the email was successfully sent, 'No' otherwise.
            error_message (str, optional): Error details if the email was not sent.
        """
        # Contenido: Logs individuales
        self.set_font('Arial', '', 10)
        self.cell(90, 8, email, border=1, align='C')
        self.cell(35, 8, status, border=1, align='C')
        self.cell(65, 8, error_message if error_message else 'N/A', border=1, align='C')
        self.ln()

def send_email(archivos_pdf, client_email, client_name, log_pdf, moneda, codigo_cliente):
    """Send the generated PDF via email and log the result."""

    if moneda == 'COL':
        moneda = 'CRC'

    # Reconstruct the output folder and Excel file path
    today = datetime.now().strftime('%d-%m-%y')
    current_directory = os.path.dirname(os.path.abspath(__file__))
    parent_directory = os.path.abspath(os.path.join(current_directory, ".."))
    output_folder = os.path.join(parent_directory, f"E.C._{today}_EXCEL")
    excel_path = os.path.join(output_folder, f"E.C._{codigo_cliente}.xlsx")

    # Si client_email es "NO_ENVIAR", solo subimos los archivos a SharePoint y retornamos
    if client_email == "NO_ENVIAR":
        try:
            # Subir los archivos a SharePoint (tanto PDF como Excel)
            upload_file_to_sharepoint(client_name, excel_path, file_type='excel')
            for pdf_path in archivos_pdf:
                upload_file_to_sharepoint(client_name, pdf_path, file_type='pdf')
            log_pdf.add_log_entry(client_email, "Si", "Archivos en el SharePoint")
            print(f"Archivos subidos a SharePoint para {client_name} sin enviar correo")
        except Exception as e:
            log_pdf.add_log_entry(client_email, "No", f"Error al subir archivos a SharePoint: {e}")
            print(f"Error al subir archivos a SharePoint: {e}")
        return  # Salir de la función sin enviar el correo

    from_email = config('SAMESA_EMAIL')
    password = config('SAMESA_EMAIL_PASS')
    to_email = client_email
    image_path = "info_SAMESA.png"
    logo_path = "SAMESA_LOG.jpg"

    # Email body (HTML format)
    body = f"""
        <html>
        <head>
            <style>
                /* Estilos generales */
                body {{
                    font-family: 'Arial', sans-serif;
                    color: #333333;
                    background-color: #f4f4f4;
                    margin: 0;
                    padding: 0;
                }}

                .container {{
                    width: 80%;
                    margin: 20px auto;
                    background-color: #ffffff;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);
                }}

                .header {{
                    text-align: center;
                    margin-bottom: 10px;
                }}

                .header img {{
                    width: 250px;
                    height: auto;
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

                .footer a {{
                    color: #0066cc;
                    text-decoration: none;
                    font-weight: bold;
                }}

                .footer a:hover {{
                    text-decoration: underline;
                }}

                .footer p {{
                    margin: 5px 0;
                }}

                .footer img {{
                width: 100%;
                max-width: 600px;
                height: auto;
                }}

                .highlight {{
                    color: #0066cc;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>

            <div class="container">
                <!-- Header with logo -->
                <div class="header">
                    <img src="cid:logo_samesa" alt="SAMESA Logo">
                </div>

                <!-- Main content -->
                <div class="content">
                    <p>Estimado Cliente: <span class="highlight">{client_name}</span></p>

                    <p>Adjunto a este mensaje encontrará el estado de cuenta actualizado al día de hoy.</p>
                    <p>Agradecemos su colaboración en verificar las facturas como el detalle de servicios liquidados, además de los montos que se detallan en su estado de cuenta. 
                    Si encuentra alguna inconsistencia por favor infórmenos lo antes posible para poder asistirle, así si realizo algún pago no incluido favor adjuntarlo a su correo de respuesta.</p>

                    <p>Es importante tener presente que las facturas detalladas en este estado de cuenta se han emitido bajo los términos y condiciones de los trabajos solicitados, aprobados como realizados por nuestra empresa, así acordado en el contrato y acuerdos entre empresas.</p>

                    <p>En el caso de que no exista consulta o desacuerdos entre las empresas, se tendrá como validos trascurridos 72 horas después del envió de este correo, al correo aprobado por la empresa como válidos y como lugar oficial para notificaciones para este tipo de información.
                    </p>
                    
                    <P>Nos complace informarles que ahora ponemos a su disposición el <strong>Sinpe Móvil 6015-1531</strong>
                    para pagos inferiores a <strong>100,000.00 colones.</strong> Esta opción les permitirá realizar sus pagos de manera rápida y segura</p>

                    <p>Cualquier consulta estamos a sus órdenes.</p>
                    <p><span class="highlight">Importante:</span><strong> Para responder a este correo, por favor hágalo escribiéndonos a <a href="mailto:cxc@samesacr.com">cxc@samesacr.com</a>.</strong>
                    <p>Saludos.</p>
                    
                </div>

                <!-- Footer -->
                <div class="footer">
                    <hr>
                    <img src="cid:info_samesa_footer" alt="Pie de Página SAMESA">
                    <hr>
                </div>
            </div>

        </body>
        </html>
    """

    # Crear el mensaje
    email = EmailMessage()
    email['From'] = from_email
    email['To'] = to_email
    email['Subject'] = "Estados de Cuenta - SAMESA S.A."
    email.set_content(body, subtype='html')

    # Adjuntar la imagen con un CID
    try:
        with open(image_path, 'rb') as img_file:
            email.add_attachment(
                img_file.read(),
                maintype='image',
                subtype='png',  # Cambiar el tipo si la imagen no es PNG
                filename="info_SAMESA.png",
                cid="info_samesa_footer" 
            )
    except Exception as e:
        print(f"Error adjuntando imagen: {e}")
        return

    # Adjuntar el archivo de Excel
    try:
        upload_file_to_sharepoint(client_name, excel_path, file_type='excel')
        with open(excel_path, 'rb') as excel_file:
            email.add_attachment(
                excel_file.read(),
                maintype='application',
                subtype='vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                filename=f"E.C. {client_name}.xlsx"
            )
    except FileNotFoundError:
        log_pdf.add_log_entry(client_email, "No", "Archivo de Excel no encontrado")
        print(f"Error: Archivo de Excel '{excel_path}' no encontrado.")
        return
    except Exception as e:
        log_pdf.add_log_entry(client_email, "No", f"Error adjuntando Excel: {e}")
        print(f"Error adjuntando Excel: {e}")
        return

    # Adjuntar el PDF
    for pdf_path in archivos_pdf:
        try:
            upload_file_to_sharepoint(client_name, pdf_path, file_type='pdf')
            with open(pdf_path, 'rb') as pdf_file:
                email.add_attachment(
                    pdf_file.read(),
                    maintype='application',
                    subtype='pdf',
                    filename=os.path.basename(pdf_path)
                )
        except Exception as e:
            log_pdf.add_log_entry(client_email, "No", "Error adjuntando PDF")
            print(f"Error adjuntando PDF: {e}")
            return

    # Adjuntar la imagen con un CID
    try:
        with open(logo_path, 'rb') as img_file:
            email.add_attachment(
                img_file.read(),
                maintype='image',
                subtype='png', 
                filename="SAMESA_LOG.png",
                cid="logo_samesa"  
            )
    except Exception as e:
        print(f"Error adjuntando imagen: {e}")
        return

    # Enviar el correo
    try:
        with smtplib.SMTP('smtp.office365.com', 587) as smtp:  # Usar SSL para seguridad
            smtp.ehlo()  # Saludar al servidor
            smtp.starttls()
            smtp.login(from_email, password)
            smtp.send_message(email)
        log_pdf.add_log_entry(client_email, "Si")
        masked_email = f"{client_email.split('@')[0][:3]}......@{client_email.split('@')[1]}"
        print(f"Correo enviado con exito a {masked_email}")
        return True  # Indicar que el envío fue exitoso
        #print(f"Correo enviado con exito a {client_email}")
    except smtplib.SMTPException as e:
        log_pdf.add_log_entry(client_email, "No", "Correo NO Enviado (verificar)")
        print(f"Error enviando correo a {client_email}: {e}")
        return False

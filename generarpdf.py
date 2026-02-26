import os
from datetime import datetime
import time
from fpdf import FPDF
import pandas as pd
import qrcode
import re

from generarEmail import EmailLogPDF, send_email
from generarExcel import generar_excels_por_cliente
from global_status import status_global_ejecution

class PDF(FPDF):
    """
        Custom PDF class inheriting from FPDF to generate account statements.

        This class defines the structure of the PDF, including the header 
        with the company logo and titles.
    """


    def header(self):
        """ 
        Adds a custom header to the PDF.

        The header includes:
        - The company logo positioned on the top-left.
        - A centered title ('Estado de Cuenta') and company name ('Agencia Aduanal SAMESA S.A.').
        - Preliminary contact and address information displayed as multiline text.
        - The current date and time aligned to the top-right.

        This method sets up the main structure and branding of the PDF header.
    
        """
        self.image('SAMESA_LOG.jpg', 5, self.get_y(), 60)
        self.set_font('Arial', 'B', 14)
        self.cell(0, 8, 'Estado de Cuenta', ln=1, align='C')
        self.cell(0, 6, 'Agencia Aduanal SAMESA S.A.', ln=1, align='C')
        self.ln(2)

        self.set_font('Arial', '', 10)
        self.multi_cell(0, 5, '''Cedula Juridica 3-101-093323\nTel: (506) 2215-25-36\nBodegas el Almendro local 11 Contiguo a Construplaza, Guachipelin, Escazú.
                ''', align='C')
        self.ln(2)

        current_datetime = datetime.now()
        self.set_font('Arial', '', 10)
        fecha_hora = f'Fecha: {current_datetime.strftime("%d/%m/%Y")}  Hora: {current_datetime.strftime("%I:%M %p")}'
        self.set_xy(-70, self.get_y())
        self.cell(60, 10, fecha_hora, 0, 1, 'R')

        qr = qrcode.QRCode(box_size=2, border=2)
        qr.add_data('https://www.samesacr.com')
        qr.make(fit=True)
        
        # Save the QR code as an image
        qr_img_path = 'temp_qr.png'
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_img.save(qr_img_path)
        
        self.image(qr_img_path, self.w - 30, 10, 20)
        

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


    def chapter_title(self, client_name, client_code, cedula):
        """
        Displays the chapter title with client information in the PDF.

        The title includes:
        - The client's name, displayed in uppercase and centered.
        - Font size dynamically adjusts based on the length of the name:
            - Default size: 14.
            - Medium length (50-70 characters): Reduced to 12.
            - Long length (>70 characters): Reduced to 10.
        - The client's identification code (Cédula Jurídica), displayed below the name.
        - The client code ('Codigo de Cliente'), displayed further below in bold.

        After rendering the information, it adds spacing for better layout.

        Args:
            client_name (str): The name of the client.
            client_code (str): The client's identification code and unique client code.
            cedula (str): the client's code number
        """
      
        font_size = 14

        # Adjust font size based on the length of the client name
        if 50 < len(client_name) < 70:
            font_size = 12
            self.set_font('Arial', 'B', font_size)
            self.cell(0, 10, client_name.upper(), ln=1, align='C')
        elif len(client_name)> 70:
            font_size = 10
            self.set_font('Arial', 'B', font_size)
            self.cell(0, 10, client_name.upper(), ln=1, align='C')
        else:
            self.set_font('Arial', 'B', font_size)
            self.cell(0, 10, client_name.upper(), ln=1, align='C')
        self.set_font('Arial', 'B', 12)
        if not cedula or pd.isna(cedula):  # pd.isna verifica si es NaN
            cedula = 'No tiene'
        self.cell(0, 10, f'Cédula Jurídica: {cedula}', ln=1, align='C')
        self.ln(2)
        self.set_font('Arial', 'B', 10)
        self.cell(0, 10, f'Codigo de Cliente: {client_code}', ln=1)
        self.ln(2)

    def add_table(self, data, moneda):
        """
        Adds two tables to the PDF: Account statement details and overdue amounts.

        The first table includes:
        - Document information (e.g., invoice number, dates, amounts, balance).
        - Dynamically calculates the accumulated balance.
        - Ends with a row displaying the total account balance.

        The second table includes:
        - Overdue amount ranges (e.g., 0-30 days, 31-60 days, etc.).
        - Dynamically calculates the overdue amounts and their percentages of the total.
        - Highlights values: "Sin Vencer" in green if non-zero, others in red.

        Args:
            data (list): A list of rows containing document data. Each row should include:
                - [0]: Document number (str).
                - [1]: Document date (str or datetime).
                - [2]: Due date (str or datetime).
                - [4]: Pending amount (float).
                - [5]: Recibe Number (str)
            moneda (str): The currency symbol to display (e.g., 'USD', 'CRC').
        """

        print(f"Total de facturas para el cliente: {len(data)}",)
        self.set_font('Arial', 'B', 9)
        col_widths = [25, 25, 33, 33, 37, 37] 
        headers = [
            "Factura", "No. Recibo", "Fecha Factura", "Fecha Vencimiento", "Importe Facturado", "Saldo de Cuenta"
        ]

        for header, width in zip(headers, col_widths):
            self.cell(width, 10, header, border=1, align="C")
        self.ln() 

        self.set_font('Arial', '', 10)
        saldo_acumulado = 0 
        facturas_en_primera_tabla = 0 
        #facturas_total = len(data)  # Total de facturas

        for row in data:
            documento = row[0]  # Número de factura
            recibo_tramite = str(row[5])
            fecha_documento = row[1]  # Fecha de la factura
            fecha_vencimiento = row[2]  # Fecha de vencimiento
            
            if isinstance(fecha_documento, str):
                fecha_documento = fecha_documento.split(" ")[0]
            else:
                fecha_documento = fecha_documento.strftime('%d/%m/%Y') #ojo

            if isinstance(fecha_vencimiento, str):
                fecha_vencimiento = fecha_vencimiento.split(" ")[0]
            else:
                fecha_vencimiento = fecha_vencimiento.strftime('%d/%m/%Y') #ojo

            importe_doc = float(row[4])
            saldo_acumulado += importe_doc

            importe_doc_con_moneda = f"{moneda.upper()}  {importe_doc:,.2f}"
            saldo_acumulado_con_moneda = f"{moneda.upper()}  {saldo_acumulado:,.2f}"

            # Modificación para el campo 'recibo_tramite'
            if recibo_tramite is not None and len(recibo_tramite) > 12:
                recibo_principal = recibo_tramite[:6]
                mas = (len(recibo_tramite) - 6) // 6
                if mas > 0:
                    recibo_tramite = f"{recibo_principal}, +{mas}"
                else:
                    recibo_tramite = recibo_principal
            elif recibo_tramite is None:
                recibo_tramite = ""
        

            fila = [
                documento, recibo_tramite, fecha_documento, fecha_vencimiento, importe_doc_con_moneda, saldo_acumulado_con_moneda
            ]
            
            if len(data) == 10 :
                for value, width in zip(fila, col_widths):
                    self.cell(width, 9, str(value), border=1, align="C")
                self.ln()
            else:
                for value, width in zip(fila, col_widths):
                    self.cell(width, 10, str(value), border=1, align="C")
                self.ln()

            facturas_en_primera_tabla += 1

         # Si tenemos entre 5 y 9 facturas, hacer salto de página antes de la segunda tabla
        

        self.set_font('Arial', 'B', 10)
        self.cell(col_widths[0] + col_widths[1] + col_widths[2] + col_widths[3], 10, "Total del Estado de Cuenta :", border=1, align="L")  # Fila para el total
        self.cell(col_widths[4] + col_widths[5], 10, f"{moneda.upper()}  {saldo_acumulado:,.2f}", border=1, align="R")  # Saldo total
        self.ln()

        if 5 <= facturas_en_primera_tabla <= 9:
            self.add_page()

            # Salto de página según los rangos de facturas procesadas en la primera tabla
        if 27 <= facturas_en_primera_tabla <= 29:
            self.add_page()
        elif 48 <= facturas_en_primera_tabla <= 50:
            self.add_page()
        elif 69 <= facturas_en_primera_tabla <= 71:
            self.add_page()
        elif 90 <= facturas_en_primera_tabla <= 92:
            self.add_page()
        elif 111 <= facturas_en_primera_tabla <= 113:
            self.add_page()
        elif 122 <= facturas_en_primera_tabla <= 124:
            self.add_page()
        elif 143 <= facturas_en_primera_tabla <= 145:
            self.add_page()
        elif 164 <= facturas_en_primera_tabla <= 165:
            self.add_page()
        elif 185 <= facturas_en_primera_tabla <= 187:
            self.add_page()
        elif 206 <= facturas_en_primera_tabla <= 208:
            self.add_page()
        elif 227 <= facturas_en_primera_tabla <= 229:
            self.add_page()
        elif 248 <= facturas_en_primera_tabla <= 250:
            self.add_page()
        elif 269 <= facturas_en_primera_tabla <= 271:
            self.add_page()

        #Second table: Overdue amounts       
        self.ln(3)
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Total Vencimiento', ln=1, align='C')

        
        # Headers
        headers = ['Total', 'Sin Vencer', '0-30', '31-60', '61-90', '91-120', '+121']
        col_widths = [28, 27, 27, 27, 27, 27, 27]

        sin_vencer = 0
        rango_0_30 = 0
        rango_31_60 = 0
        rango_61_90 = 0
        rango_91_120 = 0
        rango_121_mas = 0

        fecha_actual = datetime.now()

        for row in data:
            fecha_vencimiento = row[2]
            monto = float(row[4])

            if isinstance(fecha_vencimiento, str):
                fecha_vencimiento = datetime.strptime(fecha_vencimiento, '%d/%m/%Y')

            dias_vencidos = (fecha_actual - fecha_vencimiento).days


            if dias_vencidos <= 0: 
                sin_vencer += monto
            elif 1 <= dias_vencidos <= 30:
                rango_0_30 += monto
            elif 31 <= dias_vencidos <= 60:
                rango_31_60 += monto
            elif 61 <= dias_vencidos <= 90:
                rango_61_90 += monto
            elif 91 <= dias_vencidos <= 120:
                rango_91_120 += monto
            else:
                rango_121_mas += monto

        total = f"{moneda.upper()} {saldo_acumulado:,.2f}"
        sin_vencer = f"{moneda.upper()} {sin_vencer:,.2f}"
        rango_0_30 = f"{moneda.upper()} {rango_0_30:,.2f}"
        rango_31_60 = f"{moneda.upper()} {rango_31_60:,.2f}"
        rango_61_90 = f"{moneda.upper()} {rango_61_90:,.2f}"
        rango_91_120 = f"{moneda.upper()} {rango_91_120:,.2f}"
        rango_121_mas = f"{moneda.upper()} {rango_121_mas:,.2f}"

        self.set_font('Arial', 'B', 9)
        for header, width in zip(headers, col_widths):
            self.cell(width, 10, header, border=1, align='C')
        self.ln()

        if saldo_acumulado >= 100_000_000:
            self.set_font('Arial', '', 7)
        elif saldo_acumulado >= 10_000_000:
            self.set_font('Arial', '', 8)
        elif saldo_acumulado >= 1_000_000:
            self.set_font('Arial', '', 9)
        elif saldo_acumulado >= 100_000:
            self.set_font('Arial', '', 10)
        else:
            self.set_font('Arial', '', 11)
        
        fila = [total, sin_vencer, rango_0_30, rango_31_60, rango_61_90, rango_91_120, rango_121_mas]
        for value, width in zip(fila, col_widths):
            self.cell(width, 10, value, border=1, align='C')
        self.ln()

        porcentajes = [
            100.0,
            (float(sin_vencer.replace(f"{moneda.upper()} ", "").replace(",", "")) / saldo_acumulado * 100) if saldo_acumulado > 0 else 0,
            (float(rango_0_30.replace(f"{moneda.upper()} ", "").replace(",", "")) / saldo_acumulado * 100) if saldo_acumulado > 0 else 0,
            (float(rango_31_60.replace(f"{moneda.upper()} ", "").replace(",", "")) / saldo_acumulado * 100) if saldo_acumulado > 0 else 0,
            (float(rango_61_90.replace(f"{moneda.upper()} ", "").replace(",", "")) / saldo_acumulado * 100) if saldo_acumulado > 0 else 0,
            (float(rango_91_120.replace(f"{moneda.upper()} ", "").replace(",", "")) / saldo_acumulado * 100) if saldo_acumulado > 0 else 0,
            (float(rango_121_mas.replace(f"{moneda.upper()} ", "").replace(",", "")) / saldo_acumulado * 100) if saldo_acumulado > 0 else 0
        ]

        porcentajes = [f"{porcentaje:.2f}%" for porcentaje in porcentajes]

        self.set_font('Arial', 'B', 9)  # Fuente en negrita para los porcentajes
        for i, (porcentaje, width) in enumerate(zip(porcentajes, col_widths)):
            if i == 1 and porcentaje != "0.00%":
                self.set_text_color(0, 128, 0)  # Verde
            elif i > 1 and porcentaje != "0.00%":
                self.set_text_color(255, 0, 0)  # Rojo
            else:
                self.set_text_color(0, 0, 0)  # Negro

            self.cell(width, 10, porcentaje, border=1, align='C')

        self.ln() 
        self.set_text_color(0, 0, 0) 
    

    def bank_accounts_section(self):
        """
        Adds a section to the PDF displaying the details of bank accounts 
        organized by bank. Each bank includes IBAN account numbers for 
        colones and dollars.

        The section is formatted with two columns, separating the banks 
        for better readability. Headers are displayed in bold, and account 
        details use a smaller font size.

        This method adjusts the x and y coordinates to properly align 
        content in the PDF.

        Banks included:
        - Banco BCT
        - Banco Nacional de Costa Rica
        - BAC Credomatic
        - Banco BCR
        """
        self.set_font('Arial', 'B', 10)
        self.cell(0, 10, 'Cuentas Bancarias:', ln=1)
        
        self.set_xy(10, self.get_y())
        self.set_font('Arial', 'B', 10)
        self.cell(90, 5, 'Banco BCT', ln=0)
        self.set_xy(10, self.get_y() + 5)
        self.set_font('Arial', '', 9)
        self.cell(90, 5, 'Cuenta IBAN Colones: CR41010700000000059950', ln=0)
        self.set_xy(10, self.get_y() + 5)
        self.cell(90, 5, 'Cuenta IBAN Dolares: CR77010700000000059981', ln=0)

        self.set_xy(110, self.get_y() - 10)
        self.set_font('Arial', 'B', 10)
        self.cell(90, 5, 'Banco Nacional de Costa Rica', ln=0)
        self.set_xy(110, self.get_y() + 5)
        self.set_font('Arial', '', 9)
        self.cell(90, 5, 'Cuenta IBAN Colones: CR66015108410010015301', ln=0)
        self.set_xy(110, self.get_y() + 5)
        self.cell(90, 5, 'Cuenta IBAN Dolares: CR86015100010026231724', ln=0)

        self.ln(8)

        self.set_xy(10, self.get_y())
        self.set_font('Arial', 'B', 10)
        self.cell(90, 5, 'BAC Credomatic', ln=0)
        self.set_xy(10, self.get_y() + 5)
        self.set_font('Arial', '', 9)
        self.cell(90, 5, 'Cuenta IBAN Colones: CR82010200009094245589', ln=0)
        self.set_xy(10, self.get_y() + 5)
        self.cell(90, 5, 'Cuenta IBAN Dolares: CR62010200009417358478', ln=0)

        self.set_xy(110, self.get_y() - 10)
        self.set_font('Arial', 'B', 10)
        self.cell(90, 5, 'Banco BCR', ln=0)
        self.set_xy(110, self.get_y() + 5)
        self.set_font('Arial', '', 9)
        self.cell(90, 5, 'Cuenta IBAN Colones: CR89015201001049730899', ln=0)
        self.set_xy(110, self.get_y() + 5)
        self.cell(90, 5, 'Cuenta IBAN Dolares: CR07015201001050020950', ln=0)

        self.ln(8) 

        self.set_font('Arial', 'B', 9)
        self.cell(0, 10, 'Sinpe Móvil 6015-1531 para pagos inferiores a 100,000.00 colones', ln=1)

    def add_note(self):
        """
        Adds a special note section to the PDF explaining the numbering system 
        for documents. It differentiates between electronic documents and 
        cost and tax liquidation documents.

        The text is styled in italic with a smaller font size for emphasis 
        and uses multi-line formatting to fit the content properly within 
        the PDF layout.
        """
        self.set_font('Arial', 'I', 8)
        self.multi_cell(0, 5, '''Las numeraciones que inician con 10000XXXXX, corresponden a Documentos Electrónicos.
Las numeraciones de 6 dígitos corresponden a la liquidación de costos e impuestos.
            ''')
        self.ln(3)


def generar_estado_de_cuenta_pdf_por_cliente_y_moneda(df):
    """
    Generates account statement PDFs for each client and currency, grouped by unique client codes 
    and currency types. Creates a folder with the current date to store the generated PDFs.

    Args:
        df (DataFrame): Pandas DataFrame containing the data for account statements. 
                        Must include columns 'Código Cliente', 'Cliente', 'Moneda', 'Número Factura', 
                        'Fecha Factura', 'Fecha Vencimiento', and 'Monto Pendiente [Currency]'.
        ruta_salida_base (str): Base directory path where the PDF files will be saved.
    """
    
    # Mapear los días de la semana
    dias_semana = {
        0: 'L',  # Lunes
        1: 'K',  # Martes
        2: 'M',  # Miércoles
        3: 'J',  # Jueves
        4: 'V',  # Viernes
    }

    hoy = datetime.now().weekday()
    dia_actual = dias_semana.get(hoy, None)

    # if dia_actual is None:
    #     print("Hoy no es un día hábil. El script no se ejecutará.")
    # else:
    #     print("El script puede ejecutarse.")


    def filtrar_por_dia(dias_tramite):
        """
            Filters records based on the specified processing days.

            Args:
                dias_tramite (str): A string containing the days assigned for processing,
                                    separated by hyphens (e.g., 'L-M-V'). It can also be
                                    empty or NaN.

            Returns:
                bool: True if the current day matches any of the specified processing days
                    or if the field is empty/NaN and defaults to Saturday ('S'). 
                    False otherwise.

            Notes:
                - Defaults to 'L' (Monday) if the field is empty or NaN.
                - Supports multiple processing days separated by hyphens (e.g., 'L-M-V').
        """
        
        if pd.isna(dias_tramite) or dias_tramite.strip() == "":
            return dia_actual == 'L'  # Asignar lunes si no tiene días de trámite
        return dia_actual in dias_tramite.split("-")

    df_filtrado = df[df["Días de Trámite"].apply(filtrar_por_dia)]

    if df_filtrado.empty:
        print(f"No hay clientes para procesar en el día: {dia_actual}.")
        status_global_ejecution["observaciones"] = "No Hubo clientes para procesar"
        return False


    today = datetime.now().strftime('%d-%m-%y')
    current_directory = os.path.dirname(os.path.abspath(__file__))
    parent_directory = os.path.abspath(os.path.join(current_directory, ".."))
    output_folder = os.path.join(parent_directory, f"E.C._{today}")
    log_folder = os.path.join(parent_directory, f"Email_Logs_E.C._{today}")
    create_and_wait_for_directory(output_folder)
    create_and_wait_for_directory(log_folder)

    log_pdf = EmailLogPDF()
    log_pdf.add_page()

    
    clientes = df_filtrado["Código Cliente"].unique()
    status_global_ejecution["clientes_procesados"] = len(clientes)
    enviado_prueba = 0 # Variable para controlar el envío de 
    
     # Inicializar contadores para ir acumulando:
    total_documentos = 0
    reportes_generados = 0
    emails_exitosos = 0
    emails_fallidos = 0
    monto_total_usd = 0.0
    monto_total_colones = 0.0

    generar_excels_por_cliente(df_filtrado)

    for cliente in clientes:
        df_cliente = df_filtrado[df_filtrado["Código Cliente"] == cliente]
        nombre_cliente = df_cliente["Cliente"].iloc[0]
        cedula_juridica = df_cliente["Cedula Juridica"].iloc[0]
        monedas = df_cliente["Moneda"].unique()
        correos_cliente = df_cliente["Correo Electrónico"].iloc[0]

        # Acumula documentos del cliente:
        total_documentos += len(df_cliente)

        if pd.isna(correos_cliente) or correos_cliente.strip().upper() == "NO ENVIAR E.C." or correos_cliente.strip() == "":
            #print(f"No se enviará correo para el cliente {nombre_cliente} debido a datos inválidos o instrucción de 'NO ENVIAR E.C.'.")
            lista_correos = ["NO_ENVIAR"]  # Asignar marcador para enviar solo a SharePoint
        else:
            if ',' in correos_cliente:
                correos_cliente = correos_cliente.replace(",", ";")
            lista_correos = [correo.strip() for correo in correos_cliente.split(";") if correo.strip() != ""]        

        archivos_pdf = []

        for moneda in monedas:
            df_moneda = df_cliente[df_cliente["Moneda"] == moneda]

            pdf = PDF()  
            pdf.alias_nb_pages()
            pdf.add_page()
            pdf.chapter_title(nombre_cliente, cliente, cedula_juridica)
            pdf.bank_accounts_section()
            pdf.add_note()
            moneda = moneda.upper()

            if moneda in {"COL", "CRC"}:
                monto_columna = "Monto Pendiente CRC"
                moneda = "CRC"
            elif moneda == "USD":
                monto_columna = "Monto Pendiente USD"
            else:
                raise ValueError(f"Moneda no reconocida: {moneda}")
            
            df_moneda = df_moneda.sort_values(by="Fecha Factura", ascending=True)
            data = df_moneda[["Número Factura", "Fecha Factura", "Fecha Vencimiento", "Moneda", monto_columna, "Recibo"]].values.tolist()
            pdf.add_table(data, moneda)
            nombre_cliente_sanitizado = limpiar_nombre_archivo(nombre_cliente)
            ruta_salida = f"{output_folder}/E.C_{nombre_cliente_sanitizado}_PARTE_{moneda}.pdf"
            pdf.output(ruta_salida)
            archivos_pdf.append(ruta_salida)
            reportes_generados += 1

             # Aquí acumulas el total por moneda
            if moneda == "USD":
                monto_total_usd += df_moneda[monto_columna].sum()
            elif moneda == "CRC":
                monto_total_colones += df_moneda[monto_columna].sum()

        # if enviado_prueba <= 2:
        #     correos_prueba = ["devs@techconnectors.co"]  # Lista de correos de prueba
        #     for correo_prueba in lista_correos:
        #         send_email(archivos_pdf, correo_prueba, nombre_cliente_sanitizado, log_pdf, moneda, cliente)
        #         print(f"Correo de prueba enviado a {correo_prueba}")
        #     enviado_prueba += 1

        #ENVÍO REAL (DESCOMENTAR EN PRODUCCIÓN)
        #AHORA VALIDAMOS SI HAY CORREOS VALIDOS ENTNCES SE ENVIA SINO DA UN MENSAJE
        if lista_correos:
            for correo in lista_correos:
                exito = send_email(archivos_pdf, correo, nombre_cliente_sanitizado, log_pdf, moneda, cliente)
                if exito:
                    emails_exitosos += 1
                else:
                    emails_fallidos += 1
                # print(f"Correo enviado a {correo}")
        else:
            print("La lista de correo esta vacia revisar")
        
    # Actualiza el status global con totales acumulados
    status_global_ejecution["total_documentos_procesados"] = total_documentos
    status_global_ejecution["reportes_generados"] = reportes_generados
    status_global_ejecution["emails_exitosos"] = emails_exitosos
    status_global_ejecution["emails_fallidos"] = emails_fallidos
    status_global_ejecution["monto_total_usd"] = round(monto_total_usd, 2)
    status_global_ejecution["monto_total_colones"] = round(monto_total_colones, 2)


    log_path = f"{log_folder}/email_logs_{today}.pdf"
    log_pdf.output(log_path)
    return len(clientes)


def create_and_wait_for_directory(path, timeout=15):
    """
    Crea una carpeta si no existe y espera hasta que esté disponible.
    
    :param path: Ruta de la carpeta.
    :param timeout: Tiempo máximo de espera para confirmar que la carpeta existe.
    """
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Carpeta creada: {path}")
    
    # Esperar hasta que la carpeta exista
    start_time = time.time()
    while not os.path.exists(path):
        if time.time() - start_time > timeout:
            raise TimeoutError(f"No se pudo crear la carpeta en el tiempo esperado: {path}")
        time.sleep(0.5) 

def limpiar_nombre_archivo(nombre):
    """
        Cleans a file name by replacing invalid characters with hyphens.

        Args:
            nombre (str): The original file name that may contain invalid characters.

        Returns:
            str: A sanitized file name with invalid characters replaced by hyphens ('-').

        Notes:
            - Replaces characters with -.
            - Ensures the resulting file name is safe for use in most file systems.
    """
    return re.sub(r'[<>:"/\\|?*]', '-', nombre)
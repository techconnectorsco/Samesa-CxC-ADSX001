from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from datetime import datetime

# Configuración
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = "1WW6irwNZ0NVtZH6X6v1IU9p4TPBCP8N37_AHEPiNGKA"  # Cambia por tu ID real
SHEET_NAME = "Hoja 1"
SHEET_ID = 0  # Normalmente 0 para la primera hoja

# Autenticación
creds = Credentials.from_service_account_file("GOOGLE-CREDENTIALS.json", scopes=SCOPES)
service = build("sheets", "v4", credentials=creds)

def aplicar_formato_fecha():
    requests = [{
        "repeatCell": {
            "range": {
                "sheetId": SHEET_ID,
                "startColumnIndex": 0,
                "endColumnIndex": 1
            },
            "cell": {
                "userEnteredFormat": {
                    "numberFormat": {
                        "type": "DATE_TIME",
                        "pattern": "dd/mm/yyyy hh:mm:ss"
                    }
                }
            },
            "fields": "userEnteredFormat.numberFormat"
        }
    }]
    # type: ignore
    response = service.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body={"requests": requests}
    ).execute()
    print("✅ Formato fecha/hora aplicado a la columna A")

def registrar_ejecucion(status_global):
    aplicar_formato_fecha()
    values = [[
        status_global.get("fecha_ejecucion", datetime.now().strftime("%d/%m/%Y %H:%M:%S")),
        status_global.get("tiempo_ejecucion", ""),
        status_global.get("clientes_procesados", 0),
        status_global.get("total_documentos_procesados", 0),
        status_global.get("reportes_generados", 0),
        status_global.get("emails_exitosos", 0),
        status_global.get("emails_fallidos", 0),
        status_global.get("tipo_ejecucion", ""),
        status_global.get("fuente", ""),
        status_global.get("monto_total_usd", 0.0),
        status_global.get("monto_total_colones", 0.0),
        status_global.get("observaciones", ""),

    ]]
    body = {"values": values}
    # type: ignore
    response = service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A:K",
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body=body
    ).execute()
    print("✅ Fila insertada con formato en Google Sheets")

if __name__ == "__main__":
    # Cambia esta variable con tus datos reales o prueba con el ejemplo
    status_global_ejecution = {
        "fecha_ejecucion": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "tiempo_ejecucion": 123.45,
        "clientes_procesados": 18,
        "total_documentos_procesados": 40,
        "reportes_generados": 18,
        "emails_exitosos": 17,
        "emails_fallidos": 1,
        "tipo_ejecucion": "Automatica",
        "fuente": "Vedova&Obando Automation",
        "monto_total_usd": 1000.0,
        "monto_total_colones": 500000.0,
        "observaciones": 'test'
    }

    
    registrar_ejecucion(status_global_ejecution)
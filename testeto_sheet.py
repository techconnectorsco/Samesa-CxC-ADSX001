import pandas as pd
from datetime import datetime

# Importa tu función desde donde esté definida
from generarpdf import generar_estado_de_cuenta_pdf_por_cliente_y_moneda
from global_status import status_global_ejecution
from google_sheet_log import registrar_ejecucion

# Simulación de un DataFrame con datos mínimos válidos
data = [
    {
        "Código Cliente": "C001",
        "Cliente": "Cliente de Prueba S.A.",
        "Cedula Juridica": "3-101-123456",
        "Correo Electrónico": "test@example.com",
        "Días de Trámite": "L-M-V",
        "Moneda": "USD",
        "Número Factura": "F001",
        "Fecha Factura": datetime(2024, 6, 15),
        "Fecha Vencimiento": datetime(2024, 7, 15),
        "Monto Pendiente USD": 150.75,
        "Monto Pendiente CRC": 0,
        "Recibo": "R001"
    },
    {
        "Código Cliente": "C001",
        "Cliente": "Cliente de Prueba S.A.",
        "Cedula Juridica": "3-101-123456",
        "Correo Electrónico": "test@example.com",
        "Días de Trámite": "L-M-V",
        "Moneda": "CRC",
        "Número Factura": "F002",
        "Fecha Factura": datetime(2024, 6, 20),
        "Fecha Vencimiento": datetime(2024, 7, 20),
        "Monto Pendiente USD": 0,
        "Monto Pendiente CRC": 52500.00,
        "Recibo": "R002"
    },
    {
        "Código Cliente": "C001",
        "Cliente": "Cliente de Prueba S.A.",
        "Cedula Juridica": "3-101-123456",
        "Correo Electrónico": "test@example.com",
        "Días de Trámite": "L-M-V",
        "Moneda": "CRC",
        "Número Factura": "F002",
        "Fecha Factura": datetime(2024, 6, 20),
        "Fecha Vencimiento": datetime(2024, 7, 20),
        "Monto Pendiente USD": 0,
        "Monto Pendiente CRC": 52500.00,
        "Recibo": "R002"
    },
]

df_prueba = pd.DataFrame(data)

# Llamar la función
generar_estado_de_cuenta_pdf_por_cliente_y_moneda(df_prueba)
status_global_ejecution["tiempo_ejecucion"] = 19.36
registrar_ejecucion(status_global_ejecution)



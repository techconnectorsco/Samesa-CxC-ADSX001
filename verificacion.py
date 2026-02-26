import pandas as pd
from db_connection import get_db_connection


def verificacion():

    pd.set_option('display.max_columns', None)
    pd.set_option('display.expand_frame_repr', False)

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
        
        # Ejecutar consultas y cargar resultados en DataFrames
        df_facturas = pd.read_sql_query(query_facturas, conn)
        df_clientes = pd.read_sql_query(query_clientes, conn)
        
        # Exportar datos crudos a archivos separados
        df_facturas.to_excel('datos_crudos_facturas.xlsx', index=False, engine='openpyxl')
        df_clientes.to_excel('datos_crudos_clientes.xlsx', index=False, engine='openpyxl')
        
        print("Archivos Excel generados exitosamente:")
        print("- datos_crudos_facturas.xlsx")
        print("- datos_crudos_clientes.xlsx")
        
        # Realizar la unión de ambos DataFrames por "Código Cliente"
        df_combined = pd.merge(df_facturas, df_clientes, on="Código Cliente", how="inner")
        
        # Exportar los datos combinados a un archivo Excel
        df_combined.to_excel('datos_combinados.xlsx', index=False, engine='openpyxl')
        
        print("- datos_combinados.xlsx (Datos combinados por 'Código Cliente')")
        
        # Cerrar conexión
        conn.close()
    except Exception as e:
        print("Error:", e)

verificacion()
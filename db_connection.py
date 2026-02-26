#import pyodbc
from sqlalchemy import create_engine
from decouple import config

def get_db_connection():
    """
    Establece y devuelve una conexión a la base de datos SQL Server.

    :return: engine.Connect
    """

   
    server = config('SAMESA_SERVER')
    database = config('SAMESA_DATABASE')
    user= config('SAMESA_USER')
    password= config('SAMESA_PASSWORD')
    connection_string = (
    f"mssql+pyodbc://{user}:{password}@{server}/{database}"
    "?driver=ODBC+Driver+17+for+SQL+Server")
    engine = create_engine(connection_string)
     

    try:
        conn = engine.connect()
        #conn = pyodbc.connect(connection_string)
        print("Conexión Exitosa a la Base de Datos.")
        return conn
    except Exception as e:
        print("Error al conectar a la base de datos:", e)
        raise

#get_db_connection()
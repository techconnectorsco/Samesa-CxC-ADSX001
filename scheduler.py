import logging
import schedule
import time
import threading
import subprocess
import os

# Configurar logging
logging.basicConfig(
    filename='schedule_log.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
# Función principal
def run_task():
    logging.info("Executing the main script...")
    print("Executing the main script...")
    # Obtener la ruta relativa al directorio actual del script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    main_path = os.path.join(current_dir, "main.py")
    try:
        # Ejecutar el archivo main.py
        subprocess.run(["python", main_path], check=True)
        print("Main script executed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error while executing the script: {e}")

# Función que ejecuta schedule en un hilo separado
def schedule_task():
    #schedule.every().day.at("HH:MM").do(run_task)
    schedule.every().sunday.at("19:42").do(run_task)
    while True:
        schedule.run_pending()
        time.sleep(1)

# Iniciar schedule en un hilo
thread = threading.Thread(target=schedule_task)
thread.daemon = True
thread.start()

# Otra lógica que puede coexistir con schedule
while True:
    # Aquí puedes agregar más código si es necesario
    time.sleep(10)
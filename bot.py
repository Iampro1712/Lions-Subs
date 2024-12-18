import threading
import mysql.connector
import logging
import os
import importlib
from pyrogram import Client
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import sys
from dotenv import load_dotenv

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot_logs.log", encoding="utf-8"),  # Archivo con soporte UTF-8
        logging.StreamHandler(sys.stdout)  # Consola con soporte UTF-8
    ]
)

# Configuración del bot
load_dotenv()

api_id = os.getenv('api_id')
api_hash = os.getenv('api_hash')
bot_token = os.getenv('bot_token')

print("Importado Correctamente")

app = Client("mi_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# Variables globales
PREFIXES = ["/", ".", ",", "$", "#", "@", "&", "!", "?", "-"]
commands_dir = "commands"

# Cargar módulos de la carpeta commands
registered_commands = []

for filename in os.listdir(commands_dir):
    if filename.endswith(".py") and filename != "__init__.py":
        module_name = f"{commands_dir}.{filename[:-3]}"
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, "register_command"):
                commands = module.register_command(app)
                if not commands:
                    logging.warning(f"⚠️ El módulo {module_name} no registró ningún comando.")
                else:
                    registered_commands.extend(commands)
                    logging.info(f"✅ Comando registrado desde el módulo: {module_name}. Comandos: {', '.join(commands)}")
            else:
                logging.warning(f"⚠️ El módulo {module_name} no contiene la función register_command. Ignorado.")
        except Exception as e:
            logging.error(f"❌ Error al cargar el módulo {module_name}: {e}")

# Conexión a la base de datos
def connect_db():
    try:
        connection = mysql.connector.connect(
            host=os.getenv("host"),
            port=int(os.getenv("port")),
            user=os.getenv("user"),
            password=os.getenv("password"),
            database=os.getenv("database")
        )
        cursor = connection.cursor(dictionary=True)
        return connection, cursor
    except mysql.connector.Error as e:
        logging.error(f"❌ Error al conectar a la base de datos: {e}")
        return None, None

# Crear tabla de suscripciones si no existe y agregar la columna 'diamond' si no está
def initialize_db():
    conexion, cursor = connect_db()
    if not conexion or not cursor:
        logging.error("❌ No se pudo inicializar la base de datos debido a problemas de conexión.")
        return

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS subscriptions (
        user_id BIGINT PRIMARY KEY,
        start_date DATETIME,
        end_date DATETIME,
        premium TINYINT DEFAULT 0,
        diamond TINYINT DEFAULT 0
    )
    """)

    cursor.execute("SHOW COLUMNS FROM subscriptions LIKE 'diamond';")
    column_exists = cursor.fetchone()

    if not column_exists:
        cursor.execute("ALTER TABLE subscriptions ADD COLUMN diamond TINYINT DEFAULT 0;")
        logging.info("Columna 'diamond' añadida a la tabla 'subscriptions'.")

    conexion.commit()
    conexion.close()

# Inicializar la base de datos
initialize_db()

# Configuración del Scheduler
scheduler = BackgroundScheduler()

def notify_expired_subscriptions():
    """Notifica a los usuarios con suscripciones expiradas y actualiza su estado."""
    conexion, cursor = connect_db()
    if not conexion or not cursor:
        logging.error("No se pudo conectar a la base de datos para verificar suscripciones expiradas.")
        return

    cursor.execute("SELECT user_id, end_date, diamond FROM subscriptions WHERE premium = 1 OR diamond = 1")
    subscriptions = cursor.fetchall()

    now = datetime.now()
    for subscription in subscriptions:
        user_id = subscription["user_id"]
        end_date = subscription["end_date"]
        is_diamond = subscription["diamond"]

        end_date_dt = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S")
        if now > end_date_dt:  # Si la suscripción ha expirado
            try:
                rango = "Diamond" if is_diamond else "Premium"
                app.send_message(user_id, f"Tu suscripción {rango} ha expirado. 😔 Considera renovarla.")
                logging.info(f"Notificación enviada al usuario {user_id} por suscripción {rango} expirada.")
                
                if is_diamond:
                    cursor.execute("UPDATE subscriptions SET diamond = 0 WHERE user_id = %s", (user_id,))
                else:
                    cursor.execute("UPDATE subscriptions SET premium = 0 WHERE user_id = %s", (user_id,))
                conexion.commit()
                logging.info(f"Estado actualizado a 'no {rango.lower()}' para el usuario {user_id}.")
            except Exception as e:
                logging.error(f"No se pudo notificar al usuario {user_id}: {e}")

    conexion.close()

# Programar la tarea para ejecutarse cada 30 minutos
scheduler.add_job(notify_expired_subscriptions, "interval", minutes=30)

# Función principal
def main():
    try:
        threading.Thread(target=scheduler.start).start()
        logging.info("📅 Scheduler iniciado.")
        app.run()
    except Exception as e:
        logging.error(f"❌ Error al iniciar el bot: {e}")

if __name__ == "__main__":
    main()

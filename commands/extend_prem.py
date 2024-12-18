from pyrogram import Client, filters
import logging
import mysql.connector
from commands.prefixes import PREFIXES
from datetime import datetime, timedelta
from pyrogram.handlers import MessageHandler
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

ids_admins = [6706374638, 6364510923]

# Conexión a la base de datos MySQL
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

async def extend_premium(client, message):
    """Extiende la suscripción premium de un usuario."""
    if message.from_user.id not in ids_admins:
        await message.reply("Solo los admins pueden extender suscripciones premium.")
        logging.warning(f"Usuario no autorizado {message.from_user.id} intentó usar /extend_prem.")
        return

    if len(message.text.split()) < 3:
        await message.reply("Uso incorrecto. Ejemplo: /extend_prem <user_id> <días>")
        logging.warning(f"Comando /extend_prem mal usado por {message.from_user.id}.")
        return

    try:
        user_id = int(message.text.split()[1])
        days = int(message.text.split()[2])

        # Conexión a la base de datos
        conexion, cursor = connect_db()
        if not conexion or not cursor:
            await message.reply("Error al conectar con la base de datos.")
            return

        cursor.execute("SELECT end_date, premium FROM subscriptions WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()

        if result and result["premium"] == 1:  # Usuario tiene premium activo
            end_date = datetime.strptime(result["end_date"], "%Y-%m-%d %H:%M:%S")
            new_end_date = end_date + timedelta(days=days)
            cursor.execute(
                "UPDATE subscriptions SET end_date = %s WHERE user_id = %s",
                (new_end_date.strftime("%Y-%m-%d %H:%M:%S"), user_id)
            )
            conexion.commit()
            conexion.close()

            logging.info(f"Suscripción de {user_id} extendida por {days} días.")
            await message.reply(
                f"Suscripción de `{user_id}` extendida exitosamente. Nueva fecha de vencimiento: {new_end_date.strftime('%Y-%m-%d')}."
            )
        else:
            conexion.close()
            await message.reply(f"El usuario `{user_id}` no tiene una suscripción premium activa.")
            logging.info(f"Intento de extender premium a un usuario sin suscripción activa: {user_id}.")

    except Exception as e:
        logging.error(f"Error al extender premium para el usuario: {e}")
        await message.reply(f"Error al extender premium: {e}")

def register_command(app):
    app.add_handler(MessageHandler(extend_premium, filters.command("extend_prem", prefixes=PREFIXES)))
    return ["extend_prem"]

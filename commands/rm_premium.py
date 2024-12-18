from pyrogram import Client, filters
import logging
import mysql.connector
from commands.prefixes import PREFIXES
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

async def remove_premium(client, message):
    """Quita el rango premium de un usuario específico."""
    if message.from_user.id not in ids_admins:
        await message.reply("Solo los admins pueden quitar el rango premium.")
        logging.warning(f"Usuario no autorizado {message.from_user.id} intentó usar /remove_premium.")
        return

    if len(message.text.split()) < 2:
        await message.reply("Uso incorrecto. Ejemplo: /rm_premium <user_id>")
        logging.warning(f"Comando /remove_premium mal usado por {message.from_user.id}.")
        return

    try:
        user_id = int(message.text.split()[1])  # ID del usuario al que se le quita premium

        # Conexión a la base de datos
        conexion, cursor = connect_db()
        if not conexion or not cursor:
            await message.reply("Error al conectar con la base de datos.")
            return

        # Verificar si el usuario tiene premium
        cursor.execute("SELECT premium FROM subscriptions WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()

        if result and result["premium"] == 1:  # Si el usuario tiene premium
            # Quitar el rango premium
            cursor.execute("UPDATE subscriptions SET premium = 0 WHERE user_id = %s", (user_id,))
            conexion.commit()
            conexion.close()

            logging.info(f"Premium eliminado para el usuario {user_id}.")
            
            # Enviar mensaje al usuario
            try:
                await client.send_message(
                    user_id,
                    "Tu rango premium ha sido eliminado. 😔 Gracias por usar nuestro servicio."
                )
            except Exception as e:
                logging.error(f"No se pudo notificar al usuario {user_id} sobre la eliminación de premium: {e}")

            # Confirmación al administrador
            await message.reply(f"El rango premium del usuario `{user_id}` ha sido eliminado exitosamente.")

        else:  # Si el usuario no tiene premium
            conexion.close()
            await message.reply(f"El usuario `{user_id}` no tiene una suscripción premium activa.")
            logging.info(f"Intento de eliminar premium a un usuario sin suscripción activa: {user_id}.")

    except Exception as e:
        logging.error(f"Error al eliminar premium para el usuario: {e}")
        await message.reply(f"Error al eliminar premium: {e}")

def register_command(app):
    app.add_handler(MessageHandler(remove_premium, filters.command("rm_prem", prefixes=PREFIXES)))
    return ["rm_prem"]

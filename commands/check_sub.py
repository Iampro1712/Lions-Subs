from pyrogram import Client, filters
import logging
import mysql.connector
from datetime import datetime
from commands.prefixes import PREFIXES
from pyrogram.handlers import MessageHandler
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

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

async def check_subscription(client, message):
    """Verifica los días restantes de la suscripción premium o diamond."""
    try:
        # Determinar el user_id desde diferentes contextos
        if message.reply_to_message:  # Si el mensaje es una respuesta
            user_id = message.reply_to_message.from_user.id
        elif len(message.text.split()) > 1:  # Si se proporciona un ID como argumento
            user_id = int(message.text.split()[1])
        else:  # Por defecto, usa el ID del usuario que ejecutó el comando
            user_id = message.from_user.id

        conexion, cursor = connect_db()
        if not conexion or not cursor:
            await message.reply("Error al conectar con la base de datos.")
            return

        cursor.execute(
            "SELECT end_date, premium, diamond FROM subscriptions WHERE user_id = %s",
            (user_id,)
        )
        result = cursor.fetchone()

        if result:
            end_date = result["end_date"]
            premium = result["premium"]
            diamond = result["diamond"]
            now = datetime.now()
            rango_activo = None

            # Verificar si el usuario tiene rango activo
            if diamond == 1 and now <= datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S"):
                rango_activo = "Diamond"
            elif premium == 1 and now <= datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S"):
                rango_activo = "Premium"

            if rango_activo:
                remaining_time = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S") - now
                remaining_days = remaining_time.days
                remaining_hours = remaining_time.seconds // 3600

                # Determinar formato de tiempo restante
                if remaining_days > 0:
                    time_left = f"**{remaining_days} días**"
                elif remaining_hours > 0:
                    time_left = f"**{remaining_hours} horas**"
                else:
                    time_left = "**menos de una hora**"

                # Responder al usuario o al administrador
                if user_id == message.from_user.id:
                    await message.reply(
                        f"Hola, {message.from_user.first_name}. Te quedan {time_left} de suscripción **{rango_activo}**. 🎉"
                    )
                else:
                    await message.reply(
                        f"El usuario con ID `{user_id}` tiene {time_left} de suscripción **{rango_activo}**. 🎉"
                    )
                logging.info(f"El usuario {user_id} tiene {time_left} restantes de {rango_activo}.")
            else:
                if user_id == message.from_user.id:
                    await message.reply("No tienes una suscripción activa. 🚫")
                else:
                    await message.reply(f"El usuario con ID `{user_id}` no tiene una suscripción activa. 🚫")
                logging.info(f"El usuario {user_id} no tiene una suscripción activa.")
        else:
            if user_id == message.from_user.id:
                await message.reply("No tienes una suscripción registrada. 🚫")
            else:
                await message.reply(f"No se encontró registro para el usuario con ID `{user_id}`.")
            logging.info(f"No se encontró registro para el usuario {user_id} en la base de datos.")

        conexion.close()

    except Exception as e:
        logging.error(f"Error al verificar la suscripción de {user_id}: {e}")
        await message.reply(f"Error al verificar la suscripción: {e}")

def register_command(app):
    app.add_handler(MessageHandler(check_subscription, filters.command("check_sub", prefixes=PREFIXES)))
    return ["check_sub"]

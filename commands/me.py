import logging
import mysql.connector
from pyrogram import Client, filters
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

async def show_user_info(client, message):
    """Muestra información sobre el usuario que ejecuta el comando."""
    try:
        user_id = message.from_user.id
        user_name = message.from_user.first_name
        username = f"@{message.from_user.username}" if message.from_user.username else "Sin username"

        # Conectar a la base de datos
        conexion, cursor = connect_db()
        if not conexion or not cursor:
            await message.reply("Error al conectar con la base de datos.")
            return

        cursor.execute("SELECT end_date, premium FROM subscriptions WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        conexion.close()

        if result:
            end_date = result["end_date"]
            premium = result["premium"]
            rank = "Premium" if premium == 1 else "Normal"

            if premium == 1 and end_date:
                end_date = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S")
                now = datetime.now()

                if now <= end_date:
                    remaining_time = end_date - now
                    remaining_days = remaining_time.days
                    remaining_hours = remaining_time.seconds // 3600

                    if remaining_days > 0:
                        time_left = f"**{remaining_days} días**"
                    elif remaining_hours > 0:
                        time_left = f"**{remaining_hours} horas**"
                    else:
                        time_left = "**menos de una hora**"
                else:
                    time_left = "**Expirada**"
            else:
                time_left = "**N/A**"
        else:
            rank = "Normal"
            time_left = "**N/A**"

        # Enviar información al usuario
        await message.reply(
            f"🦁𝗜𝗡𝗙𝗢 𝗗𝗘 𝗦𝗨𝗦𝗖𝗥𝗜𝗣𝗖𝗜𝗢𝗡🦁\n"
            "━━━━━━━━━━━━━━━\n"
            f"⛈╏𝗡𝗔𝗠𝗘: {user_name}\n"
            f"⛈╏𝗨𝗦𝗘𝗥𝗡𝗔𝗠𝗘: {username}\n"
            f"⛈╏𝗜𝗗: `{user_id}`\n"
            f"⛈╏𝗥𝗔𝗡𝗚𝗢: {rank}\n"
            f"⛈╏𝗙𝗜𝗡 𝗗𝗘 𝗦𝗨𝗦𝗖𝗥𝗜𝗣𝗖𝗜𝗢𝗡: {time_left}"
            "\n━━━━━━━━━━━━━━━"
        )
        logging.info(f"Información mostrada para el usuario {user_id}.")
    except Exception as e:
        logging.error(f"Error al mostrar información del usuario {user_id}: {e}")
        await message.reply(f"Error al mostrar tu información: {e}")

def register_command(app):
    app.add_handler(MessageHandler(show_user_info, filters.command("me", prefixes=PREFIXES)))
    return ["me"]

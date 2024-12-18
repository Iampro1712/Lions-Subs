from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.handlers import MessageHandler
from datetime import datetime, timedelta
import mysql.connector
import logging
from commands.prefixes import PREFIXES
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

async def give_diamond(client: Client, message):
    """Otorga rango Diamond a un usuario por una cantidad específica de días."""
    if message.from_user.id not in ids_admins:
        await message.reply("Solo los admins pueden otorgar rango Diamond.")
        return

    if len(message.text.split()) < 3:
        await message.reply("Uso incorrecto. Ejemplo: /diamond <user_id> <duración_en_días>")
        return

    try:
        user_id = int(message.text.split()[1])
        duration = int(message.text.split()[2])

        start_date = datetime.now()
        end_date = start_date + timedelta(days=duration)

        conexion, cursor = connect_db()
        if not conexion or not cursor:
            await message.reply("Error al conectar con la base de datos.")
            return

        # Insertar o actualizar suscripción
        cursor.execute("""
        INSERT INTO subscriptions (user_id, start_date, end_date, diamond)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE start_date = %s, end_date = %s, diamond = 1
        """, (user_id, start_date, end_date, 1, start_date, end_date))
        conexion.commit()
        conexion.close()

        # Mensaje de bienvenida al usuario
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💎 Lions VIP Curso", url="https://t.me/+TZo3GzQ-VBszM2Qx"), InlineKeyboardButton("🐍 LIONS Premium Scrap", url="https://t.me/+Y2BaNz9UNHQwNWE5")],
            [InlineKeyboardButton("👑 LIONS Users VIP Group", url="https://t.me/+QdygY-TnbMU4MDZh")]
        ])

        await client.send_message(
            user_id,
            (
                f"⍟⚘ 𝑮𝒓𝒂𝒄𝒊𝒂𝒔 𝑷𝒐𝒓 𝑼𝒏𝒊𝒓𝒕𝒆 𝑨 𝑵𝒖𝒆𝒔𝒕𝒓𝒂 𝑬𝒙𝒄𝒍𝒖𝒔𝒊𝒗𝒂 𝑺𝒖𝒔𝒄𝒓𝒊𝒑𝒄𝒊𝒐𝒏 𝑫𝒊𝒂𝒎𝒐𝒏𝒅 ⚘⍟\n\n"
                f"👤 **Usuario ID:** `{user_id}`\n"
                f"💎 **Plan Activo:** Diamond User\n"
                f"⏳ **Duración:** {duration} días\n\n"
                f"¡Disfruta de los beneficios exclusivos!"
            ),
            reply_markup=keyboard
        )

        await message.reply(f"Diamond activado exitosamente para el usuario `{user_id}` por {duration} días.")
        logging.info(f"Diamond activado para el usuario {user_id} por {duration} días por el admin {message.from_user.id}.")
    except Exception as e:
        await message.reply(f"Error: {e}")
        logging.error(f"Error al activar Diamond para el usuario {user_id}: {e}")

async def remove_diamond(client: Client, message):
    """Elimina el rango Diamond de un usuario."""
    if message.from_user.id not in ids_admins:
        await message.reply("Solo los admins pueden quitar el rango Diamond.")
        return

    if len(message.text.split()) < 2:
        await message.reply("Uso incorrecto. Ejemplo: /rm_diamond <user_id>")
        return

    try:
        user_id = int(message.text.split()[1])

        conexion, cursor = connect_db()
        if not conexion or not cursor:
            await message.reply("Error al conectar con la base de datos.")
            return

        cursor.execute("UPDATE subscriptions SET diamond = 0 WHERE user_id = %s", (user_id,))
        conexion.commit()
        conexion.close()

        await message.reply(f"Diamond eliminado exitosamente para el usuario `{user_id}`.")
        logging.info(f"Diamond eliminado para el usuario {user_id} por el admin {message.from_user.id}.")
    except Exception as e:
        await message.reply(f"Error: {e}")
        logging.error(f"Error al eliminar Diamond para el usuario {user_id}: {e}")

def register_command(app: Client):
    """Registra los comandos para gestionar el rango Diamond."""
    app.add_handler(MessageHandler(give_diamond, filters.command("diamond", prefixes=PREFIXES)))
    app.add_handler(MessageHandler(remove_diamond, filters.command("rm_diamond", prefixes=PREFIXES)))
    return ["diamond", "rm_diamond"]

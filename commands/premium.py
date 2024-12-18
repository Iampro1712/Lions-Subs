import logging
import mysql.connector
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime, timedelta
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

async def give_premium(client, message):
    if message.from_user.id not in ids_admins:
        await message.reply("Solo los admins pueden dar premium.")
        logging.warning(f"Usuario no autorizado {message.from_user.id} intentó usar /premium.")
        return

    if len(message.text.split()) < 3:
        await message.reply("Uso incorrecto. Ejemplo: /premium <user_id> <duración_en_días>")
        logging.warning(f"Comando /premium mal usado por {message.from_user.id}.")
        return

    try:
        user_id = int(message.text.split()[1])  # ID del usuario al que se le da premium
        duration = int(message.text.split()[2])  # Duración en días

        # Calcular fechas de inicio y fin
        start_date = datetime.now()
        end_date = start_date + timedelta(days=duration)

        # Conexión a la base de datos
        conexion, cursor = connect_db()
        if not conexion or not cursor:
            await message.reply("Error al conectar con la base de datos.")
            return

        # Guardar en la base de datos
        cursor.execute("""
        INSERT INTO subscriptions (user_id, start_date, end_date, premium)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE start_date = %s, end_date = %s, premium = 1
        """, (user_id, start_date, end_date, 1, start_date, end_date))
        conexion.commit()
        conexion.close()

        logging.info(f"Premium activado para {user_id} por {duration} días.")
        # Enviar mensaje al usuario
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("LIONS Users VIP Group", url="https://t.me/+QdygY-TnbMU4MDZh"), InlineKeyboardButton("LIONS Premium Scrap", url="https://t.me/+Y2BaNz9UNHQwNWE5")]
        ])
    
        await client.send_message(
            user_id,
            f"✪❂𝑯𝒐𝒍𝒂, 𝑮𝒓𝒂𝒄𝒊𝒂𝒔 𝑷𝒐𝒓 𝑨𝒅𝒒𝒖𝒊𝒓𝒊𝒓 𝒖𝒏𝒂 𝑺𝒖𝒔𝒄𝒓𝒊𝒑𝒄𝒊𝒐𝒏 𝑫𝒆 𝑳𝑰𝑶𝑵𝑺 𝑺𝑪𝑹𝑨𝑷𝑷𝑬𝑹 𝑽𝑰𝑷!✪❂\n"
            "\n"
            f"◓⇢⇢⇢⇢⇢⇢⇢⇢⇢⇢⇢\n"
            "\n"
            f"「<a href='tg://user?id=6364510923'>𓃭</a>」𝑼𝒔𝒆𝒓 𝑰𝑫  ➩ <code>{user_id}</code>\n"
            "\n"
            f"「<a href='tg://user?id=6364510923'>𓃭</a>」𝑺𝒕𝒂𝒕𝒖𝒔   ➩ Plan Active <strong>[Premium User]</strong>\n"
            "\n"
            f"「<a href='tg://user?id=6364510923'>𓃭</a>」𝑫𝒖𝒓𝒂𝒕𝒊𝒐𝒏  ➩ <strong>{duration}</strong>d\n"
            "\n"
            f"◓⇢⇢⇢⇢⇢⇢⇢⇢⇢⇢⇢"
            "\n"
            f"\n✪❂⇱ 𝑨𝒃𝒂𝒋𝒐 𝑻𝒆 𝑫𝒆𝒋𝒂𝒓𝒆𝒎𝒐𝒔 𝑳𝒐𝒔 𝑳𝒊𝒏𝒌𝒔 𝑫𝒆𝒍 𝑮𝒓𝒖𝒑𝒐 𝒀 𝑫𝒆𝒍 𝑺𝒄𝒓𝒂𝒑𝒑𝒆𝒓, 𝑫𝒊𝒔𝒇𝒖𝒕𝒂 𝑻𝒖 𝑬𝒔𝒕𝒂𝒅𝒊𝒂 𝒀 𝑺𝒖𝒆𝒓𝒕𝒆 ☘️ 𝑪𝒐𝒏 𝑳𝒂𝒔 𝑪𝑪 ⇲✪❂",
            reply_markup=keyboard
        )

        await message.reply("Premium activado exitosamente.")
    except Exception as e:
        logging.error(f"Error al activar premium para {user_id}: {e}")
        await message.reply(f"Error: {e}")

def register_command(app):
    """Registra el comando premium en el cliente."""
    app.add_handler(MessageHandler(give_premium, filters.command("premium", prefixes=PREFIXES)))
    return ["premium"]

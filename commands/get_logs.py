from pyrogram import Client, filters
import logging
from commands.prefixes import PREFIXES
from pyrogram.handlers import MessageHandler

ids_admins = [6706374638, 6364510923]

async def send_logs(client, message):
    """Envía el archivo de logs a los administradores."""
    try:
        log_file = "bot_logs.log"  # Nombre del archivo de logs

        # Verificar si el archivo existe
        try:
            with open(log_file, "rb") as file:
                await client.send_document(
                    chat_id=message.chat.id,
                    document=file,
                    caption="Aquí tienes el archivo de logs 📄"
                )
                logging.info(f"Archivo {log_file} enviado a {message.from_user.id}.")
        except FileNotFoundError:
            await message.reply("El archivo de logs no existe actualmente. 📂")
            logging.warning(f"{message.from_user.id} intentó acceder a un archivo inexistente.")
    except Exception as e:
        logging.error(f"Error al enviar el archivo de logs: {e}")
        await message.reply(f"Error al enviar los logs: {e}")

def register_command(app):
    app.add_handler(MessageHandler(send_logs, filters.command("get_logs", prefixes=PREFIXES) & filters.user(ids_admins)))
    return ["get_logs"]
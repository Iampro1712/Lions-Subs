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

async def stats(client, message):
    """Muestra estadísticas del sistema y detalles de usuarios premium activos."""
    try:
        conexion, cursor = connect_db()
        if not conexion or not cursor:
            await message.reply("Error al conectar con la base de datos.")
            return

        # Obtener estadísticas generales
        cursor.execute("SELECT COUNT(*) AS total_users FROM subscriptions")
        total_users = cursor.fetchone()["total_users"]

        cursor.execute("SELECT COUNT(*) AS active_premium_count FROM subscriptions WHERE premium = 1")
        active_premium_count = cursor.fetchone()["active_premium_count"]

        cursor.execute("SELECT COUNT(*) AS expired_premium FROM subscriptions WHERE premium = 0")
        expired_premium = cursor.fetchone()["expired_premium"]

        # Obtener detalles de usuarios premium activos
        cursor.execute("""
            SELECT user_id, start_date, end_date FROM subscriptions WHERE premium = 1
        """)
        active_premium_users = cursor.fetchall()

        conexion.close()

        # Construir el mensaje de estadísticas generales
        stats_message = (
            f"📊 **Estadísticas del sistema:**\n"
            f"👥 Total de usuarios registrados: {total_users}\n"
            f"💎 Usuarios premium activos: {active_premium_count}\n"
            f"⏳ Suscripciones expiradas: {expired_premium}\n"
        )

        # Agregar detalles de usuarios premium activos
        if active_premium_users:
            stats_message += "\n**💎 Detalles de usuarios premium activos:**\n"
            for user in active_premium_users:
                user_id, start_date, end_date = user["user_id"], user["start_date"], user["end_date"]
                try:
                    # Obtener username del usuario
                    user_info = await client.get_users(user_id)
                    username = f"@{user_info.username}" if user_info.username else "Sin username"
                except Exception as e:
                    username = "Desconocido"
                    logging.error(f"No se pudo obtener el username para el ID {user_id}: {e}")

                stats_message += (
                    f"• **ID:** `{user_id}`\n"
                    f"  **Username:** {username}\n"
                    f"  **Inicio:** {start_date}\n"
                    f"  **Vencimiento:** {end_date}\n\n"
                )
        else:
            stats_message += "\nNo hay usuarios premium activos actualmente. 🚫"

        # Enviar el mensaje de estadísticas
        await message.reply(stats_message)
        logging.info(f"Estadísticas enviadas a {message.from_user.id}.")

    except Exception as e:
        logging.error(f"Error al generar estadísticas: {e}")
        await message.reply(f"Error al generar estadísticas: {e}")

def register_command(app):
    app.add_handler(MessageHandler(stats, filters.command("stats", prefixes=PREFIXES)))
    return ["stats"]

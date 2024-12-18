from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import logging
import mysql.connector
from commands.prefixes import PREFIXES
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

# Configuración global
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

async def expired_subscriptions(client, message):
    """Muestra un inline keyboard con usuarios que tienen suscripciones expiradas."""
    try:
        conexion, cursor = connect_db()
        if not conexion or not cursor:
            await message.reply("Error al conectar con la base de datos.")
            return

        # Obtener usuarios con suscripciones expiradas
        cursor.execute("""
            SELECT user_id, start_date, end_date FROM subscriptions WHERE premium = 0
        """)
        expired_users = cursor.fetchall()
        conexion.close()

        if not expired_users:
            await message.reply("No hay usuarios con suscripciones expiradas. 🚫")
            logging.info("No se encontraron usuarios con suscripciones expiradas.")
            return

        # Crear el teclado inline
        buttons = []
        for user in expired_users:
            user_id, start_date, end_date = user.values()
            buttons.append(
                [InlineKeyboardButton(f"Usuario ID: {user_id}", callback_data=f"expired_{user_id}")]
            )

        keyboard = InlineKeyboardMarkup(buttons)
        await message.reply("📋 Usuarios con suscripciones expiradas:", reply_markup=keyboard)
        logging.info(f"Usuarios con suscripciones expiradas enviados a {message.from_user.id}.")
    
    except Exception as e:
        logging.error(f"Error al generar la lista de suscripciones expiradas: {e}")
        await message.reply(f"Error al generar la lista: {e}")

@Client.on_callback_query(filters.regex(r"expired_\d+"))
async def show_expired_user_details(client, callback_query):
    """Muestra detalles de un usuario con suscripción expirada."""
    try:
        user_id = int(callback_query.data.split("_")[1])
        conexion, cursor = connect_db()
        if not conexion or not cursor:
            await callback_query.message.edit_text("Error al conectar con la base de datos.")
            return

        # Obtener detalles del usuario
        cursor.execute("""
            SELECT start_date, end_date FROM subscriptions WHERE user_id = %s AND premium = 0
        """, (user_id,))
        result = cursor.fetchone()
        conexion.close()

        if result:
            start_date, end_date = result["start_date"], result["end_date"]

            # Obtener username
            try:
                user_info = await client.get_users(user_id)
                username = f"@{user_info.username}" if user_info.username else "Sin username"
            except Exception as e:
                username = "Desconocido"
                logging.error(f"No se pudo obtener el username para el ID {user_id}: {e}")

            # Crear botón de regreso
            back_button = InlineKeyboardMarkup(
                [[InlineKeyboardButton("↩️ Regresar", callback_data="back_to_expired_list")]]
            )

            await callback_query.message.edit_text(
                f"**Detalles del usuario con suscripción expirada:**\n"
                f"👤 **ID:** `{user_id}`\n"
                f"📝 **Username:** {username}\n"
                f"📅 **Inicio de la suscripción:** {start_date}\n"
                f"📅 **Fecha de vencimiento:** {end_date}\n",
                reply_markup=back_button
            )
            logging.info(f"Detalles de suscripción expirada mostrados para el usuario {user_id}.")
        else:
            await callback_query.message.edit_text(
                f"No se encontraron detalles para el usuario `{user_id}`."
            )
            logging.warning(f"Intento de ver detalles de usuario inexistente: {user_id}.")
    
    except Exception as e:
        logging.error(f"Error al mostrar detalles de usuario con suscripción expirada: {e}")
        await callback_query.message.edit_text(f"Error al mostrar detalles: {e}")

@Client.on_callback_query(filters.regex("back_to_expired_list"))
async def return_to_expired_list(client, callback_query):
    """Regresa a la lista de usuarios con suscripciones expiradas."""
    try:
        conexion, cursor = connect_db()
        if not conexion or not cursor:
            await callback_query.message.edit_text("Error al conectar con la base de datos.")
            return

        # Obtener usuarios con suscripciones expiradas
        cursor.execute("""
            SELECT user_id FROM subscriptions WHERE premium = 0
        """)
        expired_users = cursor.fetchall()
        conexion.close()

        if not expired_users:
            await callback_query.message.edit_text("No hay usuarios con suscripciones expiradas. 🚫")
            logging.info("No se encontraron usuarios con suscripciones expiradas.")
            return

        # Crear el teclado inline nuevamente
        buttons = []
        for user in expired_users:
            user_id = user["user_id"]
            buttons.append(
                [InlineKeyboardButton(f"Usuario ID: {user_id}", callback_data=f"expired_{user_id}")]
            )

        keyboard = InlineKeyboardMarkup(buttons)
        await callback_query.message.edit_text("📋 Usuarios con suscripciones expiradas:", reply_markup=keyboard)
        logging.info("Regreso a la lista de usuarios con suscripciones expiradas.")
    
    except Exception as e:
        logging.error(f"Error al regresar a la lista de suscripciones expiradas: {e}")
        await callback_query.message.edit_text(f"Error al regresar a la lista: {e}")

def register_command(app):
    app.add_handler(MessageHandler(expired_subscriptions, filters.command("exp_subs", prefixes=PREFIXES) & filters.user(ids_admins)))

    # Handler para mostrar detalles de usuarios con suscripciones expiradas
    app.add_handler(CallbackQueryHandler(show_expired_user_details, filters.regex(r"expired_\d+")))

    # Handler para regresar a la lista de usuarios expirados
    app.add_handler(CallbackQueryHandler(return_to_expired_list, filters.regex("back_to_expired_list")))
    return ["exp_subs"]

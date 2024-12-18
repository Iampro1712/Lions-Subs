from pyrogram import Client, filters
from commands.prefixes import PREFIXES
from pyrogram.handlers import MessageHandler

async def start(client, message):
    link = "https://t.me/ProjectLions/5"
    await message.reply(f"𝑩𝑶𝑻 𝑶𝑭𝑰𝑪𝑰𝑨𝑳 𝑫𝑬 𝑪𝑶𝑵𝑻𝑹𝑶𝑳 𝑫𝑬 𝑺𝑼𝑺𝑪𝑹𝑰𝑷𝑪𝑰𝑶𝑵𝑬𝑺 𝑫𝑬 𝑳𝑰𝑶𝑵𝑺 𝑺𝑪𝑹𝑨𝑷𝑷𝑬𝑹 𝑽𝑰𝑷, 𝑺𝑰 𝑻𝑬 𝑰𝑵𝑻𝑬𝑹𝑬𝑺𝑨 𝑻𝑬𝑵𝑬𝑹 𝑴𝑨𝑺 𝑰𝑵𝑭𝑶𝑹𝑴𝑨𝑪𝑰𝑶𝑵 𝑨𝑸𝑼𝑰: <a href='{link}'> 𝑷𝑹𝑶𝑱𝑬𝑪𝑻 𝑳𝑰𝑶𝑵𝑺 </a>")

def register_command(app):
    app.add_handler(MessageHandler(start, filters.command("start", prefixes=PREFIXES)))
    return ["start"]
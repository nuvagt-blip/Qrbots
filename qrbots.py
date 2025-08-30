import logging
import re
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests

# Configura el logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ⚠️ Token directo en el código (porque el repo es privado)
TOKEN = "AQUI_VA_TU_TOKEN"  
ADMIN_ID = 8113919663  # tu ID de admin fijo

# Lista de usuarios y grupos autorizados
AUTHORIZED_USERS = {ADMIN_ID}
AUTHORIZED_GROUPS = set()

# Estado del bot
BOT_STATUS = "active"

WELCOME_MESSAGE = (
    "👑 ¡Bienvenid@ al Bot Profesional de Lectura de Códigos QR creado por @Sangre_binerojs! 👑\n"
    "✨ Estado del sistema: {status_message}\n"
    "📌 Tu ID de Telegram: {user_id}\n"
    "📛 Tu nombre de usuario: {username}\n"
    "⚙️ Usa el comando /qrgen para enviar una imagen de código QR y extraer su contenido.\n"
    "⚠️ Nota: La lectura de códigos QR está disponible solo para usuarios o grupos autorizados por el administrador."
)

def extract_name(qr_content: str):
    match = re.search(r'59(\d{2})([A-Z\s]+)', qr_content)
    if match:
        name_length = int(match.group(1))
        name = match.group(2)[:name_length]
        return name.strip()
    return None

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = f"@{user.username}" if user.username else user.first_name
    status_message = "Sistemas operacionales están activos. ✅" if BOT_STATUS == "active" else "Sistemas operacionales están apagados. 🚫"
    await update.message.reply_text(
        WELCOME_MESSAGE.format(status_message=status_message, user_id=user_id, username=username)
    )

# /qrgen
async def qrgen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    if BOT_STATUS != "active":
        await update.message.reply_text("⛔ El bot está apagado. Contacta al administrador. 🔧")
        return
    if user_id not in AUTHORIZED_USERS and chat_id not in AUTHORIZED_GROUPS:
        await update.message.reply_text("⛔ Acceso denegado. Contacta a @Sangre_binerojs 📩")
        return
    await update.message.reply_text("✅ Envía la imagen del código QR para extraer el contenido. 📸")

# /authorize
async def authorize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Solo el administrador puede usar este comando. 🔒")
        return
    if not context.args:
        await update.message.reply_text("📋 Uso: /authorize <user_id> o /authorize group")
        return
    try:
        if context.args[0].lower() == "group":
            group_id = update.effective_chat.id
            AUTHORIZED_GROUPS.add(group_id)
            await update.message.reply_text(f"✅ Grupo {group_id} autorizado 🎉")
        else:
            user_id = int(context.args[0])
            AUTHORIZED_USERS.add(user_id)
            await update.message.reply_text(f"✅ Usuario {user_id} autorizado 🎉")
    except ValueError:
        await update.message.reply_text("❌ ID inválido. Usa un número o 'group'. 🔍")

# /agregargrupo
async def agregargrupo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Solo el administrador puede usar este comando. 🔒")
        return
    group_id = update.effective_chat.id
    AUTHORIZED_GROUPS.add(group_id)
    await update.message.reply_text(f"✅ Grupo {group_id} autorizado 🎉")

# /deauthorize
async def deauthorize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Solo el administrador puede usar este comando. 🔒")
        return
    if not context.args:
        await update.message.reply_text("📋 Uso: /deauthorize <user_id> o /deauthorize group")
        return
    try:
        if context.args[0].lower() == "group":
            group_id = update.effective_chat.id
            AUTHORIZED_GROUPS.discard(group_id)
            await update.message.reply_text(f"✅ Grupo {group_id} desautorizado 🚫")
        else:
            user_id = int(context.args[0])
            AUTHORIZED_USERS.discard(user_id)
            await update.message.reply_text(f"✅ Usuario {user_id} desautorizado 🚫")
    except ValueError:
        await update.message.reply_text("❌ ID inválido. Usa un número o 'group'. 🔍")

# /verusuarios
async def verusuarios(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Solo el administrador puede usar este comando. 🔒")
        return
    if not AUTHORIZED_USERS:
        await update.message.reply_text("📋 No hay usuarios autorizados.")
        return
    users_list = "\n".join([f"ID: {user_id}" for user_id in AUTHORIZED_USERS])
    await update.message.reply_text(f"📋 Usuarios autorizados:\n{users_list}")

# /vergrupos
async def vergrupos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Solo el administrador puede usar este comando. 🔒")
        return
    if not AUTHORIZED_GROUPS:
        await update.message.reply_text("📋 No hay grupos autorizados.")
        return
    groups_list = "\n".join([f"ID: {group_id}" for group_id in AUTHORIZED_GROUPS])
    await update.message.reply_text(f"📋 Grupos autorizados:\n{groups_list}")

# /on
async def turn_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BOT_STATUS
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Solo el administrador puede usar este comando. 🔒")
        return
    BOT_STATUS = "active"
    await update.message.reply_text("✅ Bot encendido 🚀")

# /off
async def turn_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BOT_STATUS
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Solo el administrador puede usar este comando. 🔒")
        return
    BOT_STATUS = "inactive"
    await update.message.reply_text("🛑 Bot apagado.")

# Manejar fotos
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    if BOT_STATUS != "active":
        await update.message.reply_text("⛔ El bot está apagado. 🔧")
        return
    if user_id not in AUTHORIZED_USERS and chat_id not in AUTHORIZED_GROUPS:
        await update.message.reply_text("⛔ Acceso denegado. Contacta a @Sangre_binerojs 📩")
        return
    await update.message.reply_text("📸 Escaneando imagen... ⏳")
    try:
        photo = update.message.photo[-1]
        file = await photo.get_file()
        response = requests.get(file.file_path, timeout=10)
        response.raise_for_status()
        api_url = "https://api.qrserver.com/v1/read-qr-code/"
        files = {"file": ("image.jpg", response.content)}
        api_response = requests.post(api_url, files=files, timeout=10)
        api_response.raise_for_status()
        qr_data = api_response.json()
        if qr_data and qr_data[0].get("symbol") and qr_data[0]["symbol"][0].get("data"):
            qr_content = qr_data[0]["symbol"][0]["data"]
            name = extract_name(qr_content)
            if name:
                await update.message.reply_text(f"✅ Nombre extraído del código QR: *{name}* 🎉", parse_mode="Markdown")
            else:
                await update.message.reply_text("❌ No se pudo extraer un nombre válido del QR. 🔍")
        else:
            await update.message.reply_text("❌ No se detectó un código QR válido. 📷")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error de red: {e}")
        await update.message.reply_text("❌ Error de red. Intenta de nuevo. 🌐")
    except Exception as e:
        logger.error(f"Error procesando la imagen: {e}")
        await update.message.reply_text("❌ Error al procesar la imagen. 📷")

# Manejo de errores global
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Error: {context.error}")
    if update and update.message:
        await update.message.reply_text("❌ Ocurrió un error inesperado. Contacta a @Sangre_binerojs 🛠️")

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("qrgen", qrgen))
    application.add_handler(CommandHandler("authorize", authorize))
    application.add_handler(CommandHandler("agregargrupo", agregargrupo))
    application.add_handler(CommandHandler("deauthorize", deauthorize))
    application.add_handler(CommandHandler("verusuarios", verusuarios))
    application.add_handler(CommandHandler("vergrupos", vergrupos))
    application.add_handler(CommandHandler("on", turn_on))
    application.add_handler(CommandHandler("off", turn_off))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_error_handler(error_handler)
    application.run_polling()

if __name__ == "__main__":
    main()

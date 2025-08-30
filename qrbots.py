import logging
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests
# Configura el logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log"), # Guarda logs en un archivo
        logging.StreamHandler() # Muestra logs en consola
    ]
)
logger = logging.getLogger(__name__)
# Token del bot
TOKEN = "8146061705:AAEYuDB4QxIdZ9Vvhg5XGg4tSMd8qpzEnlE"
# ID del administrador
ADMIN_ID = 8113919663
# Lista de usuarios y grupos autorizados
AUTHORIZED_USERS = {8113919663} # Incluye al admin por defecto
AUTHORIZED_GROUPS = set() # Grupos autorizados
# Estado del bot
BOT_STATUS = "active"  # Puede ser "active" o "inactive"
# Mensaje de bienvenida (accesible para todos)
WELCOME_MESSAGE = (
    "👑 ¡Bienvenid@ al Bot Profesional de Lectura de Códigos QR creado por @Sangre_binerojs! 👑\n"
    "✨ Estado del sistema: {status_message}\n"
    "📌 Tu ID de Telegram: {user_id}\n"
    "📛 Tu nombre de usuario: {username}\n"
    "⚙️ Usa el comando /qrgen para enviar una imagen de código QR y extraer su contenido.\n"
    "⚠️ Nota: La lectura de códigos QR está disponible solo para usuarios o grupos autorizados por el administrador."
)
# Función para extraer el nombre del contenido del QR
def extract_name(qr_content):
    # Busca el campo 59 (nombre en el estándar QR de Nequi)
    match = re.search(r'59(\d{2})([A-Z\s]+)', qr_content)
    if match:
        name_length = int(match.group(1)) # Longitud del nombre
        name = match.group(2)[:name_length] # Extrae el nombre
        return name.strip()
    return None
# Comando /start (accesible para todos)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = f"@{user.username}" if user.username else user.first_name
    # Determina el mensaje de estado del bot
    status_message = "Sistemas operacionales están activos. ✅" if BOT_STATUS == "active" else "Sistemas operacionales están apagados. 🚫"
    # Envía mensaje de bienvenida
    await update.message.reply_text(
        WELCOME_MESSAGE.format(status_message=status_message, user_id=user_id, username=username)
    )
# Comando /qrgen (verifica autorización y pide la imagen)
async def qrgen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    # Verifica si el usuario o grupo está autorizado
    if user_id not in AUTHORIZED_USERS and chat_id not in AUTHORIZED_GROUPS:
        await update.message.reply_text(
            "⛔ Acceso denegado. Solo usuarios o grupos autorizados pueden usar esta función. Contacta a @Sangre_binerojs para obtener acceso. 📩"
        )
        return
    # Pide la imagen
    await update.message.reply_text(
        "✅ Por favor, envía la imagen del código QR (por ejemplo, de Nequi o Bancolombia) para extraer el nombre asociado. 📸"
    )
# Comando /authorize (solo para el admin)
async def authorize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Solo el administrador (@Sangre_binerojs) puede usar este comando. 🔒")
        return
    if not context.args:
        await update.message.reply_text("📋 Uso: /authorize <user_id> o /authorize group")
        return
    try:
        if context.args[0].lower() == "group":
            group_id = update.effective_chat.id
            AUTHORIZED_GROUPS.add(group_id)
            await update.message.reply_text(f"✅ ¡Grupo {group_id} autorizado con éxito! 🎉")
        else:
            user_id = int(context.args[0])
            AUTHORIZED_USERS.add(user_id)
            await update.message.reply_text(f"✅ ¡Usuario {user_id} autorizado con éxito! 🎉")
    except ValueError:
        await update.message.reply_text("❌ Error: ID inválido. Usa un número para usuarios o 'group' para grupos. 🔍")
# Comando /deauthorize (solo para el admin)
async def deauthorize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Solo el administrador (@Sangre_binerojs) puede usar este comando. 🔒")
        return
    if not context.args:
        await update.message.reply_text("📋 Uso: /deauthorize <user_id> o /deauthorize group")
        return
    try:
        if context.args[0].lower() == "group":
            group_id = update.effective_chat.id
            AUTHORIZED_GROUPS.discard(group_id)
            await update.message.reply_text(f"✅ ¡Grupo {group_id} desautorizado con éxito! 🚫")
        else:
            user_id = int(context.args[0])
            AUTHORIZED_USERS.discard(user_id)
            await update.message.reply_text(f"✅ ¡Usuario {user_id} desautorizado con éxito! 🚫")
    except ValueError:
        await update.message.reply_text("❌ Error: ID inválido. Usa un número para usuarios o 'group' para grupos. 🔍")
# Manejar imágenes con códigos QR usando API externa
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    # Verifica si el usuario o grupo está autorizado
    if user_id not in AUTHORIZED_USERS and chat_id not in AUTHORIZED_GROUPS:
        await update.message.reply_text(
            "⛔ Acceso denegado. Solo usuarios o grupos autorizados pueden usar esta función. Contacta a @Sangre_binerojs para obtener acceso. 📩"
        )
        return
    # Informa que está escaneando
    await update.message.reply_text("📸 Escaneando imagen... Por favor, espera un momento. ⏳")
    try:
        # Obtiene la foto de mayor resolución
        photo = update.message.photo[-1]
        file = await photo.get_file()
        # Descarga la imagen
        response = requests.get(file.file_path, timeout=10)
        response.raise_for_status()
        # Envía la imagen a la API de qrserver.com
        api_url = "https://api.qrserver.com/v1/read-qr-code/"
        files = {"file": ("image.jpg", response.content)}
        api_response = requests.post(api_url, files=files, timeout=10)
        api_response.raise_for_status()
        # Procesa la respuesta de la API
        qr_data = api_response.json()
        if qr_data and qr_data[0]["symbol"] and qr_data[0]["symbol"][0]["data"]:
            qr_content = qr_data[0]["symbol"][0]["data"]
            # Extrae el nombre
            name = extract_name(qr_content)
            if name:
                await update.message.reply_text(f"✅ Nombre extraído del código QR: **{name}** 🎉")
            else:
                await update.message.reply_text("❌ No se pudo extraer un nombre del código QR. Asegúrate de que el QR contenga un nombre válido. 🔍")
        else:
            await update.message.reply_text("❌ No se detectó ningún código QR en la imagen. Por favor, verifica e intenta de nuevo. 📷")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error de red al procesar la imagen: {e}")
        await update.message.reply_text("❌ Error de red. Por favor, verifica tu conexión a internet e intenta de nuevo. 🌐")
    except Exception as e:
        logger.error(f"Error al procesar la imagen: {e}")
        await update.message.reply_text("❌ Error al procesar la imagen. Asegúrate de enviar una imagen válida con un código QR. 📷")
# Manejar errores generales
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Error: {context.error}")
    if update and update.message:
        await update.message.reply_text("❌ Ocurrió un error inesperado. Por favor, intenta de nuevo o contacta a @Sangre_binerojs. 🛠️")
def main():
    # Crea la aplicación del bot
    application = Application.builder().token(TOKEN).build()
    # Agrega manejadores
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("qrgen", qrgen))
    application.add_handler(CommandHandler("authorize", authorize))
    application.add_handler(CommandHandler("deauthorize", deauthorize))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_error_handler(error_handler)
    # Inicia el bot
    application.run_polling()
if __name__ == "__main__":
    main()

import os
import io
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# Inicializar Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'credentials.json'
creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=creds)

# ID de la carpeta base en tu Drive (la carpeta "Fotos")
ROOT_FOLDER_ID = os.getenv("ROOT_FOLDER_ID")

# Función para subir a Google Drive en memoria
def subir_a_drive(nombre_archivo, data_bytes, folder_id):
    media = MediaIoBaseUpload(io.BytesIO(data_bytes), mimetype='image/jpeg', resumable=True)
    file_metadata = {'name': nombre_archivo, 'parents': [folder_id]}
    drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()

# Obtener o crear carpeta por nombre
def obtener_o_crear_carpeta(nombre, padre_id):
    query = f"'{padre_id}' in parents and name = '{nombre}' and mimeType = 'application/vnd.google-apps.folder'"
    resultado = drive_service.files().list(q=query, fields="files(id)").execute()
    archivos = resultado.get('files', [])
    if archivos:
        return archivos[0]['id']
    else:
        nueva = {'name': nombre, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [padre_id]}
        archivo = drive_service.files().create(body=nueva, fields='id').execute()
        return archivo.get('id')

# Manejador de fotos
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.photo[-1].get_file()
    data = await file.download_as_bytearray()
    
    fecha = datetime.now()
    año = str(fecha.year)
    mes = fecha.strftime("%m_%B")
    tema = "General"  # Puedes personalizar esto con input
    lugar = "Viña del Mar"  # Igual acá

    # Crear estructura de carpetas
    año_id = obtener_o_crear_carpeta(año, ROOT_FOLDER_ID)
    mes_id = obtener_o_crear_carpeta(mes, año_id)
    carpeta_final_id = obtener_o_crear_carpeta(f"{lugar} - {tema}", mes_id)

    nombre_archivo = f"{fecha.strftime('%Y%m%d_%H%M%S')}.jpg"
    subir_a_drive(nombre_archivo, data, carpeta_final_id)

    await update.message.reply_text("📸 Imagen guardada exitosamente.")

# Inicializar bot
app = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

if __name__ == '__main__':
    app.run_polling()

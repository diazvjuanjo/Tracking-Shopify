from ftplib import FTP

# Cambia estos valores por los de tu servidor
ftp_host = '154.53.132.27'  # Dirección IP del servidor FTP
ftp_user = 'gls'    # Usuario del servidor FTP
ftp_password = '7n!6b4jD6'  # Contraseña del usuario

# Conexión al servidor FTP
ftp = FTP(ftp_host)
ftp.login(user=ftp_user, passwd=ftp_password)
print("Conectado al servidor FTP.")

# Descarga del archivo
remote_file = 'GLS.Xlsx'
local_file = 'GLS.Xlsx'

with open(local_file, 'wb') as file:
    ftp.retrbinary(f'RETR {remote_file}', file.write)
print(f"Archivo {remote_file} descargado correctamente.")

ftp.quit()
import pandas as pd

# Cargar el archivo descargado
archivo = 'GLS.xlsx'  # Asegúrate de que este es el nombre correcto
data = pd.read_excel(archivo, engine='openpyxl')  # Leemos el archivo Excel

# Mostrar las primeras filas del archivo para verificar
print("Contenido inicial del archivo:")
print(data.head())

# Verificar que las columnas necesarias existen
columnas_necesarias = ['REFERENCIA', 'URLTRACKING']
for columna in columnas_necesarias:
    if columna not in data.columns:
        raise ValueError(f"Falta la columna requerida: {columna}")

# Añadir la columna del transportista
data['TRANSPORTISTA'] = 'GLS'  # Añadimos la columna con "GLS" como valor predeterminado

# Mostrar las primeras filas después de añadir el transportista
print("\nContenido del archivo después de añadir el transportista:")
print(data.head())

# Guardar el archivo procesado (opcional)
archivo_procesado = 'archivo_seguimiento_procesado.xlsx'
data.to_excel(archivo_procesado, index=False, engine='openpyxl')  # Guardamos como Excel
print(f"\nArchivo procesado guardado como: {archivo_procesado}")

import requests

# Configuración de la API de Shopify
API_KEY = '97b66a4c4b48aca5d652a108f30bf0c8'             # Reemplaza con tu API Key
PASSWORD = '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'       # Reemplaza con tu Access Token
SHOP_NAME = 'oofos-espana.myshopify.com'  # Dominio de tu tienda Shopify
API_VERSION = '2024-10'            # Versión de la API (revisa la más reciente)

# URL base de la API
BASE_URL = f"https://{API_KEY}:{PASSWORD}@{SHOP_NAME}/admin/api/{API_VERSION}"

# Cargar el archivo procesado
archivo_procesado = 'archivo_seguimiento_procesado.xlsx'  # Archivo con la info
data = pd.read_excel(archivo_procesado, engine='openpyxl')

# Iterar sobre cada fila para actualizar los pedidos
for index, row in data.iterrows():
    order_id = row['REFERENCIA']          # ID del pedido
    tracking_number = row['URLTRACKING']  # Número de seguimiento
    carrier = row['TRANSPORTISTA']        # Transportista (GLS)

    # Crear el cuerpo de la solicitud para añadir seguimiento
    payload = {
        "fulfillment": {
            "tracking_number": tracking_number,
            "tracking_company": carrier,
            "notify_customer": True  # Envía notificación al cliente
        }
    }

    # Endpoint de la API para crear un "fulfillment" (envío) en el pedido
    endpoint = f"{BASE_URL}/orders/{order_id}/fulfillments.json"

    # Hacer la solicitud POST a la API de Shopify
    response = requests.post(endpoint, json=payload)

    # Comprobar si la solicitud fue exitosa
    if response.status_code == 201:
        print(f"✅ Seguimiento añadido al pedido {order_id}.")
    else:
        print(f"❌ Error al actualizar el pedido {order_id}: {response.text}")
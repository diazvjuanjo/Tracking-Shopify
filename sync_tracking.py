import os
import shopify
import json
import ftplib
import pandas as pd
from io import BytesIO

# Configuración de Shopify
API_KEY = os.getenv("SHOPIFY_API_KEY")
ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")
SHOP_NAME = os.getenv("SHOPIFY_SHOP_NAME")
API_VERSION = "2024-10"

# Configuración del servidor FTP
FTP_HOST = os.getenv("FTP_HOST")
FTP_USER = os.getenv("FTP_USER")
FTP_PASSWORD = os.getenv("FTP_PASSWORD")
FTP_PATH = os.getenv("FTP_PATH")

def setup_shopify_session():
    shopify.Session.setup(api_key=API_KEY)
    session = shopify.Session(f"https://{SHOP_NAME}", API_VERSION, ACCESS_TOKEN)
    shopify.ShopifyResource.activate_session(session)

def clear_shopify_session():
    shopify.ShopifyResource.clear_session()

# Descargar archivo desde el FTP
def download_ftp_file():
    try:
        ftp = ftplib.FTP(FTP_HOST)
        ftp.login(user=FTP_USER, passwd=FTP_PASSWORD)
        print("Conectado al servidor FTP.")

        # Descargar el archivo
        with BytesIO() as f:
            ftp.retrbinary(f"RETR {FTP_PATH}", f.write)
            f.seek(0)
            data = pd.read_excel(f)

        print("Archivo descargado correctamente.")
        ftp.quit()
        return data
    except ftplib.all_errors as e:
        print(f"Error al descargar el archivo desde el FTP: {e}")
        return None


# Procesar el archivo descargado
def process_file(data):
    try:
        # Seleccionar columnas de interés
        data = data.iloc[:, [2, 3]]  # Columnas 3 (REFERENCIA) y 4 (URLTRACKING)
        data.columns = ["REFERENCIA", "URLTRACKING"]
        print("Archivo procesado correctamente.")
        return data
    except Exception as e:
        print(f"Error al procesar el archivo: {e}")
        return None

# Buscar el fulfillment order de un pedido
def find_fulfillment_order(order_name):
    query = f"""
    query {{
      orders(first: 1, query: "name:{order_name}") {{
        edges {{
          node {{
            id
            fulfillmentOrders(first: 5) {{
              edges {{
                node {{
                  id
                  lineItems(first: 50) {{
                    edges {{
                      node {{
                        id
                        remainingQuantity
                      }}
                    }}
                  }}
                }}
              }}
            }}
          }}
        }}
      }}
    }}
    """
    try:
        result = shopify.GraphQL().execute(query)
        if isinstance(result, str):
            result = json.loads(result)
        
        orders_data = result.get("data", {}).get("orders", {}).get("edges", [])
        if not orders_data:
            raise ValueError(f"No se encontró el pedido con nombre {order_name}.")

        # Extraer fulfillmentOrderId y lineItems
        order_data = orders_data[0]["node"]
        fulfillment_orders = order_data["fulfillmentOrders"]["edges"]

        return [(f_order["node"]["id"], f_order["node"]["lineItems"]["edges"]) for f_order in fulfillment_orders]
    except Exception as e:
        print(f"Error al buscar el fulfillment order para {order_name}: {e}")
        return []

# Crear cumplimiento con datos de seguimiento
def create_fulfillment(fulfillment_order_id, line_items, tracking_info):
    line_items_query = ", ".join([
        f"""{{ id: "{line_item['node']['id']}", quantity: {line_item['node']['remainingQuantity']} }}"""
        for line_item in line_items
    ])
    
    query = f"""
    mutation fulfillmentCreateV2 {{
      fulfillmentCreateV2(fulfillment: {{
        notifyCustomer: true,
        trackingInfo: {{
          company: "{tracking_info['company']}",
          number: "Ver aquí",
          url: "{tracking_info['url']}"
        }},
        lineItemsByFulfillmentOrder: [
          {{
            fulfillmentOrderId: "{fulfillment_order_id}",
            fulfillmentOrderLineItems: [{line_items_query}]
          }}
        ]
      }}) {{
        fulfillment {{
          id
          status
          trackingInfo {{
            company
            number
            url
          }}
        }}
        userErrors {{
          field
          message
        }}
      }}
    }}
    """
    try:
        result = shopify.GraphQL().execute(query)
        print("Resultado de crear cumplimiento:")
        print(result)
    except Exception as e:
        print(f"Error al crear el cumplimiento para fulfillmentOrderId {fulfillment_order_id}: {e}")

# Flujo principal para procesar pedidos
def main():
    setup_shopify_session()

    # Descargar y procesar archivo
    raw_data = download_ftp_file()
    if raw_data is None:
        print("No se pudo descargar el archivo. Abortando.")
        return

    data = process_file(raw_data)
    if data is None:
        print("No se pudo procesar el archivo. Abortando.")
        return

    # Iterar sobre cada fila del archivo procesado
    for _, row in data.iterrows():
        referencia = row["REFERENCIA"]
        url_tracking = row["URLTRACKING"]
        tracking_number = url_tracking.split("/")[-1]

        tracking_info = {
            "company": "GLS",
            "number": "Ver aquí",
            "url": url_tracking
        }

        # Buscar fulfillment orders asociados al pedido
        fulfillment_orders = find_fulfillment_order(referencia)
        if not fulfillment_orders:
            print(f"No se encontró fulfillment order para el pedido {referencia}.")
            continue

        # Procesar cada fulfillment order y sus line items
        for fulfillment_order_id, line_items in fulfillment_orders:
            create_fulfillment(fulfillment_order_id, line_items, tracking_info)

    clear_shopify_session()

if __name__ == "__main__":
    main()

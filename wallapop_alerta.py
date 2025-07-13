import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import requests
import time

# I need to change this for my personal token and id before executing
TELEGRAM_TOKEN = "TELEGRAM_TOKEN" 
TELEGRAM_CHAT_ID = "TELEGRAM_CHAT_ID"

KEYWORDS = "steam deck oled"
PRICE_MIN = 100
PRICE_MAX = 350

LAST_SEEN = set()

# 📩 Función para enviar mensajes a Telegram
def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    params = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensaje
    }
    requests.get(url, params=params)

async def buscar_wallapop(page):
    url = (
        f"https://es.wallapop.com/search?"
        f"keywords={KEYWORDS.replace(' ', '%20')}"
        f"&priceMax={PRICE_MAX}"
        f"&order_by=newest"
    )

    await page.goto(url)

        # Intenta aceptar cookies si aparece el aviso
    try:
        boton_cookies = await page.wait_for_selector('#onetrust-accept-btn-handler', timeout=5000)
        if boton_cookies:
            await boton_cookies.click()
            await asyncio.sleep(1)
    except PlaywrightTimeoutError:
        pass  # No apareció el banner de cookies

    # Espera unos segundos mientras se cargan los productos
    max_scroll_time = 20
    scroll_interval = 1
    start_time = time.time()

    productos = []
    while time.time() - start_time < max_scroll_time:
        productos = await page.query_selector_all('a.item-card_ItemCard--vertical__FiFz6')
        if productos:
            break
        await page.evaluate("window.scrollBy(0, window.innerHeight);")
        await asyncio.sleep(scroll_interval)

    if not productos:
        print(f"[{KEYWORDS}] No se encontraron productos.")
        return

    nuevos_encontrados = 0
    mensajes = []

    # Procesa cada producto encontrado
    for prod in productos:
        titulo_el = await prod.query_selector("h3")
        precio_el = await prod.query_selector('strong[aria-label="Item price"]')
        enlace = await prod.get_attribute("href")

        if not titulo_el or not precio_el or not enlace:
            continue

        titulo = await titulo_el.inner_text()
        precio_text = await precio_el.inner_text()
        precio_num_str = ''.join(filter(str.isdigit, precio_text))
        if not precio_num_str:
            continue

        precio_num = int(precio_num_str)

        # Comprueba si cumple el rango de precio y si no ha sido enviado ya
        if PRICE_MIN <= precio_num <= PRICE_MAX and enlace not in LAST_SEEN:
            LAST_SEEN.add(enlace)
            mensaje = f"{titulo}\n{precio_num} €\nhttps://es.wallapop.com{enlace}"
            mensajes.append(mensaje)
            nuevos_encontrados += 1

    # Si hay productos nuevos, primero envía un encabezado, luego cada resultado
    if nuevos_encontrados > 0:
        encabezado = f"...................\n\n📦 Resultados para: {KEYWORDS}\n\n..................."
        enviar_telegram(encabezado)
        for mensaje in mensajes:
            enviar_telegram(mensaje)


# Bucle principal que ejecuta las búsquedas periódicamente
async def main_loop():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)  # No abre ventana
        page = await browser.new_page()

    while True:
        print("\n Iniciando ciclo de búsqueda...")
        await buscar_wallapop(page)
        await asyncio.sleep(2)  # Pequeña pausa entre búsquedas

        print(f"\n Esperando 10 minutos para la siguiente búsqueda...\n")
        await asyncio.sleep(10 * 60)  # Espera 10 mins antes del siguiente ciclo


# Ejecuta el script
if __name__ == "__main__":
    asyncio.run(main_loop())

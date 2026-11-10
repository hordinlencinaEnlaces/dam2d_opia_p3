"""Plantilla: aplicación Streamlit conectada a tu servicio de IA.

Versión final con todos los apartados (a-e) completados.
Autores: Alejandro Felices, Héctor Ordín

Qué hace la app: el usuario introduce 2 variables (ingreso medio y número de
habitaciones); la app completa el resto con valores por defecto, comprueba que
están las 8 variables, llama a la API (POST /predict), transforma la respuesta
a dólares y la muestra.

Dónde está cada apartado:
    a) Conexión ............. URL de la API (API_URL) y petición POST
    b) Datos de entrada ..... find_missing()
    c) Datos de salida ...... format_price() y mostrar el precio
    d) Interfaz ............. campo de número de habitaciones
    e) Control de errores ... fallo de comunicación y respuesta de error
       (la documentación de la API va en el README)

Ejecución en local (con la API en marcha):
    pip install -r requirements.txt
    streamlit run streamlit_app.py
Los mensajes de log salen en la terminal desde la que lanzas Streamlit.
La URL de la API se puede cambiar en la barra lateral. Por defecto (API_URL)
es http://localhost:8000; para el despliegue, API_URL debe ser la URL pública
de tu API en Render (ver API_URL): es la que usará la app desplegada.

Despliegue en Render (segundo Web Service, además del de la API):
    Build Command:  pip install -r requirements.txt
    Start Command:  streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true

Capturas (memoria): deben incluir el nombre del autor y la palabra P3
(ej: Juan Perez P3). Rellena AUTORES más abajo para que salga en la interfaz.

Pruebas desde la barra lateral (para la memoria, apartados b y e):
    - Marcar "omitir HouseAge"                         -> validación local: no se envía nada.
    - Marcar "omitir HouseAge" + "saltar la validación" -> la API responde 422.
    - Cambiar la URL de la API por una incorrecta       -> fallo de comunicación.

Contrato de la API:
    POST /predict, cuerpo JSON con las 8 variables:
        MedInc, HouseAge, AveRooms, AveBedrms, Population, AveOccup,
        Latitude, Longitude
    200  {"MedHouseVal": 4.53}  -> precio en CIENTOS DE MILES de dólares
    422  {"detail": [...]}      -> falta un campo o tiene un tipo incorrecto
    500  texto "Internal Server Error" (¡no es JSON!)
"""
import logging
import time

import requests
import streamlit as st

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("app")

AUTORES = "Alejandro Felices, Héctor Ordín"

# Apartado a: URL pública de tu API en Render (sin barra final).
# Por defecto la app usa la API en local. Antes de desplegar en Render,
# sustituye <tu-servicio-api> por el nombre de tu servicio, comenta la línea
# de localhost y descomenta la de Render: es la que usará la app desplegada.
# API_URL = "http://localhost:8000"  # para pruebas en local
API_URL = "https://<tu-servicio-api>.onrender.com"  # <-- CAMBIA por la URL real de tu API en Render
# Segundos de espera. Con dos servicios dormidos en Render (la API y esta app),
# el arranque en frío puede tardar más de un minuto.
TIMEOUT = 90

# Las 8 variables que necesita el modelo.
FEATURE_NAMES = [
    "MedInc", "HouseAge", "AveRooms", "AveBedrms",
    "Population", "AveOccup", "Latitude", "Longitude",
]

# Variables que NO se piden al usuario (valores aproximados de la mediana del
# dataset de California Housing).
DEFAULTS = {
    "HouseAge": 29.0,
    "AveBedrms": 1.05,
    "Population": 1166.0,
    "AveOccup": 2.8,
    "Latitude": 34.26,
    "Longitude": -118.49,
}


def find_missing(payload: dict) -> list[str]:
    return [name for name in FEATURE_NAMES if payload.get(name) is None]


def format_price(med_house_val: float) -> str:
    precio = med_house_val * 100_000
    return f"${precio:,.0f}"


# ---------------------------------------------------------------- Interfaz --
st.set_page_config(page_title="Precio de casas en California")
st.title("Precio de casas en California")
st.caption(f"{AUTORES} - P3")
st.write("Introduce los datos de la zona y estima el precio medio de sus viviendas.")

# Barra lateral: permite cambiar de servidor y provocar errores de prueba.
api_url = st.sidebar.text_input("URL de la API", API_URL).rstrip("/")
simulate_missing = st.sidebar.checkbox("Prueba: omitir HouseAge de la petición")
skip_validation = st.sidebar.checkbox(
    "Prueba: saltar la validación local (provoca un 422 de la API)"
)

# Variables clave que introduce el usuario.
med_inc = st.number_input(
    "Ingreso medio de la zona (decenas de miles de $)",
    min_value=0.0, max_value=15.0, value=3.5, step=0.1,
)
ave_rooms = st.number_input(
    "Número medio de habitaciones por vivienda",
    min_value=1.0, max_value=15.0, value=5.2, step=0.1,
)

if st.button("Estimar precio"):
    payload = {
        **DEFAULTS,
        "MedInc": med_inc,
        "AveRooms": ave_rooms,
    }
    if simulate_missing:  # solo para la prueba de errores
        payload.pop("HouseAge", None)

    # Apartado b: validar los datos ANTES de enviarlos.
    # Con la casilla "saltar la validación" la petición sale incompleta y es
    # la API quien la rechaza (422), para probar el control de errores (5b).
    missing = find_missing(payload)
    if skip_validation and missing:
        logger.warning("Validación local saltada (prueba). Faltan: %s", missing)
    elif missing:
        logger.warning("Petición no enviada, faltan: %s", missing)
        st.error(f"Faltan variables obligatorias: {', '.join(missing)}")
        st.stop()

    if "<" in api_url:  # sigue el valor de ejemplo de Render: falta configurar API_URL
        st.error("Configura la URL de la API (API_URL o barra lateral).")
        st.stop()

    try:
        start = time.perf_counter()
        with st.spinner("Consultando la API (la primera vez puede tardar más de un minuto)..."):
            response = requests.post(api_url + "/predict", json=payload, timeout=TIMEOUT)
        elapsed_ms = (time.perf_counter() - start) * 1000
    except requests.RequestException as exc:
        logger.error("Fallo de comunicación con %s: %s", api_url, exc)
        st.error(
            "No se pudo contactar con la API (sin conexión, URL incorrecta o "
            "tiempo de espera agotado). Revisa la URL en la barra lateral, "
            "comprueba que el servicio está activo en Render e inténtalo de nuevo."
        )
    else:
        logger.info("POST %s/predict -> HTTP %s en %.0f ms", api_url, response.status_code, elapsed_ms)
        if response.status_code == 200:
            med_house_val = response.json()["MedHouseVal"]
            st.metric("Precio estimado", format_price(med_house_val))
            st.caption(f"Valor devuelto por la API (cientos de miles de $): {med_house_val}")
        else:
            logger.error("La API respondió HTTP %s: %s", response.status_code, response.text)
            st.error(
                f"La API devolvió un error (código {response.status_code}). "
                f"Detalle: {response.text}"
            )

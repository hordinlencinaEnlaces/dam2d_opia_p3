# Aplicación Streamlit para el precio de casas en California

Aplicación web que estima el precio medio de las viviendas de una zona de California a partir de un modelo de
machine learning entrenado con el dataset California Housing. El usuario introduce solo dos datos (ingreso medio y
número medio de habitaciones); la aplicación completa el resto de variables con valores por defecto (mediana del
dataset), comprueba que están las 8 variables que necesita el modelo y consulta la API.

Está formada por dos servicios independientes:

- **API (`app.py`, FastAPI)**: carga `modelo_california.pkl` y expone `POST /predict`, que devuelve la predicción.
- **Interfaz (`streamlit_app.py`, Streamlit)**: formulario web que envía los datos en JSON a la API mediante una petición
  POST a `/predict` (con `requests`) y muestra el resultado convertido a dólares. Gestiona los errores de la API con mensajes claros.

Autores: Alejandro Felices, Héctor Ordín

## Servicios desplegados en Render

| Servicio | Qué es | URL |
|----------|--------|-----|
| API | FastAPI con el modelo (`app.py`) | https://<tu-servicio-api>.onrender.com |
| Interfaz | Streamlit (`streamlit_app.py`), que llama a la API | https://<tu-servicio-streamlit>.onrender.com |

## Cómo ejecutarla en local

```bash
pip install -r requirements.txt

# Terminal 1: API (http://localhost:8000, documentación en /docs)
uvicorn app:app --reload

# Terminal 2: interfaz Streamlit (http://localhost:8501)
streamlit run streamlit_app.py
```

En la barra lateral de la interfaz, pon como URL de la API `http://localhost:8000`.

## Despliegue en Render

Ambos son *Web Services* de Render creados desde el mismo repositorio, con el mismo Build Command.

| Servicio | Build Command | Start Command |
|----------|---------------|---------------|
| API | `pip install -r requirements.txt` | `uvicorn app:app --host 0.0.0.0 --port $PORT` |
| Interfaz | `pip install -r requirements.txt` | `streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true` |

La URL de la API que usa la interfaz se cambia en `streamlit_app.py`, en la constante `API_URL` (arriba del fichero),
o en caliente desde el campo «URL de la API» de la barra lateral. Con el plan gratuito los servicios se duermen: la
primera petición puede tardar más de un minuto.

## Documentación de la API

URL base: <https://tu-servicio-api.onrender.com>

### `POST /predict`

Recibe un JSON con las 8 variables de una zona censal (todas numéricas y obligatorias) y devuelve el precio medio
estimado de sus viviendas en `MedHouseVal`, expresado en **cientos de miles de dólares** (1.51 = 151,260 $).

**Ejemplo de petición**

```json
{
  "MedInc": 3.5,
  "HouseAge": 29.0,
  "AveRooms": 5.2,
  "AveBedrms": 1.05,
  "Population": 1166.0,
  "AveOccup": 2.8,
  "Latitude": 34.26,
  "Longitude": -118.49
}
```

**Ejemplo de respuesta correcta (200)**

```json
{
  "MedHouseVal": 1.5126018234536092
}
```

**Errores**

| Código | Cuándo ocurre | Qué muestra la aplicación |
|--------|---------------|---------------------------|
| 422 | Falta un campo o tiene un tipo incorrecto | `La API devolvió un error (código 422). Detalle: ...` con el detalle devuelto por la API |
| Sin respuesta | La API no está disponible o tarda demasiado | `No se pudo contactar con la API ...` con indicaciones para revisar la URL y el servicio |
| 500 | Error interno de la API (el cuerpo no es JSON) | `La API devolvió un error (código 500). Detalle: Internal Server Error` |

La aplicación valida localmente las 8 variables antes de enviar la petición; si falta alguna, no se envía y se
muestra cuáles faltan.

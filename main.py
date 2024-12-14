import datetime
import json
from typing import Union

import pytz
# Ensure 'fastapi' is installed in your environment by running: pip install fastapi
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from services.airquality import get_no2
from services.roads import get_roads
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()
madrid_tz = pytz.timezone("Europe/Madrid")

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "API de servicios de geolocalización"}


@app.get("/roads")
def get_roads_endpoint(lat: float, lon: float, distancia: int = 1000):
    """
    Endpoint para obtener los caminos cercanos a un punto geográfico.
    Parámetros:
        - lat: Latitud
        - lon: Longitud
        - distancia: Radio de búsqueda en metros (por defecto 1000)

    Retorna:
        - Un GeoDataFrame con la información de las calles
    """
    try:
        # Llamar a la función get_roads para obtener los datos
        roads_data = get_roads(lat, lon, distancia)

        # Convertir el GeoDataFrame en formato JSON para la respuesta
        roads_json = roads_data.to_json()
        json_object = json.loads(roads_json)
        # parse json
        return json_object
    except Exception as e:
        # Manejar errores y retornar una respuesta adecuada
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/airquality")
def get_airquality(lat: float, lon: float, distancia: int = 1000, date: str = None):
    """
    Endpoint para obtener datos de calidad del aire a partir de coordenadas.

    Parámetros:
        - lat: Latitud
        - lon: Longitud

    Retorna:
        - Un JSON con información de calidad del aire.
    """
    try:
        if date:
            new_date = datetime.datetime.fromisoformat(date) if date else None
        else:
            new_date = datetime.datetime.fromisoformat("2021-01-01T00:00:00")
        year = new_date.year if date else None
        month = new_date.month if date else None
        day = new_date.day if date else None
        hour = new_date.hour if date else None

        # Obtener el día y la hora en 2 digitos en string

        data = get_no2(dia=str(day).zfill(2), mes=str(month).zfill(2), hora=hour, center_coordinate_lat=lat, center_coordinate_lon=lon)

        return data

    except Exception as e:
        # Manejo de errores y respuesta en caso de fallo
        raise HTTPException(status_code=500, detail=str(e))
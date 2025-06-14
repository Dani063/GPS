import os
import requests
import numpy as np
import cv2

def obtener_mapa_google(lat, lon, zoom=16, size=(600, 400),
                        maptype='roadmap', scale=2, fmt='jpg', key=None):
    """
    Construye la URL con parámetros de Google Static Maps,
    descarga la imagen y la decodifica con OpenCV.
    Requiere GOOGLE_API_KEY en variable de entorno o key.
    """
    key = 'AIzaSyC9MmrD6Qe4MsZ_zQWWPheTFdLTI9Axsf8'
    if not key:
        raise RuntimeError('Falta GOOGLE_API_KEY en variables de entorno')
    params = {
        'center': f'{lat},{lon}',
        'zoom': zoom,
        'size': f'{size[0]}x{size[1]}',
        'scale': scale,
        'format': fmt,
        'maptype': maptype,
        'key': key
    }
    url = 'https://maps.googleapis.com/maps/api/staticmap'
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    arr = np.frombuffer(resp.content, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return img

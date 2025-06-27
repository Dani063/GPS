import folium
import utm
import time
import webview
import threading
import os
import numpy as np
from leer_datos import obtener_coordenadas
from medir_velocidad import obtener_velocidad_maxima, mostrar_alerta

MAP_FILE = "mapa.html"
coord_1 = (40.424217, -3.809688)
coord_2 = (40.423143, -3.806340)

# Convertir a UTM
utm_1 = utm.from_latlon(*coord_1)
utm_2 = utm.from_latlon(*coord_2)

AREA_PISTA = {
    "norte_max": utm_1[1],  # Norte máximo
    "norte_min": utm_2[1],  # Norte mínimo
    "este_max": utm_1[0],   # Este máximo
    "este_min": utm_2[0]    # Este mínimo
}

puntos_historicos = []
velocidad_actual = 0
texto_alerta = ""
color_alerta = (255, 255, 255)
mapa_csv = None

def cargar_mapa_electronico():
    ruta_mapa = os.path.join(os.path.dirname(__file__), "..", "Recursos", "mapa_electronico.csv")
    try:
        mapa = np.genfromtxt(ruta_mapa, delimiter=',', dtype=None, encoding=None, names=True)
        print(f"[INFO] Mapa electrónico cargado: {ruta_mapa}")
        return mapa
    except Exception as e:
        print(f"[ERROR] No se pudo cargar el mapa electrónico: {e}")
        return None

def crear_mapa(lat, lon):
    global puntos_historicos, texto_alerta, color_alerta
    m = folium.Map(location=[lat, lon], zoom_start=17, control_scale=True)

    # Ruta histórica
    if len(puntos_historicos) > 1:
        folium.PolyLine(puntos_historicos, color="blue", weight=4.5, opacity=0.7).add_to(m)

    # Punto actual
    folium.Marker(
        [lat, lon],
        tooltip=texto_alerta,
        icon=folium.Icon(color="red" if color_alerta == (0, 0, 255) else
                         "green" if color_alerta == (0, 255, 0) else "orange")
    ).add_to(m)

    m.save(MAP_FILE)

def dentro_de_area(utm_n, utm_e):
    return (AREA_PISTA["norte_min"] <= utm_n <= AREA_PISTA["norte_max"] and
            AREA_PISTA["este_min"] <= utm_e <= AREA_PISTA["este_max"])

def actualizar_posicion():
    global puntos_historicos, velocidad_actual, texto_alerta, color_alerta, mapa_csv
    prev_pos = None
    prev_time = None

    while True:
        datos = obtener_coordenadas()
        if not datos:
            time.sleep(2)
            continue

        utm_e, utm_n, zone_number, zone_letter = datos
        lat, lon = utm.to_latlon(utm_e, utm_n, zone_number, zone_letter)

        # Ruta histórica
        puntos_historicos.append((lat, lon))
        if len(puntos_historicos) > 100:
            puntos_historicos.pop(0)

        # Velocidad
        ahora = time.time()
        if prev_pos and prev_time:
            dx = utm_e - prev_pos[0]
            dy = utm_n - prev_pos[1]
            dt = ahora - prev_time
            velocidad_actual = (np.hypot(dx, dy) / dt) * 3.6
        else:
            velocidad_actual = 0.0
        prev_pos = (utm_e, utm_n)
        prev_time = ahora

        # Mostrar velocidad solo dentro del área designada
        if dentro_de_area(utm_n, utm_e) and mapa_csv is not None:
            vel_max = obtener_velocidad_maxima(utm_n, utm_e, mapa_csv)
            if vel_max is not None:
                color_alerta, texto_alerta = mostrar_alerta(velocidad_actual, vel_max)
            else:
                texto_alerta = f"{velocidad_actual:.1f} Km/h"
                color_alerta = (255, 255, 255)
        else:
            texto_alerta = ""  # No mostrar velocidad fuera del área
            color_alerta = (255, 255, 255)

        crear_mapa(lat, lon)
        time.sleep(2)

def iniciar_visor():
    html = f"""
    <html>
    <head>
        <meta http-equiv="refresh" content="2">
    </head>
    <body>
        <iframe src="{MAP_FILE}" width="100%" height="100%" frameborder="0"></iframe>
    </body>
    </html>
    """
    with open("visor.html", "w", encoding="utf-8") as f:
        f.write(html)
    webview.create_window("Práctica 4 - Mapa Online GPS", "visor.html", width=900, height=700, resizable=True)
    webview.start()

if __name__ == "__main__":
    mapa_csv = cargar_mapa_electronico()
    hilo = threading.Thread(target=actualizar_posicion, daemon=True)
    hilo.start()
    iniciar_visor()
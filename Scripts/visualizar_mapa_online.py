# python
import os
import time
import cv2
import numpy as np
import utm
import logging
import concurrent.futures
from leer_datos import obtener_coordenadas
from google_static_map import obtener_mapa_google

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define AREA_PISTA
coord_1 = (40.424217, -3.809688)
coord_2 = (40.423143, -3.806340)
utm_1 = utm.from_latlon(*coord_1)
utm_2 = utm.from_latlon(*coord_2)
AREA_PISTA = {
    "norte_max": utm_1[1],
    "norte_min": utm_2[1],
    "este_max": utm_1[0],
    "este_min": utm_2[0]
}

# Global zoom level and zoom change flag
zoom_level = 17
zoom_changed = False

def dentro_de_area(utm_n, utm_e):
    """Check if the position is within AREA_PISTA."""
    return (AREA_PISTA["norte_min"] <= utm_n <= AREA_PISTA["norte_max"] and
            AREA_PISTA["este_min"] <= utm_e <= AREA_PISTA["este_max"])

def dibujar_interfaz(velocidad, color, texto, frame):
    """Draw the speed meter only if inside AREA_PISTA."""
    cv2.rectangle(frame, (10, 10), (300, 100), (50, 50, 50), -1)
    cv2.rectangle(frame, (10, 10), (300, 100), (200, 200, 200), 2)
    cv2.putText(frame, texto, (20, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2, cv2.LINE_AA)

def mouse_scroll(event, x, y, flags, param):
    """Handle mouse scroll to adjust zoom level."""
    global zoom_level, zoom_changed
    if event == cv2.EVENT_MOUSEWHEEL:
        if flags > 0:  # Scroll up
            zoom_level = min(zoom_level + 1, 20)  # Max zoom level is 20
        else:  # Scroll down
            zoom_level = max(zoom_level - 1, 0)  # Min zoom level is 0
        zoom_changed = True  # Mark zoom as changed
        logging.info(f"Zoom level updated: {zoom_level}")

def main():
    global zoom_level, zoom_changed
    ruta_csv = os.path.abspath(os.path.join(
        os.path.dirname(__file__), '..', 'Recursos', 'mapa_electronico.csv'))
    logging.info('Iniciando servicio georeferenciado online')

    size = (600, 400)
    blank = np.zeros((size[1], size[0], 3), dtype=np.uint8)
    current_map = blank.copy()
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    map_future = None

    window = 'Mapa Georreferenciado'
    cv2.namedWindow(window, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(window, cv2.WND_PROP_ASPECT_RATIO, cv2.WINDOW_KEEPRATIO)
    cv2.setMouseCallback(window, mouse_scroll)

    prev_pos = None
    prev_time = None
    last_map_pos = None

    while True:
        datos = obtener_coordenadas()
        if not datos:
            logging.warning('No hay coordenadas válidas')
            time.sleep(1)
            continue

        x_utm, y_utm, z_num, z_let = datos
        lat, lon = utm.to_latlon(x_utm, y_utm, z_num, z_let)
        ahora = time.time()

        # Calcular velocidad
        velocidad = 0.0
        if prev_pos:
            dx = x_utm - prev_pos[0]
            dy = y_utm - prev_pos[1]
            dt = ahora - prev_time
            velocidad = (np.hypot(dx, dy) / dt) * 3.6

        prev_pos = (x_utm, y_utm)
        prev_time = ahora

        # Verificar si necesitamos actualizar el mapa (por posición o zoom change)
        if zoom_changed or not last_map_pos or np.hypot(x_utm - last_map_pos[0], y_utm - last_map_pos[1]) > 50:
            if not map_future or map_future.done():
                logging.info(f'Actualizando mapa por cambio de zoom o movimiento significativo...')
                map_future = executor.submit(
                    obtener_mapa_google,
                    lat, lon,
                    zoom=zoom_level,  # Use dynamic zoom level
                    size=size,
                    maptype='satellite',
                    scale=2,
                    fmt='jpg'
                )
                last_map_pos = (x_utm, y_utm)
                zoom_changed = False  # Reset zoom change flag

        # Use the last available map if the new one isn't ready yet
        if map_future and map_future.done():
            try:
                current_map = map_future.result()
                logging.info('Mapa satélite actualizado.')
            except Exception as e:
                logging.error(f'Error al descargar mapa: {e}')
                current_map = blank.copy()

        frame = current_map.copy()

        # marcador con estética
        h, w = frame.shape[:2]
        centro = (w // 2, h // 2)
        radius = 10
        cv2.circle(frame, centro, radius, (209, 45, 40), -1)
        cv2.circle(frame, centro, radius, (255, 255, 255), 2)

        # Mostrar medidor de velocidad solo dentro de AREA_PISTA
        if dentro_de_area(y_utm, x_utm):
            color, texto = (255, 255, 255), f'{velocidad:.1f} Km/h'
            dibujar_interfaz(velocidad, color, texto, frame)

        cv2.imshow(window, frame)

        time.sleep(0.01)
        if cv2.waitKey(30) & 0xFF == 27:
            break
        if cv2.getWindowProperty(window, cv2.WND_PROP_VISIBLE) < 1:
            break

    executor.shutdown(wait=False)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
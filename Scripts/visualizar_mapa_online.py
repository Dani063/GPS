import os
import time
import cv2
import numpy as np
import utm
import logging
import concurrent.futures
from leer_datos import obtener_coordenadas
from medir_velocidad import obtener_velocidad_maxima, mostrar_alerta
from google_static_map import obtener_mapa_google

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def dibujar_interfaz(velocidad, color, texto, frame):
    cv2.rectangle(frame, (10, 10), (300, 100), (50, 50, 50), -1)
    cv2.rectangle(frame, (10, 10), (300, 100), (200, 200, 200), 2)
    cv2.putText(frame, texto, (20, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2, cv2.LINE_AA)

def distancia(p1, p2):
    return np.hypot(p1[0] - p2[0], p1[1] - p2[1])

def main():
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
        if prev_pos:
            dx = x_utm - prev_pos[0]
            dy = y_utm - prev_pos[1]
            dt = ahora - prev_time
            velocidad = (np.hypot(dx, dy) / dt) * 3.6
        else:
            velocidad = 0.0

        prev_pos = (x_utm, y_utm)
        prev_time = ahora

        # Verificar si necesitamos actualizar el mapa (cada 50 m)
        if not last_map_pos or distancia((x_utm, y_utm), last_map_pos) > 50:
            if not map_future or map_future.done():
                logging.info(f'Actualizando mapa por movimiento significativo...')
                map_future = executor.submit(
                    obtener_mapa_google,
                    lat, lon,
                    zoom=17,
                    size=size,
                    maptype='satellite',
                    scale=2,
                    fmt='jpg'
                )
                last_map_pos = (x_utm, y_utm)

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
        radius = 70
        cv2.circle(frame, centro, radius, (209, 45, 40), -1)
        cv2.circle(frame, centro, radius, (255, 255, 255), 10)

        # Alerta de velocidad
        mapa_csv = np.genfromtxt(ruta_csv, delimiter=',',
                                 names=True, dtype=None, encoding=None)
        vel_max = obtener_velocidad_maxima(y_utm, x_utm, mapa_csv)
        if vel_max is None:
            color, texto = (255, 255, 255), f'{velocidad:.1f} Km/h'
        else:
            color, texto = mostrar_alerta(velocidad, vel_max)

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

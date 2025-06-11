# python
import cv2
import numpy as np
import utm
import logging
import time
from leer_datos import obtener_coordenadas
from threading import Thread

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def latlon_to_pixel(lat, lon, top_left, bottom_right, image_shape):
    lat_top, lon_left = top_left
    lat_bottom, lon_right = bottom_right

    x = int((lon - lon_left) / (lon_right - lon_left) * image_shape[1])
    y = int((lat_top - lat) / (lat_top - lat_bottom) * image_shape[0])

    x = max(0, min(image_shape[1] - 1, x))
    y = max(0, min(image_shape[0] - 1, y))
    return x, y

def zoom_and_pan(event, x, y, flags, params):
    global zoom_factor, pan_x, pan_y, image
    h, w = image.shape[:2]
    if event == cv2.EVENT_MOUSEWHEEL:
        old_zoom = zoom_factor
        # Actualizar el factor de zoom
        if flags > 0:
            new_zoom = zoom_factor * 1.1
        else:
            new_zoom = zoom_factor / 1.1
        zoom_factor = min(max(new_zoom, 1.0), 5.0)
        # Ajustar pan_x y pan_y para hacer zoom relativo al puntero
        # La conversión usa la relación entre el puntero y la escala inversa
        pan_x = pan_x + (x / old_zoom) - (x / zoom_factor)
        pan_y = pan_y + (y / old_zoom) - (y / zoom_factor)
        logging.debug(f"Nuevo zoom: {zoom_factor}, pan: ({pan_x}, {pan_y})")
    elif event == cv2.EVENT_LBUTTONDOWN:
        params['dragging'] = True
        params['start_x'], params['start_y'] = x, y
    elif event == cv2.EVENT_MOUSEMOVE and params['dragging']:
        dx, dy = x - params['start_x'], y - params['start_y']
        # Invertir el arrastre: al mover el mouse a la derecha se desplaza la imagen a la izquierda
        pan_x -= dx / zoom_factor
        pan_y -= dy / zoom_factor
        params['start_x'], params['start_y'] = x, y
        logging.debug(f"Arrastre invertido, pan: ({pan_x}, {pan_y})")
    elif event == cv2.EVENT_LBUTTONUP:
        params['dragging'] = False

def update_display():
    global display_image, image, last_position, zoom_factor, pan_x, pan_y
    h, w = image.shape[:2]
    new_w, new_h = int(w / zoom_factor), int(h / zoom_factor)
    x_start = max(0, min(w - new_w, int(pan_x)))
    y_start = max(0, min(h - new_h, int(pan_y)))
    x_end, y_end = x_start + new_w, y_start + new_h

    cropped = image[y_start:y_end, x_start:x_end]
    resized = cv2.resize(cropped, (w, h))
    display_image = resized.copy()

    if last_position:
        # Convertir la posición original a la de la imagen actual
        rel_x = (last_position[0] - x_start) * (w / new_w)
        rel_y = (last_position[1] - y_start) * (h / new_h)
        # Escalar el radio de acuerdo al zoom (aumenta con zoom_factor)
        radius = 70
        logging.debug("Dibujando círculo en (%s, %s) con radio constante %s", int(rel_x), int(rel_y), radius)
        cv2.circle(display_image, (int(rel_x), int(rel_y)), radius, (209, 45, 40), -1)
        cv2.circle(display_image, (int(rel_x), int(rel_y)), radius, (255, 255, 255), 10)

def fetch_coordinates():
    global last_position, top_left, bottom_right, image
    while True:
        coordenadas = obtener_coordenadas()
        if coordenadas:
            x_utm, y_utm, zone_number, zone_letter = coordenadas
            lat, lon = utm.to_latlon(x_utm, y_utm, zone_number, zone_letter)
            last_position = latlon_to_pixel(lat, lon, top_left, bottom_right, image.shape)
        time.sleep(2)

def main():
    global zoom_factor, pan_x, pan_y, image, display_image, last_position, top_left, bottom_right
    zoom_factor = 1.0
    pan_x, pan_y = 0, 0
    last_position = None

    top_left = (40.4413680, -3.8236194) #42.4695791, -6.0826056
    bottom_right = (40.4140750, -3.7704831) #42.4415865, -6.0191640

    image_path = "C:/Users/danie/PycharmProjects/GPS/Recursos/Mapa.jpg"
    image = cv2.imread(image_path)
    if image is None:
        logging.error("Error: No se pudo cargar la imagen.")
        return
    display_image = image.copy()

    cv2.namedWindow("Mapa georreferenciado", cv2.WINDOW_NORMAL)
    mouse_params = {'dragging': False, 'start_x': 0, 'start_y': 0}
    cv2.setMouseCallback("Mapa georreferenciado", zoom_and_pan, mouse_params)

    coord_thread = Thread(target=fetch_coordinates, daemon=True)
    coord_thread.start()

    while True:
        if cv2.getWindowProperty("Mapa georreferenciado", cv2.WND_PROP_VISIBLE) < 1:
            break

        update_display()
        cv2.imshow("Mapa georreferenciado", display_image)
        key = cv2.waitKey(30) & 0xFF
        if key == 27:
            break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
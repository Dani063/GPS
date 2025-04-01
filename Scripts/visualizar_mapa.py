import cv2
import numpy as np
import utm
from leer_datos import obtener_coordenadas  # Importa el script de lectura de datos


def latlon_to_pixel(lat, lon, top_left, bottom_right, image_shape):
    lat_top, lon_left = top_left
    lat_bottom, lon_right = bottom_right

    x = int((lon - lon_left) / (lon_right - lon_left) * image_shape[1])
    y = int((lat_top - lat) / (lat_top - lat_bottom) * image_shape[0])

    return x, y


def zoom_and_pan(event, x, y, flags, param):
    global zoom_factor, pan_x, pan_y, display_image

    if event == cv2.EVENT_MOUSEWHEEL:
        if flags > 0:  # Zoom in
            zoom_factor = min(zoom_factor * 1.2, 5.0)
        else:  # Zoom out
            zoom_factor = max(zoom_factor / 1.2, 1.0)

    elif event == cv2.EVENT_LBUTTONDOWN:
        param['dragging'] = True
        param['start_x'], param['start_y'] = x, y

    elif event == cv2.EVENT_MOUSEMOVE and param['dragging']:
        pan_x += (x - param['start_x'])
        pan_y += (y - param['start_y'])
        param['start_x'], param['start_y'] = x, y

    elif event == cv2.EVENT_LBUTTONUP:
        param['dragging'] = False

    update_display()


def update_display():
    global display_image, image, last_position
    h, w = image.shape[:2]
    new_w, new_h = int(w / zoom_factor), int(h / zoom_factor)
    x_start, y_start = max(0, min(w - new_w, pan_x)), max(0, min(h - new_h, pan_y))
    x_end, y_end = x_start + new_w, y_start + new_h

    resized = cv2.resize(image[y_start:y_end, x_start:x_end], (w, h))
    display_image = resized.copy()

    if last_position:
        x, y = last_position
        cv2.circle(display_image, (x, y), 10, (0, 0, 255), -1)


def main():
    global zoom_factor, pan_x, pan_y, image, display_image, last_position
    zoom_factor = 1.0
    pan_x, pan_y = 0, 0
    last_position = None

    # Coordenadas de las esquinas de la imagen (latitud, longitud)
    top_left = (40.4361028, -3.8260611)  # 40°26'9.97"N 3°49'33.82"O
    bottom_right = (40.4172361, -3.7676194)  # 40°25'2.05"N 3°46'3.43"O

    # Cargar imagen
    image_path = "C:/Users/claud/PycharmProjects/GPS/Recursos/Mapa.jpg"
    image = cv2.imread(image_path)
    if image is None:
        print("Error: No se pudo cargar la imagen.")
        return
    display_image = image.copy()

    cv2.namedWindow("Mapa georreferenciado", cv2.WINDOW_NORMAL)
    mouse_params = {'dragging': False, 'start_x': 0, 'start_y': 0}
    cv2.setMouseCallback("Mapa georreferenciado", zoom_and_pan, mouse_params)

    while True:
        # Obtener coordenadas UTM en tiempo real
        coordenadas = obtener_coordenadas()
        if coordenadas:
            x_utm, y_utm, zone_number, zone_letter = coordenadas
            lat, lon = utm.to_latlon(x_utm, y_utm, zone_number, zone_letter)
            x, y = latlon_to_pixel(lat, lon, top_left, bottom_right, image.shape)
            last_position = (x, y)

        update_display()
        cv2.imshow("Mapa georreferenciado", display_image)
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # Presionar ESC para salir
            break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

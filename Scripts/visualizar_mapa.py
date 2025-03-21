import cv2
import numpy as np
from leer_datos import obtener_coordenadas  # Importa el script de lectura de datos


def latlon_to_pixel(lat, lon, top_left, bottom_right, image_shape):
    lat_top, lon_left = top_left
    lat_bottom, lon_right = bottom_right

    x = int((lon - lon_left) / (lon_right - lon_left) * image_shape[1])
    y = int((lat_top - lat) / (lat_top - lat_bottom) * image_shape[0])

    return x, y


def main():
    # Coordenadas de las esquinas de la imagen (puedes ajustar estos valores)
    top_left = (40.4404583, -3.8027306)
    bottom_right = (40.4369417, -3.7834056)

    # Cargar imagen
    image_path = "C:/Users/danie/Downloads/Mapa.jpg"
    image = cv2.imread(image_path)
    if image is None:
        print("Error: No se pudo cargar la imagen.")
        return

    # Obtener coordenadas GPS (del script de lectura)
    coordenadas = obtener_coordenadas()
    if coordenadas:
        x_utm, y_utm, _, _ = coordenadas

        # Convertir coordenadas UTM a GPS (latitud, longitud)
        lat = (y_utm - 0) / 111319.9  # Aproximación
        lon = (x_utm - 0) / 111319.9  # Aproximación

        # Convertir coordenadas GPS a píxeles en la imagen
        x, y = latlon_to_pixel(lat, lon, top_left, bottom_right, image.shape)

        # Dibujar el punto en la imagen
        cv2.circle(image, (x, y), 10, (0, 0, 255), -1)

        # Mostrar la imagen con la posición
        cv2.imshow("Mapa georreferenciado", image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    else:
        print("No se pudieron obtener coordenadas GPS.")


if __name__ == "__main__":
    main()

import cv2
import numpy as np
import serial
import pynmea2
import utm


def latlon_to_pixel(lat, lon, top_left, bottom_right, image_shape):
    lat_top, lon_left = top_left
    lat_bottom, lon_right = bottom_right

    x = int((lon - lon_left) / (lon_right - lon_left) * image_shape[1])
    y = int((lat_top - lat) / (lat_top - lat_bottom) * image_shape[0])

    return x, y


def get_gps_coordinates(port='/dev/ttyUSB0', baudrate=9600):
    try:
        with serial.Serial(port, baudrate, timeout=1) as ser:
            while True:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line.startswith('$GPGGA'):
                    msg = pynmea2.parse(line)
                    return msg.latitude, msg.longitude
    except serial.SerialException as e:
        print(f"Error al acceder al puerto serie: {e}")
    except pynmea2.ParseError:
        print("Error al analizar datos NMEA")
    return None, None


def convert_to_utm(lat, lon):
    utm_x, utm_y, zone_number, zone_letter = utm.from_latlon(lat, lon)
    return utm_x, utm_y, zone_number, zone_letter


def main():
    # Coordenadas de las esquinas de la imagen
    top_left = (40.3925763, -3.6386480)
    bottom_right = (40.3852558, -3.6186850)

    # Cargar imagen
    image_path = "C:/Users/danie/Downloads/Foto GPS.png"  # Especifica el nombre del archivo de la imagen
    image = cv2.imread(image_path)
    if image is None:
        print("Error: No se pudo cargar la imagen.")
        return

    # Obtener coordenadas GPS reales
    gps_lat, gps_lon = get_gps_coordinates('COM3', 9600)  # Cambia COM3 por el puerto correcto en Windows
    if gps_lat is None or gps_lon is None:
        print("No se pudieron obtener coordenadas del GPS")
        return

    # Convertir coordenadas GPS a UTM
    utm_x, utm_y, zone_number, zone_letter = convert_to_utm(gps_lat, gps_lon)
    print(f"Coordenadas UTM: X={utm_x}, Y={utm_y}, Zona={zone_number}{zone_letter}")

    # Convertir coordenadas GPS a píxeles
    x, y = latlon_to_pixel(gps_lat, gps_lon, top_left, bottom_right, image.shape)

    # Dibujar el punto en la imagen
    cv2.circle(image, (x, y), 10, (0, 0, 255), -1)

    # Mostrar imagen
    cv2.imshow("Mapa georreferenciado", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-

import os
import csv
import time
import serial
import pynmea2
import utm
import logging

def inicializar_csv(ruta_csv):
    """
    Inicializa el archivo CSV con encabezados si no existe.
    """
    if not os.path.exists(ruta_csv):
        with open(ruta_csv, mode='w', newline='', encoding='utf-8') as archivo:
            writer = csv.writer(archivo, delimiter=',')
            writer.writerow(['UTM_Norte', 'UTM_Este', 'Velocidad_Actual'])
        print(f"Archivo creado: {ruta_csv}")
    else:
        print(f"Archivo existente: {ruta_csv}")

def leer_gps(serial_port, baud_rate, timeout=1):
    """
    Conecta al puerto serial del GPS y genera sentencias NMEA.
    """
    try:
        ser = serial.Serial(serial_port, baud_rate, timeout=timeout)
        print(f"Conectado al puerto {serial_port} a {baud_rate} baudios.")
        return ser
    except serial.SerialException as e:
        logging.error(f"Error al conectar al puerto serial: {e}")
        return None

def procesar_sentencias(ser, ruta_csv):
    """
    Lee y procesa las sentencias NMEA del GPS, y escribe los datos en el CSV.
    """
    try:
        with open(ruta_csv, mode='a', newline='', encoding='utf-8') as archivo:
            writer = csv.writer(archivo, delimiter=',')
            while True:
                try:
                    linea = ser.readline().decode('ascii', errors='replace')
                    if linea.startswith('$GPRMC') or linea.startswith('$GPGGA'):
                        msg = pynmea2.parse(linea)
                        if isinstance(msg, pynmea2.types.talker.RMC):
                            if msg.status == 'A':
                                lat = msg.latitude
                                lon = msg.longitude
                                velocidad_knots = float(msg.spd_over_grnd) if msg.spd_over_grnd else 0.0
                                velocidad_kmh = velocidad_knots * 1.852  # Convertir a Km/h
                                utm_conv = utm.from_latlon(lat, lon)
                                utm_norte = utm_conv[1]
                                utm_este = utm_conv[0]
                                
                                writer.writerow([f"{utm_norte:.3f}", f"{utm_este:.4f}", f"{velocidad_kmh:.2f}"])
                                print(f"UTM_Norte: {utm_norte:.3f}, UTM_Este: {utm_este:.4f}, Velocidad: {velocidad_kmh:.2f} Km/h")
                        elif isinstance(msg, pynmea2.types.talker.GGA):
                            # Puedes procesar sentencias GGA si lo deseas
                            pass
                except pynmea2.ParseError as e:
                    logging.warning(f"No se pudo parsear la linea: {e}")
    except KeyboardInterrupt:
        print("\nCaptura de datos detenida por el usuario.")
    except Exception as e:
        logging.error(f"Error durante la captura de datos: {e}")
    finally:
        if ser and ser.is_open:
            ser.close()
            print("Puerto serial cerrado.")

def main():
    # Configuraci?n de logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Definir la ruta al archivo CSV
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    recursos_dir = os.path.join(project_dir, "Recursos")

    # Crear la carpeta Recursos si no existe
    if not os.path.exists(recursos_dir):
        os.makedirs(recursos_dir)
        print(f"Directorio creado: {recursos_dir}")

    ruta_csv = os.path.join(recursos_dir, "mapa_electronico.csv")

    # Inicializar el CSV
    inicializar_csv(ruta_csv)

    # Configuraci?n del puerto serial del GPS
    # Reemplaza 'COM3' con el puerto correspondiente en tu sistema (por ejemplo, '/dev/ttyUSB0' en Linux)
    serial_port = 'COM3'  # Cambia esto seg?n tu configuraci?n
    baud_rate = 4800      # Cambia esto si tu GPS usa una tasa de baudios diferente

    # Conectar al GPS
    ser = leer_gps(serial_port, baud_rate)

    if ser:
        # Procesar las sentencias y escribir en el CSV
        procesar_sentencias(ser, ruta_csv)

if __name__ == "__main__":
    main()

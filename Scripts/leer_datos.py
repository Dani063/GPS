# python
from time import sleep
import serial
import utm
import time

def leer_datos(puerto_serie="COM3", baudrate=4800, timeout=1):
    try:
        print(f"Intentando conectar al puerto {puerto_serie} con baudrate {baudrate}...")
        ser = serial.Serial(puerto_serie, baudrate, timeout=timeout,
                            bytesize=8, parity='N', stopbits=1, rtscts=False)
        print("Conexión establecida. Leyendo datos...")
        while True:
            linea = ser.readline().decode('ascii', errors='ignore')
            if linea:
                print(f"Trama recibida: {linea.strip()}")
                if linea.startswith("$GPGGA"):
                    print("Trama GPGGA detectada.")
                    # Aquí podrías extraer información adicional si es necesario
                    continue
                elif linea.startswith("$GPRMC"):
                    print("Trama GPRMC detectada.")
                    return linea.strip()
    except serial.SerialException as e:
        print(f"Error de puerto serial: {e}")
    except AttributeError as e:
        print(f"Error de atributo en el módulo serial: {e}")
    except Exception as e:
        print(f"Ocurrió un error: {e}")
    return None  # Asegura que la función siempre retorne algo

def parsear_trama_gprmc(trama):
    print(f"Parseando trama GPRMC: {trama}")
    partes = trama.split(',')
    if partes[0] == "$GPRMC" and partes[2] == 'A':  # 'A' indica datos válidos
        latitud = partes[3]
        latitud_dir = partes[4]
        longitud = partes[5]
        longitud_dir = partes[6]
        velocidad_nodo = partes[7]
        velocidad_kmh = float(velocidad_nodo) * 1.852  # Convertir de nudos a km/h
        print(f"Latitud: {latitud} {latitud_dir}, Longitud: {longitud} {longitud_dir}, Velocidad: {velocidad_kmh} Km/h")
        return latitud, latitud_dir, longitud, longitud_dir, velocidad_kmh
    print("Trama no válida para GPRMC.")
    return None

def convertir_a_decimal(grados_minutos, direccion):
    print(f"Convirtiendo a decimal: {grados_minutos} {direccion}")
    # Usar 2 dígitos para latitud y 3 para longitud según la dirección
    if direccion in ['N', 'S']:
        grados = float(grados_minutos[:2])
        minutos = float(grados_minutos[2:])
    elif direccion in ['E', 'W']:
        grados = float(grados_minutos[:3])
        minutos = float(grados_minutos[3:])
    else:
        raise ValueError("Dirección inválida")
    decimal = grados + minutos / 60.0
    if direccion in ['S', 'W']:
        decimal = -decimal
    print(f"Coordenada decimal: {decimal}")
    return decimal

def convertir_a_utm(latitud, latitud_dir, longitud, longitud_dir):
    print(f"Convirtiendo a UTM: Latitud {latitud} {latitud_dir}, Longitud {longitud} {longitud_dir}")
    latitud_decimal = convertir_a_decimal(latitud, latitud_dir)
    longitud_decimal = convertir_a_decimal(longitud, longitud_dir)
    coordenadas_utm = utm.from_latlon(latitud_decimal, longitud_decimal)
    print(f"Coordenadas UTM: {coordenadas_utm}")
    return coordenadas_utm

def obtener_coordenadas():
    puerto = "COM3"  # Puerto donde está conectado el GPS
    print(f"Obteniendo coordenadas desde el puerto {puerto}...")
    trama_gprmc = leer_datos(puerto_serie=puerto)
    if trama_gprmc:
        print(f"Trama GPRMC obtenida: {trama_gprmc}")
        datos = parsear_trama_gprmc(trama_gprmc)
        if datos:
            latitud, latitud_dir, longitud, longitud_dir, velocidad_kmh = datos
            coordenadas_utm = convertir_a_utm(latitud, latitud_dir, longitud, longitud_dir)
            print(f"Coordenadas finales en UTM: {coordenadas_utm}, Velocidad: {velocidad_kmh} Km/h")
            return coordenadas_utm[0], coordenadas_utm[1], velocidad_kmh
    print("No se pudo obtener una trama válida.")
    return None

if __name__ == "__main__":
    while True:
        print("Iniciando ciclo para obtener coordenadas...")
        coordenadas = obtener_coordenadas()
        time.sleep(1)
        if coordenadas:
            print(f"Coordenadas UTM: {coordenadas}")

import serial
import utm
import time


def leer_datos(puerto_serie="COM5", baudrate=4800, timeout=1):
    try:
        ser = serial.Serial(puerto_serie, baudrate, timeout=timeout,
                            bytesize=8, parity='N', stopbits=1, rtscts=False)
        while True:
            linea = ser.readline().decode('ascii', errors='ignore')
            if linea:
                if linea.startswith("$GPGGA"):
                    return linea.strip()
    except serial.SerialException as e:
        print(f"Error de puerto serial: {e}")
    except Exception as e:
        print(f"Ocurrió un error: {e}")


def parsear_trama_gga(trama):
    partes = trama.split(',')
    if partes[0] == "$GPGGA":
        latitud = partes[2]
        latitud_dir = partes[3]
        longitud = partes[4]
        longitud_dir = partes[5]
        return latitud, latitud_dir, longitud, longitud_dir
    return None


def convertir_a_decimal(grados_minutos, direccion):
    grados = float(grados_minutos[:2])
    minutos = float(grados_minutos[2:])
    decimal = grados + minutos / 60.0
    if direccion in ['S', 'W']:
        decimal = -decimal
    return decimal


def convertir_a_utm(latitud, latitud_dir, longitud, longitud_dir):
    latitud_decimal = convertir_a_decimal(latitud, latitud_dir)
    longitud_decimal = convertir_a_decimal(longitud, longitud_dir)
    coordenadas_utm = utm.from_latlon(latitud_decimal, longitud_decimal)
    return coordenadas_utm


def obtener_coordenadas():
    puerto = "COM5"  # Puerto donde está conectado el GPS
    trama_gga = leer_datos(puerto_serie=puerto)
    if trama_gga:
        latitud, latitud_dir, longitud, longitud_dir = parsear_trama_gga(trama_gga)
        coordenadas_utm = convertir_a_utm(latitud, latitud_dir, longitud, longitud_dir)
        return coordenadas_utm
    return None


if __name__ == "__main__":
    coordenadas = obtener_coordenadas()
    if coordenadas:
        print(f"Coordenadas UTM: {coordenadas}")
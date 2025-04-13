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
                    return linea.strip()
    except serial.SerialException as e:
        print(f"Error de puerto serial: {e}")
    except Exception as e:
        print(f"Ocurrió un error: {e}")

def parsear_trama_gga(trama):
    print(f"Parseando trama GGA: {trama}")
    partes = trama.split(',')
    if partes[0] == "$GPGGA":
        latitud = partes[2]
        latitud_dir = partes[3]
        longitud = partes[4]
        longitud_dir = partes[5]
        print(f"Latitud: {latitud} {latitud_dir}, Longitud: {longitud} {longitud_dir}")
        return latitud, latitud_dir, longitud, longitud_dir
    print("Trama no válida para GPGGA.")
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
    trama_gga = leer_datos(puerto_serie=puerto)
    if trama_gga:
        print(f"Trama GGA obtenida: {trama_gga}")
        latitud, latitud_dir, longitud, longitud_dir = parsear_trama_gga(trama_gga)
        coordenadas_utm = convertir_a_utm(latitud, latitud_dir, longitud, longitud_dir)
        print(f"Coordenadas finales en UTM: {coordenadas_utm}")
        return coordenadas_utm
    print("No se pudo obtener una trama válida.")
    return None

if __name__ == "__main__":
    while True:
        print("Iniciando ciclo para obtener coordenadas...")
        coordenadas = obtener_coordenadas()
        time.sleep(1)
        if coordenadas:
            print(f"Coordenadas UTM: {coordenadas}")
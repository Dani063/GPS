import serial


def leer_todo(puerto_serie="COM3", baudrate=4800, timeout=1):
    try:
        # Configurar el puerto serie
        ser = serial.Serial(puerto_serie, baudrate, timeout=timeout,
                            bytesize=8, parity='N', stopbits=1, rtscts=False)
        print(f"Conectado al puerto {puerto_serie}. Leyendo datos...")

        while True:
            # Leer una línea del GPS
            linea = ser.readline().decode('ascii', errors='ignore').strip()
            if linea:
                print(linea)  # Mostrar la línea completa en la consola
    except serial.SerialException as e:
        print(f"Error de puerto serial: {e}")
    except Exception as e:
        print(f"Ocurrió un error: {e}")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("Puerto serie cerrado.")


if __name__ == "__main__":
    leer_todo()
import os
import csv
import serial
import pynmea2
import utm
import threading
import logging
import matplotlib.pyplot as plt

def inicializar_csv(ruta_csv):
    if not os.path.exists(ruta_csv):
        with open(ruta_csv, 'w', newline='', encoding='utf-8') as f:
            csv.writer(f).writerow(['UTM_Norte', 'UTM_Este', 'Velocidad_Maxima'])
        print(f"Archivo creado: {ruta_csv}")
    else:
        print(f"Archivo existente: {ruta_csv}")

def leer_pulsar_enter(stop_event):
    input("Pulsa Enter para detener captura...\n")
    stop_event.set()



def capturar_y_escribir(conexion, ruta_csv):
    stop_event = threading.Event()
    threading.Thread(target=leer_pulsar_enter, args=(stop_event,), daemon=True).start()
    with open(ruta_csv, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        print("Comenzando captura. Pulsa Enter para detener.")
        while not stop_event.is_set():
            linea = conexion.readline().decode('ascii', errors='ignore')
            if linea.startswith('$GPRMC'):
                try:
                    msg = pynmea2.parse(linea)
                    if msg.status == 'A':
                        lat, lon = msg.latitude, msg.longitude
                        vel_kn = float(msg.spd_over_grnd or 0.0)
                        vel_kmh = vel_kn * 1.852
                        e, n = utm.from_latlon(lat, lon)[0:2]
                        writer.writerow([f"{n:.3f}", f"{e:.4f}", f"{vel_kmh:.2f}"])
                        print(f"Escrito -> Norte: {n:.3f}, Este: {e:.4f}, Vel: {vel_kmh:.2f} Km/h")
                except pynmea2.ParseError:
                    logging.warning("Línea NMEA no válida")
    print("Captura detenida por el usuario.")
    conexion.close()

def graficar(ruta_csv):
    xs, ys, vs = [], [], []
    with open(ruta_csv, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ys.append(float(row['UTM_Norte']))
            xs.append(float(row['UTM_Este']))
            vs.append(float(row['Velocidad_Maxima']))
    vel5 = [min(30, 5 * round(v/5)) for v in vs]
    categorias = sorted(set(vel5))
    marcadores = ['o','s','^','D','v','*','X'][:len(categorias)]
    plt.figure(figsize=(8,6))
    for v, m in zip(categorias, marcadores):
        ix = [i for i, val in enumerate(vel5) if val==v]
        plt.scatter([xs[i] for i in ix], [ys[i] for i in ix], label=f"{v} Km/h", marker=m)
    plt.xlabel('UTM Este')
    plt.ylabel('UTM Norte')
    plt.title('Circuito GPS')
    plt.grid(True)
    plt.legend(title='Velocidad')
    plt.tight_layout()
    plt.show()

def main():
    logging.basicConfig(level=logging.INFO)
    base = os.path.dirname(__file__)
    ruta_csv = os.path.join(base, '..', 'Recursos', 'mapa_electronico.csv')
    inicializar_csv(ruta_csv)
    conexion = serial.Serial('COM3', 4800, timeout=1)
    capturar_y_escribir(conexion, ruta_csv)
    graficar(ruta_csv)

if __name__ == '__main__':
    main()

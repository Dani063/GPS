# -*- coding: utf-8 -*-

import cv2
import os
import numpy as np
import utm
import logging
import time
from leer_datos import obtener_coordenadas
from threading import Thread

def cargar_mapa(ruta_mapa):
    try:
        mapa = np.genfromtxt(ruta_mapa, delimiter=',', dtype=None, encoding=None, names=True)
        if mapa.size == 0:
            logging.error("El mapa electronico esta vacio.")
            return None
        logging.info(f"Mapa cargado exitosamente desde {ruta_mapa}.")
        return mapa
    except Exception as e:
        logging.error(f"Error al cargar el mapa: {e}")
        return None

def obtener_velocidad_maxima(utm_norte, utm_este, mapa):
    try:
        distancias = np.sqrt((mapa['UTM_Norte'] - utm_norte)**2 + (mapa['UTM_Este'] - utm_este)**2)
        indice = np.argmin(distancias)
        velocidad_max = mapa['Velocidad_Maxima'][indice]
        return velocidad_max
    except Exception as e:
        logging.error(f"Error al obtener la velocidad maxima: {e}")
        return None

def mostrar_alerta(velocidad, velocidad_max):
    verde_limite = velocidad_max - 0.1 * velocidad_max
    amarillo_limite_inferior = velocidad_max - 0.1 * velocidad_max
    amarillo_limite_superior = velocidad_max + 0.1 * velocidad_max

    if velocidad < verde_limite:
        color = (0, 255, 0)  # Verde
        texto = f"Velocidad: {velocidad:.2f} Km/h"
    elif amarillo_limite_inferior <= velocidad <= amarillo_limite_superior:
        color = (0, 255, 255)  # Amarillo
        texto = f"Velocidad: {velocidad:.2f} Km/h"
    else:
        color = (0, 0, 255)  # Rojo
        texto = f"Velocidad: {velocidad:.2f} Km/h"
    return color, texto

def dibujar_interfaz(velocidad, color, texto_alerta, pantalla):
    pantalla[:] = (30, 30, 30)  # fondo oscuro
    cv2.rectangle(pantalla, (20, 20), (380, 180), (50, 50, 50), -1)  # panel principal
    cv2.rectangle(pantalla, (20, 20), (380, 180), (200, 200, 200), 2)  # borde
    fuente = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(pantalla, "Velocidad actual", (30, 60), fuente, 0.7, (255,255,255), 1, cv2.LINE_AA)
    cv2.putText(pantalla, f"{velocidad:.2f} Km/h", (50, 120), fuente, 2.0, color, 3, cv2.LINE_AA)
    cv2.imshow("Sistema de Aviso al Conductor", pantalla)

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    ruta_mapa = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Recursos", "mapa_electronico.csv")
    mapa = cargar_mapa(ruta_mapa)
    if mapa is None:
        return

    pantalla = np.zeros((200, 400, 3), dtype=np.uint8)
    cv2.namedWindow("Sistema de Aviso al Conductor", cv2.WINDOW_NORMAL)

    prev_pos = None
    prev_time = None

    while True:
        datos = obtener_coordenadas()
        if datos:
            utm_e, utm_n, _, _ = datos
            ahora = time.time()
            if prev_pos and prev_time:
                dx = utm_e - prev_pos[0]
                dy = utm_n - prev_pos[1]
                dt = ahora - prev_time
                velocidad = (np.hypot(dx, dy) / dt) * 3.6  # m/s a km/h
            else:
                velocidad = 0.0

            prev_pos = (utm_e, utm_n)
            prev_time = ahora

            vel_max = obtener_velocidad_maxima(utm_n, utm_e, mapa)
            if vel_max is not None:
                color, texto = mostrar_alerta(velocidad, vel_max)
                dibujar_interfaz(velocidad, color, texto, pantalla)
                logging.info(f"Vel: {velocidad:.2f} Km/h, Límite: {vel_max:.2f} Km/h")
            else:
                logging.warning("No se pudo determinar velocidad máxima.")
        else:
            logging.warning("Coordenadas inválidas.")

        if cv2.waitKey(1000) & 0xFF == 27:
            break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
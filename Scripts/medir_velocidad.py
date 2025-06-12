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
    pantalla[:] = (0, 0, 0)

    cv2.rectangle(pantalla, (50, 50), (350, 150), color, -1)

    fuente = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(pantalla, texto_alerta, (60, 120), fuente, 0.8, (255, 255, 255), 2, cv2.LINE_AA)

    cv2.imshow("Sistema de Aviso al Conductor", pantalla)

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    ruta_mapa = os.path.join(project_dir, "Recursos", "mapa_electronico.csv")

    mapa_electronico = cargar_mapa(ruta_mapa)
    if mapa_electronico is None:
        logging.error("No se pudo cargar el mapa electrónico. Saliendo del programa.")
        return

    pantalla = np.zeros((200, 400, 3), dtype=np.uint8)
    cv2.namedWindow("Sistema de Aviso al Conductor", cv2.WINDOW_NORMAL)

    while True:
        datos = obtener_coordenadas()
        if datos:
            utm_norte, utm_este, velocidad = datos
            velocidad_max = obtener_velocidad_maxima(utm_norte, utm_este, mapa_electronico)
            if velocidad_max is not None:
                color_alerta, texto_alerta = mostrar_alerta(velocidad, velocidad_max)
                dibujar_interfaz(velocidad, color_alerta, texto_alerta, pantalla)
                logging.info(f"Velocidad actual: {velocidad} Km/h, Velocidad máxima: {velocidad_max} Km/h")
            else:
                logging.warning("No se pudo determinar la velocidad máxima para la ubicación actual.")
        else:
            logging.warning("No se obtuvieron coordenadas válidas.")

        key = cv2.waitKey(1000) & 0xFF 
        if key == 27:  # Esc para salir
            break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

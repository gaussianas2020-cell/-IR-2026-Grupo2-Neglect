# -IR-2026-Grupo2-Neglect
# Evaluación de Neglect – Exploración de Faro

## Descripción
Este proyecto consiste en el desarrollo de un software para la evaluación de neglect espacial mediante una tarea de exploración visual tipo "faro".

La interfaz presenta una pantalla oscura en la cual el cursor actúa como una linterna. El usuario debe encontrar objetos ocultos distribuidos en la escena, con especial énfasis en el hemiespacio izquierdo.

El sistema permite registrar el desempeño del usuario y generar resultados exportables para su análisis.

---

## Objetivo
Desarrollar una herramienta digital simple, accesible y reproducible para la evaluación de neglect espacial, que permita:

- Evaluar tiempos de respuesta
- Detectar omisiones
- Analizar patrones de exploración
- Registrar resultados por sesión

---

## Funcionalidades principales

- Interfaz gráfica interactiva
- Simulación de iluminación tipo "linterna"
- Detección de objetos ocultos
- Registro de:
  - Tiempo de respuesta
  - Objetos encontrados
  - Errores
- Niveles de dificultad
- Identificación del paciente y número de sesión
- Exportación automática de resultados en formato `.json`

---

## Requisitos

Este proyecto fue desarrollado en **Python 3.x** y utiliza únicamente librerías estándar.

### Librerías utilizadas
- tkinter
- random
- math
- json
- os
- datetime
- time

No es necesario instalar dependencias adicionales.

---

## Instalación

1. Tener instalado Python 3.x  
2. Descargar o clonar el repositorio  
3. Ejecutar el archivo principal:

```bash
python exploracion_faro.py

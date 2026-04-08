
import tkinter as tk
import random
import math
import json
import os
from datetime import datetime
import time




# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================


WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 700


BACKGROUND_COLOR = "#050505"
TEXT_COLOR = "white"
OBJECT_COLOR = "#bfbfbf"
FOUND_OBJECT_COLOR = "#4dd970"
FLASHLIGHT_OUTLINE_COLOR = "#fcf3a7"


FLASHLIGHT_RADIUS = 120
OBJECT_RADIUS = 25


TOTAL_OBJECTS = 12
LEFT_SIDE_OBJECTS = 8
RIGHT_SIDE_OBJECTS = TOTAL_OBJECTS - LEFT_SIDE_OBJECTS


MIN_DISTANCE_BETWEEN_OBJECTS = 80
MAX_TEST_DURATION_SEC = 90


# Get the directory where the script is located to make it portable
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_FOLDER = os.path.join(SCRIPT_DIR, "results")
TRAJECTORY_SAMPLING_MS = 20


# Puntaje
MAX_ACCURACY_SCORE = 70
MAX_SPEED_SCORE = 30
ERROR_PENALTY = 2

# Tiempo de guardado automático
AUTOSAVE_INTERVAL_MS = 5000


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================


def ensure_results_folder():
    if not os.path.exists(RESULTS_FOLDER):
        os.makedirs(RESULTS_FOLDER)


def distance(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def sanitize_filename(text):
    safe = "".join(c for c in text if c.isalnum() or c in ("_", "-"))
    return safe.strip() if safe.strip() else "sin_nombre"


def save_results_to_json(data):

    ensure_results_folder()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    test_info = data.get("test_info", {})
    level = test_info.get("level", 1)
    patient_name = test_info.get("patient_name", "sin_nombre")
    session_number = test_info.get("session_number", "sin_sesion")

    safe_name = sanitize_filename(patient_name)
    
    # Crear subcarpeta por nombre y fecha (ej: Juan_Perez_03042026)
    date_str = datetime.now().strftime("%d%m%Y")
    subfolder_name = f"{safe_name}_{date_str}"
    subfolder_path = os.path.join(RESULTS_FOLDER, subfolder_name)
    
    if not os.path.exists(subfolder_path):
        os.makedirs(subfolder_path)

    filename = os.path.join(
        subfolder_path,
        f"exploracion_faro_{safe_name}_sesion{session_number}_nivel{level}_{timestamp}.json"
    )

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    return filename


def generate_non_overlapping_positions():
    positions = []

    def valid_position(new_pos):
        for pos in positions:
            if distance(pos, new_pos) < MIN_DISTANCE_BETWEEN_OBJECTS:
                return False
        return True

    left_count = 0
    attempts = 0
    while left_count < LEFT_SIDE_OBJECTS and attempts < 5000:
        x = random.randint(60, WINDOW_WIDTH // 2 - 80)
        y = random.randint(100, WINDOW_HEIGHT - 80)
        candidate = (x, y)
        if valid_position(candidate):
            positions.append(candidate)
            left_count += 1
        attempts += 1

    right_count = 0
    attempts = 0
    while right_count < RIGHT_SIDE_OBJECTS and attempts < 5000:
        x = random.randint(WINDOW_WIDTH // 2 + 80, WINDOW_WIDTH - 60)
        y = random.randint(100, WINDOW_HEIGHT - 80)
        candidate = (x, y)
        if valid_position(candidate):
            positions.append(candidate)
            right_count += 1
        attempts += 1

    random.shuffle(positions)
    return positions


def calculate_level_score(objects_found, total_objects, total_time_ms, max_time_sec, error_count):
    accuracy_score = (objects_found / total_objects) * MAX_ACCURACY_SCORE

    time_ratio = min(total_time_ms / (max_time_sec * 1000), 1.0)
    speed_score = (1 - time_ratio) * MAX_SPEED_SCORE

    error_penalty = error_count * ERROR_PENALTY

    raw_score = accuracy_score + speed_score - error_penalty
    final_score = max(0, min(100, round(raw_score, 2)))

    return {
        "accuracy_score": round(accuracy_score, 2),
        "speed_score": round(speed_score, 2),
        "error_penalty": round(error_penalty, 2),
        "level_score": final_score
    }


#  Función para generar una ruta fija para un nivel dentro de una sesión. 
#  Si el archivo ya existe, se sobreescribe con el ultimo autoguardado
def get_level_file_path(patient_name, session_number, level):

    ensure_results_folder()
    safe_name = sanitize_filename(patient_name)
    
    # Crear subcarpeta por nombre y fecha (ej: Juan_Perez_03042026)
    date_str = datetime.now().strftime("%d%m%Y")
    subfolder_name = f"{safe_name}_{date_str}"
    subfolder_path = os.path.join(RESULTS_FOLDER, subfolder_name)
    
    if not os.path.exists(subfolder_path):
        os.makedirs(subfolder_path)

    return os.path.join(
        subfolder_path,
        f"exploracion_faro_{safe_name}_sesion{session_number}_nivel{level}.json"
    )

#  Guarda los resultados en una ruta fija.
def save_results_to_json_path(data, filepath):

    ensure_results_folder()

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    return filepath

# ============================================================
# CLASE DEL OBJETO OCULTO
# ============================================================


class HiddenObject:
    def __init__(self, obj_id, position):
        self.id = obj_id
        self.x, self.y = position
        self.radius = OBJECT_RADIUS
        self.found = False
        self.found_time_ms = None
        self.click_position = None
        self.side = "left" if self.x < WINDOW_WIDTH / 2 else "right"


    def is_clicked(self, mouse_pos):
        return distance((self.x, self.y), mouse_pos) <= self.radius




# ============================================================
# APLICACIÓN PRINCIPAL
# ============================================================


class ExploracionFaroApp:
    def __init__(self, root):
        # self.root = root
        # self.root.title("Exploración de Faro - Neglect")
        # self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        # self.root.configure(bg=BACKGROUND_COLOR)
        # self.root.resizable(False, False)

        self.root = root
        self.root.title("Exploración de Faro - Neglect")

        # Activa pantalla completa
        self.root.attributes("-fullscreen", True)

        # Obtiene automáticamente el tamaño real de la pantalla
        self.root.update_idletasks()
        global WINDOW_WIDTH, WINDOW_HEIGHT
        WINDOW_WIDTH = self.root.winfo_screenwidth()
        WINDOW_HEIGHT = self.root.winfo_screenheight()

        self.root.configure(bg=BACKGROUND_COLOR)
        self.root.resizable(False, False)

        self.mouse_x = WINDOW_WIDTH // 2
        self.mouse_y = WINDOW_HEIGHT // 2


        self.level = 1
        self.bg_color = BACKGROUND_COLOR
        self.obj_color = OBJECT_COLOR
        self.found_color = FOUND_OBJECT_COLOR
        self.flashlight_radius = FLASHLIGHT_RADIUS


        self.test_running = False
        self.test_finished = False
        self.test_start_time = None
        self.end_reason = None

        self.completed_levels = []
        self.waiting_level_selection = False


        self.objects = []
        self.cursor_trajectory = []
        self.click_events = []
        self.error_count = 0
        self.last_error_timestamp = None
        self.json_path = None
        self.last_level_score_data = None


        # Datos del paciente
        self.patient_name = ""
        self.session_number = ""
        self.active_field = "name"
        self.input_completed = False

        # Guardado automático y por cierre
        self.last_result_data = None
        self.autosave_path = None
        self.is_closing = False

        self.current_level_file_path = None

        self.canvas = tk.Canvas(
            self.root,
            width=WINDOW_WIDTH,
            height=WINDOW_HEIGHT,
            bg=BACKGROUND_COLOR,
            highlightthickness=0
        )
        self.canvas.pack()


        self.root.bind("<Motion>", self.on_mouse_move)
        self.root.bind("<Button-1>", self.on_left_click)
        self.root.bind("<Escape>", self.on_escape)
        self.root.bind("<space>", self.on_space)


        self.root.bind("<Key>", self.on_key_press)
        self.root.bind("<Tab>", self.on_tab_press)
        self.root.bind("<Return>", self.on_enter_press)

        # Instrucciones de la actividad
        self.draw_instructions()


    # ========================================================
    # PANTALLA INICIAL
    # ========================================================

    def draw_instructions(self, error_message=""):
        self.canvas.delete("all")

        center_x = WINDOW_WIDTH // 2
        center_y = WINDOW_HEIGHT // 2

        # ========================================================
        # ENCABEZADO
        # ========================================================

        self.canvas.create_text(
            center_x, 65,
            text="Exploración de Faro",
            fill="white",
            font=("Arial", 40, "bold")
        )

        self.canvas.create_line(
            center_x - 200, 95,
            center_x + 200, 95,
            fill="#25ce79",
            width=5
        )

        # ========================================================
        # PRIMERA PANTALLA: ingreso de nombre y sesión
        # ========================================================

        if not self.input_completed:
            # Posiciones verticales adaptadas a pantalla completa
            subtitle_y = center_y - 230
            name_label_y = center_y - 140
            name_box_y = center_y - 105
            session_label_y = center_y + 20
            session_box_y = center_y + 50
            help_y = center_y + 120
            tab_y = center_y - 30

            # Tamaños de cajas proporcionales a la pantalla
            name_box_width = int(WINDOW_WIDTH * 0.38)
            name_box_height = 50

            session_box_width = int(WINDOW_WIDTH * 0.16)
            session_box_height = 50

            # Coordenadas de la caja de nombre
            name_x1 = center_x - name_box_width // 2
            name_x2 = center_x + name_box_width // 2
            name_y1 = name_box_y
            name_y2 = name_box_y + name_box_height

            # Coordenadas de la caja de sesión
            session_x1 = center_x - session_box_width // 2
            session_x2 = center_x + session_box_width // 2
            session_y1 = session_box_y
            session_y2 = session_box_y + session_box_height

            self.canvas.create_text(
                center_x, subtitle_y,
                text="Ingresar datos antes de comenzar",
                fill="#b4dcff",
                font=("Arial", 18, "bold")
            )

            self.canvas.create_text(
                center_x, name_label_y,
                text="Nombre del paciente:",
                fill=TEXT_COLOR,
                font=("Arial", 20)
            )

            name_color = "#00aaff" if self.active_field == "name" else "#cccccc"
            self.canvas.create_rectangle(
                name_x1, name_y1, name_x2, name_y2,
                outline=name_color, width=2
            )

            self.canvas.create_text(
                name_x1 + 20, name_y1 + name_box_height // 2,
                anchor="w",
                text=self.patient_name if self.patient_name else "Escriba aquí",
                fill=TEXT_COLOR if self.patient_name else "#777777",
                font=("Arial", 20)
            )

            self.canvas.create_text(
                center_x, session_label_y,
                text="Número de sesión:",
                fill=TEXT_COLOR,
                font=("Arial", 20)
            )

            session_color = "#00aaff" if self.active_field == "session" else "#cccccc"
            self.canvas.create_rectangle(
                session_x1, session_y1, session_x2, session_y2,
                outline=session_color, width=2
            )

            self.canvas.create_text(
                session_x1 + 20, session_y1 + session_box_height // 2,
                anchor="w",
                text=self.session_number if self.session_number else "Ej: 1",
                fill=TEXT_COLOR if self.session_number else "#777777",
                font=("Arial", 20)
            )

            self.canvas.create_text(
                center_x, tab_y,
                text="TAB para cambiar al siguiente campo",
                fill="#cccccc",
                font=("Arial", 16)
            )

            self.canvas.create_text(
                center_x, help_y + 35,
                text="Backspace para borrar",
                fill="#cccccc",
                font=("Arial", 16)
            )

            self.canvas.create_text(
                center_x, help_y + 100,
                text="Luego de completar los datos, presioná ENTER para continuar",
                fill="#00cc66",
                font=("Arial", 20, "bold")
            )

            self.canvas.create_text(
                center_x, help_y + 175,
                text="ESC para cerrar",
                fill="#ffaa00",
                font=("Arial", 17)
            )

        # ========================================================
        # SEGUNDA PANTALLA: saludo + instrucciones + selección nivel
        # ========================================================

        else:
            self.canvas.create_text(
                center_x, center_y - 200,
                text=f"¡Hola, {self.patient_name}!",
                fill="#53de98",
                font=("Arial", 28, "bold")
            )

            # Caja de instrucciones
            inst_box_width = int(WINDOW_WIDTH * 0.70)
            inst_box_height = 150
            inst_x1 = center_x - inst_box_width // 2
            inst_x2 = center_x + inst_box_width // 2
            inst_y1 = center_y - 135
            inst_y2 = inst_y1 + inst_box_height

            self.canvas.create_rectangle(
                inst_x1, inst_y1, inst_x2, inst_y2,
                outline="#2f5f85",
                width=5,
                fill="#26292e"
            )

            instrucciones = (
                "En la pantalla hay objetos ocultos\n"
                "Mové el cursor y seleccionalos con un click 🖱️"
            )

            self.canvas.create_text(
                center_x, inst_y1 + inst_box_height // 2,
                text=instrucciones,
                fill="#f2f2f2",
                font=("Arial", 24),
                justify="center",
                width=inst_box_width - 80
            )

            # Caja de niveles
            level_box_width = int(WINDOW_WIDTH * 0.5)
            level_box_height = 120
            level_x1 = center_x - level_box_width // 2
            level_x2 = center_x + level_box_width // 2
            level_y1 = center_y + 90
            level_y2 = level_y1 + level_box_height

            self.canvas.create_rectangle(
                level_x1, level_y1, level_x2, level_y2,
                outline="#00cc66",
                width=5,
                fill="#26292e"
            )

            self.canvas.create_text(
                center_x, level_y1 + 35,
                text="Elegí el nivel para comenzar",
                fill="#66ccff",
                font=("Arial", 20, "bold")
            )

            self.canvas.create_text(
                center_x, level_y1 + 80,
                text="1 = Fácil     2 = Medio     3 = Difícil",
                fill="#00cc66",
                font=("Arial", 26, "bold")
            )

        # ========================================================
        # MENSAJE DE ERROR O CONFIRMACIÓN
        # ========================================================

        if error_message:
            color = "red"
            if "correctamente" in error_message.lower():
                color = "#00cc66"

            self.canvas.create_text(
                center_x, WINDOW_HEIGHT - 25,
                text=error_message,
                fill=color,
                font=("Arial", 15, "bold")
            )

    # ========================================================
    # ENTRADA DE DATOS
    # ========================================================


    def on_tab_press(self, event=None):
        if self.test_running:
            return "break"


        if self.active_field == "name":
            self.active_field = "session"
        else:
            self.active_field = "name"


        self.draw_instructions()
        return "break"


    def on_enter_press(self, event=None):
        if self.test_running:
            return "break"


        if self.patient_name.strip() and self.session_number.strip():
            self.input_completed = True
            self.draw_instructions("Datos cargados correctamente")
        else:
            self.input_completed = False
            self.draw_instructions("Completá nombre y número de sesión antes de confirmar.")


        return "break"


    def on_key_press(self, event):
        if self.test_running:
            return

        if event.keysym in ["Tab", "Return", "Escape"]:
            return

        if event.keysym == "BackSpace":
            self.input_completed = False
            if self.active_field == "name":
                self.patient_name = self.patient_name[:-1]
            else:
                self.session_number = self.session_number[:-1]
            self.draw_instructions()
            return

        char = event.char
        if not char:
            return

        char = event.char
        if not char:
            return

        # -------------------------
        # 1. SI ESTOY ESCRIBIENDO DATOS
        # -------------------------

        if not self.input_completed:
            if self.active_field == "name":
                if char.isprintable():
                    self.patient_name += char

            elif self.active_field == "session":
                if char.isdigit():
                    self.session_number += char

            self.draw_instructions()
            return


        # -------------------------
        # 2. SI YA CONFIRMÉ DATOS → SELECCIÓN DE NIVEL
        # -------------------------

        if char in ["1", "2", "3"]:
            selected_level = int(char)

            if self.test_finished:
                if selected_level not in self.completed_levels:
                    self.start_test(level=selected_level)
                else:
                    self.draw_end_screen(
                        self.last_result_data,
                        "Nivel ya realizado. Elegí otro."
                    )
            else:
                self.start_test(level=selected_level)

            return
            # Si terminó un test, solo permitir niveles no jugados
            if self.test_finished:
                if selected_level not in self.completed_levels:
                    self.start_test(level=selected_level)
                else:
                    if self.last_result_data is not None:
                        self.draw_end_screen(
                            self.last_result_data,
                            "Ese nivel ya fue jugado en esta sesión."
                        )
                return

            # Inicio normal
            if self.input_completed:
                self.start_test(level=selected_level)
                return
    
            # Si está esperando selección de nivel, solo permitir niveles no jugados
            if self.waiting_level_selection:
                if selected_level not in self.completed_levels:
                    self.start_test(level=selected_level)
                else:
                    self.draw_level_selection_screen("Ese nivel ya fue jugado en esta sesión.")
                return

            # Inicio normal de la sesión: permitir cualquier nivel
            if selected_level not in self.completed_levels:
                self.start_test(level=selected_level)
            else:
                self.draw_instructions("Ese nivel ya fue jugado en esta sesión.")

            return


        # Si todavía no confirmó, se usan para escribir
        if self.active_field == "name":
            if char.isprintable() or char == " ":
                self.input_completed = False
                self.patient_name += char
        elif self.active_field == "session":
            if char.isdigit():
                self.input_completed = False
                self.session_number += char


        self.draw_instructions()

    # ========================================================
    # INICIO DEL TEST
    # ========================================================


    def start_test(self, event=None, level=1):
        if self.test_running:
            return

        if not self.input_completed:
            self.draw_instructions("Primero cargá nombre y número de sesión y presioná ENTER.")
            return

        if not self.patient_name.strip() or not self.session_number.strip():
            self.draw_instructions("Completá nombre y número de sesión antes de comenzar")
            return

        self.level = level

        # Ruta fija del archivo correspondiente a este nivel y sesión
        self.current_level_file_path = get_level_file_path(
        self.patient_name,
        self.session_number,
        self.level
        )

        if level == 1:
             self.bg_color = "#050505"
             self.obj_color = "#ffffff"
             self.found_color = "#50d070"
             self.flashlight_radius = 150
        elif level == 2:
             self.bg_color = "#151515"
             self.obj_color = "#808080"
             self.found_color = "#50d070"
             self.flashlight_radius = 100
        else:
             self.bg_color = "#2a2a2a"
             self.obj_color = "#454545"
             self.found_color = "#50d070"
             self.flashlight_radius = 90

        self.canvas.configure(bg=self.bg_color)

        positions = generate_non_overlapping_positions()
        self.objects = [HiddenObject(i + 1, pos) for i, pos in enumerate(positions)]

        self.cursor_trajectory = []
        self.click_events = []
        self.error_count = 0
        self.last_error_timestamp = None
        self.json_path = None
        self.last_level_score_data = None
        self.last_result_data = None

        self.test_running = True
        self.test_finished = False
        self.test_start_time = time.time()
        self.end_reason = None

        self.autosave_path = None
        self.root.after(AUTOSAVE_INTERVAL_MS, self.autosave_progress)

        self.update_test()
        self.record_trajectory()


    # ========================================================
    # EVENTOS
    # ========================================================


    def on_mouse_move(self, event):
        self.mouse_x = event.x
        self.mouse_y = event.y
        if self.test_running:
            self.draw_test_scene()


    def on_left_click(self, event):
        if not self.test_running:
            return

        elapsed_ms = self.get_elapsed_ms()
        click_x, click_y = event.x, event.y
        hit = False

        for obj in self.objects:
            if not obj.found and obj.is_clicked((click_x, click_y)):
                obj.found = True
                obj.found_time_ms = elapsed_ms
                obj.click_position = {"x": click_x, "y": click_y}
                hit = True

                self.click_events.append({
                    "time_ms": elapsed_ms,
                    "x": click_x,
                    "y": click_y,
                    "type": "hit",
                    "object_id": obj.id,
                    "object_side": obj.side
                })
                break

        if not hit:
            self.error_count += 1
            self.last_error_timestamp = time.time()

            self.click_events.append({
                "time_ms": elapsed_ms,
                "x": click_x,
                "y": click_y,
                "type": "error",
                "object_id": None,
                "object_side": None
            })

        self.draw_test_scene()

        if all(obj.found for obj in self.objects):
            self.finish_test("all_objects_found")

    def on_escape(self, event=None):

        if self.is_closing:
            return "break"

        self.is_closing = True

        try:
            if self.test_running:
                self.save_partial_results(reason="user_cancelled_during_test")
        except Exception as e:
            print(f"Error al salir con ESC: {e}")
        finally:
            self.root.destroy()

        return "break"


    def on_space(self, event=None):
    # Permitir espacio en el nombre antes de iniciar el test
        if not self.test_running and not self.test_finished:
            if self.active_field == "name":
                if not self.patient_name.endswith(" "):
                    self.patient_name += " "
                    self.input_completed = False
                    self.draw_instructions()
            return "break"


    # ========================================================
    # TIEMPO
    # ========================================================


    def get_elapsed_ms(self):
        if not self.test_start_time:
            return 0
        return int((time.time() - self.test_start_time) * 1000)


    def get_elapsed_sec(self):
        return self.get_elapsed_ms() / 1000.0


    # ========================================================
    # REGISTRO DE TRAYECTORIA
    # ========================================================


    def record_trajectory(self):
        if not self.test_running:
            return


        self.cursor_trajectory.append({
            "time_ms": self.get_elapsed_ms(),
            "x": self.mouse_x,
            "y": self.mouse_y
        })


        self.root.after(TRAJECTORY_SAMPLING_MS, self.record_trajectory)


    # ========================================================
    # ACTUALIZACIÓN GENERAL
    # ========================================================


    def update_test(self):
        if not self.test_running:
            return


        if self.get_elapsed_sec() >= MAX_TEST_DURATION_SEC:
            self.finish_test("time_limit")
            return


        self.draw_test_scene()
        self.root.after(16, self.update_test)


    # ========================================================
    # DIBUJO DEL TEST
    # ========================================================


    def draw_test_scene(self):
        self.canvas.delete("all")


        self.canvas.create_rectangle(
            0, 0, WINDOW_WIDTH, WINDOW_HEIGHT,
            fill=self.bg_color, outline=self.bg_color
        )


        for obj in self.objects:
            d = distance((obj.x, obj.y), (self.mouse_x, self.mouse_y))
            if d <= self.flashlight_radius:
                color = self.found_color if obj.found else self.obj_color
                self.canvas.create_oval(
                    obj.x - obj.radius, obj.y - obj.radius,
                    obj.x + obj.radius, obj.y + obj.radius,
                    fill=color, outline=color
                )


        self.canvas.create_oval(
            self.mouse_x - self.flashlight_radius, self.mouse_y - self.flashlight_radius,
            self.mouse_x + self.flashlight_radius, self.mouse_y + self.flashlight_radius,
            outline=FLASHLIGHT_OUTLINE_COLOR, width=2
        )


        self.canvas.create_oval(
            self.mouse_x - 4, self.mouse_y - 4,
            self.mouse_x + 4, self.mouse_y + 4,
            fill="#fff7c0", outline="#fff7c0"
        )


        if self.level == 1:
            left_unfound = any(not obj.found for obj in self.objects if obj.side == "left")
            right_unfound = any(not obj.found for obj in self.objects if obj.side == "right")
            
            offset = 30 # Valor fijo para mantener las flechas estáticas en su máxima extensión
            
            if left_unfound:
                # Línea indicadora izquierda
                self.canvas.create_line(5, 0, 5, WINDOW_HEIGHT, fill="red", width=10)
                for obj in self.objects:
                    if not obj.found and obj.side == "left":
                        # Línea punteada que atraviesa el renglón
                        self.canvas.create_line(0, obj.y, WINDOW_WIDTH // 2, obj.y, dash=(4, 4), fill="#333333", width=1)
                        # Flechas apuntando a la izquierda
                        start_x = WINDOW_WIDTH // 2 + 60 - offset
                        end_x = WINDOW_WIDTH // 2 - 60 - offset
                        self.canvas.create_line(
                            start_x, obj.y, end_x, obj.y,
                            arrow=tk.LAST, fill="#ffdd00", width=4
                        )

            if right_unfound:
                # Línea indicadora derecha
                self.canvas.create_line(WINDOW_WIDTH - 5, 0, WINDOW_WIDTH - 5, WINDOW_HEIGHT, fill="red", width=10)
                for obj in self.objects:
                    if not obj.found and obj.side == "right":
                        # Línea punteada que atraviesa el renglón
                        self.canvas.create_line(WINDOW_WIDTH // 2, obj.y, WINDOW_WIDTH, obj.y, dash=(4, 4), fill="#333333", width=1)
                        # Flechas apuntando a la derecha
                        start_x = WINDOW_WIDTH // 2 - 60 + offset
                        end_x = WINDOW_WIDTH // 2 + 60 + offset
                        self.canvas.create_line(
                            start_x, obj.y, end_x, obj.y,
                            arrow=tk.LAST, fill="#ffdd00", width=4
                        )


        if self.last_error_timestamp is not None:
            if time.time() - self.last_error_timestamp < 0.25:
                self.canvas.create_oval(
                    self.mouse_x - 20, self.mouse_y - 20,
                    self.mouse_x + 20, self.mouse_y + 20,
                    outline="red", width=3
                )


        found_count = sum(obj.found for obj in self.objects)
        time_left = max(0, int(MAX_TEST_DURATION_SEC - self.get_elapsed_sec()))
        
        found_count = sum(obj.found for obj in self.objects)
        time_left = max(0, int(MAX_TEST_DURATION_SEC - self.get_elapsed_sec()))

        panel_x = WINDOW_WIDTH - 20
        panel_y = 20

        # Color de la línea superior
        top_line_color = "#66ccff"
        if 0 < time_left <= 10 and int(time.time() * 4) % 2 == 0:
            top_line_color = "red"

        # Línea 1: datos principales
        line1 = (
            f"Encontrados: {found_count}/{TOTAL_OBJECTS}   "
            f"Tiempo: {time_left}s   "
            f"Errores: {self.error_count}"
        )

        self.canvas.create_text(
            panel_x, panel_y,
            anchor="ne",
            text=line1,
            fill=top_line_color,
            font=("Arial", 16, "bold"),
            justify="right"
        )

        # Línea 2: datos generales
        line2 = (
            f"Paciente: {self.patient_name}   "
            f"Sesión: {self.session_number}   "
            f"Nivel: {self.level}"
        )

        self.canvas.create_text(
            panel_x, panel_y + 26,
            anchor="ne",
            text=line2,
            fill="#cccccc",
            font=("Arial", 14),
            justify="right"
        )

    # ========================================================
    # Autoguardado
    # ========================================================

    def autosave_progress(self):
        if not self.test_running:
            return

        try:
            result_data = self.build_result_data(
                reason="autosave_in_progress",
                partial_result=True
            )
            self.autosave_path = save_results_to_json_path(
                result_data,
                self.current_level_file_path
            )
        except Exception as e:
            print(f"Error en autoguardado: {e}")

        self.root.after(AUTOSAVE_INTERVAL_MS, self.autosave_progress)

    # Guardado del cierre parcial

    def save_partial_results(self, reason="interrupted"):

        try:
            result_data = self.build_result_data(
                reason=reason,
                partial_result=True
            )

            self.last_result_data = result_data
            self.json_path = save_results_to_json_path(
                result_data,
                self.current_level_file_path
            )

            print(f"Resultado parcial guardado en: {self.json_path}")

        except Exception as e:
            print(f"Error al guardar resultados parciales: {e}")

    # ========================================================
    # FINALIZACIÓN
    # ========================================================


    def build_result_data(self, reason, partial_result=False):

        total_time_ms = self.get_elapsed_ms()
        total_found = sum(obj.found for obj in self.objects)
        left_found = sum(1 for obj in self.objects if obj.side == "left" and obj.found)
        right_found = sum(1 for obj in self.objects if obj.side == "right" and obj.found)

        score_data = calculate_level_score(
            objects_found=total_found,
            total_objects=TOTAL_OBJECTS,
            total_time_ms=total_time_ms,
            max_time_sec=MAX_TEST_DURATION_SEC,
            error_count=self.error_count
        )

        result_data = {
            "test_info": {
                "test_name": "Exploración de Faro",
                "test_type": "Neglect",
                "level": self.level,
                "patient_name": self.patient_name,
                "session_number": self.session_number,
                "date_time": datetime.now().isoformat(),
                "window_width": WINDOW_WIDTH,
                "window_height": WINDOW_HEIGHT,
                "max_duration_sec": MAX_TEST_DURATION_SEC,
                "flashlight_radius_px": self.flashlight_radius,
                "total_objects": TOTAL_OBJECTS,
                "left_side_objects": LEFT_SIDE_OBJECTS,
                "right_side_objects": RIGHT_SIDE_OBJECTS,
                "trajectory_sampling_ms": TRAJECTORY_SAMPLING_MS,
                "partial_result": partial_result
            },
            "performance": {
                "total_time_ms": total_time_ms,
                "objects_found": total_found,
                "objects_missed": TOTAL_OBJECTS - total_found,
                "left_found": left_found,
                "right_found": right_found,
                "error_count": self.error_count,
                "end_reason": reason
            },
            "score": {
                "accuracy_score": score_data["accuracy_score"],
                "speed_score": score_data["speed_score"],
                "error_penalty": score_data["error_penalty"],
                "level_score": score_data["level_score"],
                "score_scale": "0_to_100"
            },
            "objects": [
                {
                    "id": obj.id,
                    "x": obj.x,
                    "y": obj.y,
                    "side": obj.side,
                    "found": obj.found,
                    "found_time_ms": obj.found_time_ms,
                    "click_position": obj.click_position
                }
                for obj in self.objects
            ],
            "click_events": self.click_events,
            "cursor_trajectory": self.cursor_trajectory
        }

        return result_data
    

    # Finalización en forma

    def finish_test(self, reason):
        if not self.test_running:
            return

        self.test_running = False
        self.test_finished = True
        self.end_reason = reason

        if self.level not in self.completed_levels:
            self.completed_levels.append(self.level)

        total_time_ms = self.get_elapsed_ms()
        total_found = sum(obj.found for obj in self.objects)
        left_found = sum(1 for obj in self.objects if obj.side == "left" and obj.found)
        right_found = sum(1 for obj in self.objects if obj.side == "right" and obj.found)

        score_data = calculate_level_score(
            objects_found=total_found,
            total_objects=TOTAL_OBJECTS,
            total_time_ms=total_time_ms,
            max_time_sec=MAX_TEST_DURATION_SEC,
            error_count=self.error_count
        )
        self.last_level_score_data = score_data

        result_data = {
            "test_info": {
                "test_name": "Exploración de Faro",
                "test_type": "Neglect",
                "level": self.level,
                "patient_name": self.patient_name,
                "session_number": self.session_number,
                "date_time": datetime.now().isoformat(),
                "window_width": WINDOW_WIDTH,
                "window_height": WINDOW_HEIGHT,
                "max_duration_sec": MAX_TEST_DURATION_SEC,
                "flashlight_radius_px": self.flashlight_radius,
                "total_objects": TOTAL_OBJECTS,
                "left_side_objects": LEFT_SIDE_OBJECTS,
                "right_side_objects": RIGHT_SIDE_OBJECTS,
                "trajectory_sampling_ms": TRAJECTORY_SAMPLING_MS
            },
            "performance": {
                "total_time_ms": total_time_ms,
                "objects_found": total_found,
                "objects_missed": TOTAL_OBJECTS - total_found,
                "left_found": left_found,
                "right_found": right_found,
                "error_count": self.error_count,
                "end_reason": self.end_reason
            },
            "score": {
                "accuracy_score": score_data["accuracy_score"],
                "speed_score": score_data["speed_score"],
                "error_penalty": score_data["error_penalty"],
                "level_score": score_data["level_score"],
                "score_scale": "0_to_100"
            },
            "objects": [
                {
                    "id": obj.id,
                    "x": obj.x,
                    "y": obj.y,
                    "side": obj.side,
                    "found": obj.found,
                    "found_time_ms": obj.found_time_ms,
                    "click_position": obj.click_position
                }
                for obj in self.objects
            ],
            "click_events": self.click_events,
            "cursor_trajectory": self.cursor_trajectory
        }

        self.last_result_data = result_data
        self.json_path = save_results_to_json_path(
            result_data,
            self.current_level_file_path
        )
        self.draw_end_screen(result_data)


    # ========================================================
    # PANTALLA FINAL
    # ========================================================


    def draw_end_screen(self, result_data, error_message=""):
        self.canvas.delete("all")

        perf = result_data["performance"]
        score = result_data["score"]

        center_x = WINDOW_WIDTH // 2
        center_y = WINDOW_HEIGHT // 2

        file_name = os.path.basename(self.json_path) if self.json_path else "No disponible"

        # ========================================================
        # POSICIONES RELATIVAS A LA PANTALLA
        # ========================================================
        title_y = center_y - 310
        patient_y = center_y - 260
        level_y = center_y - 200
        score_y = center_y - 150
        score_label_y = center_y - 110

        metrics_start_y = center_y - 60
        metrics_step = 27

        # ========================================================
        # ENCABEZADO
        # ========================================================
        self.canvas.create_text(
            center_x, title_y,
            text="Test finalizado",
            fill=TEXT_COLOR,
            font=("Arial", 30, "bold")
        )


        self.canvas.create_text(
            center_x, patient_y,
            text=f"Paciente: {self.patient_name}   |   Número de sesión: {self.session_number}",
            fill="#eeeeee",
            font=("Arial", 20, "bold")
        )

        self.canvas.create_text(
            center_x, level_y,
            text=f"NIVEL {self.level}",
            fill="#66ccff",
            font=("Arial", 26, "bold")
        )

        # ========================================================
        # PUNTAJE PRINCIPAL
        # ========================================================
        self.canvas.create_text(
            center_x, score_y,
            text=f"{score['level_score']}/100",
            fill="#00ff88",
            font=("Arial", 40, "bold")
        )

        self.canvas.create_text(
            center_x, score_label_y,
            text="Puntaje del nivel",
            fill="#aaaaaa",
            font=("Arial", 20)
        )

        # ========================================================
        # MÉTRICAS CENTRADAS
        # ========================================================
        info_lines = [
            f"Aciertos: {perf['objects_found']} de {TOTAL_OBJECTS}",
            f"Lado izquierdo: {perf['left_found']}",
            f"Lado derecho: {perf['right_found']}",
            f"Errores: {perf['error_count']}",
            f"Puntaje por aciertos: {score['accuracy_score']}",
            f"Puntaje por velocidad: {score['speed_score']}",
            f"Penalización por errores: -{score['error_penalty']}",
            f"Archivo guardado: {file_name}"
        ]

        for i, line in enumerate(info_lines):
            font_size = 16
            color = "#cccccc"

            # La línea del archivo un poco más chica
            if i == len(info_lines) - 1:
                font_size = 15
                color = "#bfbfbf"

            self.canvas.create_text(
                center_x, metrics_start_y + i * metrics_step,
                text=line,
                fill=color,
                font=("Arial", font_size)
            )

        # ========================================================
        # BLOQUE FINAL: niveles disponibles / salida
        # ========================================================
        remaining_levels = [lvl for lvl in [1, 2, 3] if lvl not in self.completed_levels]

        levels_title_y = metrics_start_y + len(info_lines) * metrics_step + 25

        if remaining_levels:
            levels_numbers_y = levels_title_y + 45
            continue_y = levels_numbers_y + 40
            esc_y = continue_y + 50

            # --------------------------------------------------------
            # RECUADRO DEL BLOQUE DE NIVELES
            # --------------------------------------------------------
            box_padding_x = 260
            box_padding_y = 25

            box_x1 = center_x - box_padding_x
            box_x2 = center_x + box_padding_x

            box_y1 = levels_title_y - box_padding_y
            box_y2 = continue_y + box_padding_y

            self.canvas.create_rectangle(
                box_x1, box_y1,
                box_x2, box_y2,
                outline="#00cc66",
                width=5,
                fill="#26292e"
            )

            self.canvas.create_text(
                center_x, levels_title_y,
                text="Niveles disponibles:",
                fill="#66ccff",
                font=("Arial", 24, "bold")
            )

            texto_niveles = "     ".join([str(lvl) for lvl in remaining_levels])

            self.canvas.create_text(
                center_x, levels_numbers_y,
                text=texto_niveles,
                fill="#00cc66",
                font=("Arial", 36, "bold")
            )

            self.canvas.create_text(
                center_x, continue_y,
                text="Presioná el número para continuar",
                fill="#cccccc",
                font=("Arial", 20)
            )

        else:
            esc_y = levels_title_y + 60

            self.canvas.create_text(
                center_x, levels_title_y,
                text="Todos los niveles completados",
                fill="#00cc66",
                font=("Arial", 24, "bold")
            )

        self.canvas.create_text(
            center_x, esc_y,
            text="ESC para finalizar",
            fill="#ffaa00",
            font=("Arial", 20, "bold")
        )

        # ========================================================
        # MENSAJE DE ERROR
        # ========================================================
        if error_message:
            self.canvas.create_text(
                center_x, WINDOW_HEIGHT - 20,
                text=error_message,
                fill="red",
                font=("Arial", 16, "bold")
            )

# ============================================================
# PUNTO DE ENTRADA
# ============================================================


def main():
    root = tk.Tk()
    app = ExploracionFaroApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
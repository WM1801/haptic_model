try:
    import tkinter as tk
    from tkinter import ttk  # Для Scrollbar
except ImportError:
    raise ImportError("Требуется tkinter для запуска GUI")


class ProfileGraph:
    def __init__(self, canvas, x_min_view, x_max_view, y_center=250, y_scale=80):
        self.canvas = canvas
        self.x_min_view = x_min_view
        self.x_max_view = x_max_view
        self.y_center = y_center
        self.y_scale = y_scale

    def draw(self, sim: 'HapticSimulation', cursor_pos=None):
        c = self.canvas
        c.delete("all")

        # --- 1. Рисуем профиль U(x) ---
        steps = 300
        dx = (self.x_max_view - self.x_min_view) / steps
        xs = []
        us = []
        for i in range(steps + 1):
            x = self.x_min_view + i * dx
            u = sim.potential_profile.potential(x)
            xs.append(x)
            us.append(u)

        u_min, u_max = (min(us), max(us)) if us else (0, 1)
        if u_max == u_min:
            u_max = u_min + 1

        # Преобразуем U в пиксели по Y (инвертируем: большее U → выше на экране)
        points = []
        for i in range(len(xs)):
            x = xs[i]
            u = us[i]
            # y = y_center - scale * (u_normalized)
            y = self.y_center - self.y_scale * (u - u_min) / (u_max - u_min)
            points.extend([x, y])

        if len(points) >= 4:
            c.create_line(points, fill="lightgray", width=2)

        # Горизонтальная линия для ориентира (не обязательно)
        c.create_line(self.x_min_view, self.y_center, self.x_max_view, self.y_center,
                    fill="gray", dash=(2, 2))

        # --- 2. ОБЪЕКТ: рисуем НА ПОВЕРХНОСТИ U(x) ---
        obj_x = sim.state.x
        u_obj = sim.potential_profile.potential(obj_x)
        obj_y = self.y_center - self.y_scale * (u_obj - u_min) / (u_max - u_min)

        c.create_oval(obj_x - 6, obj_y - 6, obj_x + 6, obj_y + 6, fill="red")

        # --- 3. "Резинка" к курсору ---
        if cursor_pos is not None and sim.state.dragging:
            cx, cy = cursor_pos
            c.create_line(obj_x, obj_y, cx, cy,
                        fill="orange", width=2, dash=(4, 2))
            c.create_oval(cx - 4, cy - 4, cx + 4, cy + 4, outline="orange", width=1)

        # --- 4. Текст ---
        F = sim.get_current_force()
        mode = "Impedance" if sim.use_impedance_control else "Standard"
        control_mode = "Tgt" if sim.use_target_control else ("Spd" if sim.use_speed_control else "None")
        c.create_text(300, 20, text=f"Mode: {mode} | Ctrl: {control_mode} | x={obj_x:.1f} | F={F:+.1f}",
                    font=("Arial", 12))


# --- НОВОЕ: график силы ---
class ForceProfileGraph:
    def __init__(self, canvas, x_min_view, x_max_view, y_center=250, y_scale=80):
        self.canvas = canvas
        self.x_min_view = x_min_view
        self.x_max_view = x_max_view
        self.y_center = y_center
        self.y_scale = y_scale

    def draw(self, sim: 'HapticSimulation', cursor_pos=None):
        c = self.canvas
        c.delete("all")

        # --- 1. Рисуем профиль F(x) ---
        steps = 300
        dx = (self.x_max_view - self.x_min_view) / steps
        xs = []
        fs = []
        for i in range(steps + 1):
            x = self.x_min_view + i * dx
            # Проверим, есть ли у sim атрибут force_profile
            if hasattr(sim, 'force_profile') and sim.force_profile is not None:
                f = sim.force_profile.force(x)
            else:
                f = 0  # Если force_profile не определён, сила = 0
            xs.append(x)
            fs.append(f)

        f_min, f_max = (min(fs), max(fs)) if fs else (0, 1)
        if f_max == f_min:
            f_max = f_min + 1

        # Преобразуем F в пиксели по Y (инвертируем: большая сила вверх)
        points = []
        for i in range(len(xs)):
            x = xs[i]
            f = fs[i]
            # y = y_center - scale * (f_normalized)
            y = self.y_center - self.y_scale * (f - f_min) / (f_max - f_min)
            points.extend([x, y])

        if len(points) >= 4:
            c.create_line(points, fill="lightblue", width=2)

        # Горизонтальная линия для ориентира (F = 0)
        f_zero_y = self.y_center - self.y_scale * (0 - f_min) / (f_max - f_min)
        c.create_line(self.x_min_view, f_zero_y, self.x_max_view, f_zero_y,
                    fill="gray", dash=(2, 2))

        # --- 2. ОБЪЕКТ: рисуем на графике силы ---
        obj_x = sim.state.x
        # Найдем силу в точке obj_x
        if hasattr(sim, 'force_profile') and sim.force_profile is not None:
            f_obj = sim.force_profile.force(obj_x)
        else:
            f_obj = 0
        obj_y = self.y_center - self.y_scale * (f_obj - f_min) / (f_max - f_min)

        c.create_oval(obj_x - 6, obj_y - 6, obj_x + 6, obj_y + 6, fill="red")

        # --- 3. "Резинка" к курсору ---
        if cursor_pos is not None and sim.state.dragging:
            cx, cy = cursor_pos
            # Найдем силу в точке курсора (если нужно, можно не отображать)
            # Для простоты, линия будет от текущей позиции объекта к курсору
            # Предположим, что cy — это Y-координата курсора на том же графике
            # Но в текущей реализации курсор не привязан к оси Y силы. Оставим как есть.
            c.create_line(obj_x, obj_y, cx, self.y_center,  # Пример: линия к центру
                        fill="orange", width=2, dash=(4, 2))
            c.create_oval(cx - 4, self.y_center - 4, cx + 4, self.y_center + 4, outline="orange", width=1)

        # --- 4. Текст ---
        F_total = sim.force_profile.force(sim.state.x) if hasattr(sim, 'force_profile') and sim.force_profile is not None else 0
        c.create_text(300, 20, text=f"F_profile = {F_total:+.1f}",
                    font=("Arial", 12))
# ------------------------------------


class ForceHistoryGraph:
    def __init__(self, canvas, max_points=300):
        self.canvas = canvas
        self.max_points = max_points
        self.history = []

    def add(self, F):
        self.history.append(F)
        if len(self.history) > self.max_points:
            self.history.pop(0)

    def draw(self):
        c = self.canvas
        c.delete("all")
        if not self.history:
            return

        w = c.winfo_width()
        h = c.winfo_height()
        F_max_abs = max(max(abs(f) for f in self.history), 0.1)
        y0 = h / 2

        points = []
        N = len(self.history)
        for i, F in enumerate(self.history):
            x = i * (w / N)
            y = y0 - (F / F_max_abs) * (h / 2)
            points.extend([x, y])

        if len(points) >= 4:
            c.create_line(points, fill="blue", width=2)

        c.create_line(0, y0, w, y0, fill="black", dash=(2, 2))
        c.create_text(50, 20, text=f"F = {self.history[-1]:+.1f}", anchor="w", font=("Arial", 10))


class DualForceGraph:
    def __init__(self, canvas, max_points=300):
        self.canvas = canvas
        self.max_points = max_points
        self.history_haptic = []
        self.history_external = []

    def add(self, F_haptic, F_external):
        self.history_haptic.append(F_haptic)
        self.history_external.append(F_external)
        if len(self.history_haptic) > self.max_points:
            self.history_haptic.pop(0)
            self.history_external.pop(0)

    def draw(self):
        c = self.canvas
        c.delete("all")
        
        if not self.history_haptic:
            return

        w = c.winfo_width()
        h = c.winfo_height()
        
        # Общий масштаб по Y: используем общий диапазон обеих сил
        all_forces = self.history_haptic + self.history_external
        F_max_abs = max(max(abs(f) for f in all_forces), 0.1)
        y0 = h / 2

        # Рисуем гаптическую силу (синяя)
        points_haptic = []
        N = len(self.history_haptic)
        for i, F in enumerate(self.history_haptic):
            x = i * (w / N)
            y = y0 - (F / F_max_abs) * (h / 2)
            points_haptic.extend([x, y])
        if len(points_haptic) >= 4:
            c.create_line(points_haptic, fill="blue", width=2)

        # Рисуем внешнюю силу (красная)
        points_external = []
        for i, F in enumerate(self.history_external):
            x = i * (w / N)
            y = y0 - (F / F_max_abs) * (h / 2)
            points_external.extend([x, y])
        if len(points_external) >= 4:
            c.create_line(points_external, fill="red", width=2)

        # Линия F = 0
        c.create_line(0, y0, w, y0, fill="black", dash=(2, 2))

        # Легенда
        c.create_text(50, 20, text=f"F_haptic = {self.history_haptic[-1]:+.1f}", anchor="w", fill="blue", font=("Arial", 10))
        c.create_text(50, 40, text=f"F_mouse   = {self.history_external[-1]:+.1f}", anchor="w", fill="red", font=("Arial", 10))
        c.create_text(w - 50, h - 10, text="время →", anchor="e", font=("Arial", 9))


class VelocityGraph:
    def __init__(self, canvas, max_points=300):
        self.canvas = canvas
        self.max_points = max_points
        self.history = []

    def add(self, vx):
        self.history.append(vx)
        if len(self.history) > self.max_points:
            self.history.pop(0)

    def draw(self):
        c = self.canvas
        c.delete("all")
        if not self.history:
            return

        w = c.winfo_width()
        h = c.winfo_height()
        vx_max_abs = max(max(abs(v) for v in self.history), 0.1)
        y0 = h / 2

        points = []
        N = len(self.history)
        for i, vx in enumerate(self.history):
            x = i * (w / N)
            y = y0 - (vx / vx_max_abs) * (h / 2)
            points.extend([x, y])

        if len(points) >= 4:
            c.create_line(points, fill="green", width=2)

        c.create_line(0, y0, w, y0, fill="black", dash=(2, 2))
        c.create_text(50, 20, text=f"V = {self.history[-1]:+.2f}", anchor="w", font=("Arial", 10), fill="green")


# --- график для силы привода ---
class TargetForceGraph:
    def __init__(self, canvas, max_points=300):
        self.canvas = canvas
        self.max_points = max_points
        self.history = []

    def add(self, F_target):
        self.history.append(F_target)
        if len(self.history) > self.max_points:
            self.history.pop(0)

    def draw(self):
        c = self.canvas
        c.delete("all")
        if not self.history:
            return

        w = c.winfo_width()
        h = c.winfo_height()
        F_max_abs = max(max(abs(f) for f in self.history), 0.1)
        y0 = h / 2

        points = []
        N = len(self.history)
        for i, F in enumerate(self.history):
            x = i * (w / N)
            y = y0 - (F / F_max_abs) * (h / 2)
            points.extend([x, y])

        if len(points) >= 4:
            c.create_line(points, fill="purple", width=2)  # Цвет для силы привода

        c.create_line(0, y0, w, y0, fill="black", dash=(2, 2))
        c.create_text(50, 20, text=f"F_target = {self.history[-1]:+.1f}", anchor="w", fill="purple", font=("Arial", 10))
# ------------------------------------


# --- график для силы затухания ---
class DecelerationForceGraph:
    def __init__(self, canvas, max_points=300):
        self.canvas = canvas
        self.max_points = max_points
        self.history = []

    def add(self, F_decel):
        self.history.append(F_decel)
        if len(self.history) > self.max_points:
            self.history.pop(0)

    def draw(self):
        c = self.canvas
        c.delete("all")
        if not self.history:
            return

        w = c.winfo_width()
        h = c.winfo_height()
        F_max_abs = max(max(abs(f) for f in self.history), 0.1)
        y0 = h / 2

        points = []
        N = len(self.history)
        for i, F in enumerate(self.history):
            x = i * (w / N)
            y = y0 - (F / F_max_abs) * (h / 2)
            points.extend([x, y])

        if len(points) >= 4:
            c.create_line(points, fill="orange", width=2)  # Цвет для силы затухания

        c.create_line(0, y0, w, y0, fill="black", dash=(2, 2))
        c.create_text(50, 20, text=f"F_decel = {self.history[-1]:+.1f}", anchor="w", fill="orange", font=("Arial", 10))
# ------------------------------------


# --- НОВОЕ: график для статического трения ---
class StaticFrictionForceGraph:
    def __init__(self, canvas, max_points=300):
        self.canvas = canvas
        self.max_points = max_points
        self.history = []

    def add(self, F_static):
        self.history.append(F_static)
        if len(self.history) > self.max_points:
            self.history.pop(0)

    def draw(self):
        c = self.canvas
        c.delete("all")
        if not self.history:
            return

        w = c.winfo_width()
        h = c.winfo_height()
        F_max_abs = max(max(abs(f) for f in self.history), 0.1)
        y0 = h / 2

        points = []
        N = len(self.history)
        for i, F in enumerate(self.history):
            x = i * (w / N)
            y = y0 - (F / F_max_abs) * (h / 2)
            points.extend([x, y])

        if len(points) >= 4:
            c.create_line(points, fill="brown", width=2)  # Цвет для статического трения

        c.create_line(0, y0, w, y0, fill="black", dash=(2, 2))
        c.create_text(50, 20, text=f"F_static = {self.history[-1]:+.1f}", anchor="w", fill="brown", font=("Arial", 10))
# ------------------------------------


# --- НОВОЕ: график для кинетического трения ---
class KineticFrictionForceGraph:
    def __init__(self, canvas, max_points=300):
        self.canvas = canvas
        self.max_points = max_points
        self.history = []

    def add(self, F_kinetic):
        self.history.append(F_kinetic)
        if len(self.history) > self.max_points:
            self.history.pop(0)

    def draw(self):
        c = self.canvas
        c.delete("all")
        if not self.history:
            return

        w = c.winfo_width()
        h = c.winfo_height()
        F_max_abs = max(max(abs(f) for f in self.history), 0.1)
        y0 = h / 2

        points = []
        N = len(self.history)
        for i, F in enumerate(self.history):
            x = i * (w / N)
            y = y0 - (F / F_max_abs) * (h / 2)
            points.extend([x, y])

        if len(points) >= 4:
            c.create_line(points, fill="blue", width=2)  # Цвет для кинетического трения

        c.create_line(0, y0, w, y0, fill="black", dash=(2, 2))
        c.create_text(50, 20, text=f"F_kinetic = {self.history[-1]:+.1f}", anchor="w", fill="blue", font=("Arial", 10))
# ------------------------------------


class HapticGUI:
    def __init__(self, sim: 'HapticSimulation'):
        self.sim = sim
        self.root = tk.Tk()
        self.root.title("Гаптическая симуляция — с 'резинкой'")

        # --- ОСНОВНОЕ ОКНО: разделение на левую (графики) и правую (управление) части ---
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Левая часть: графики
        self.graphs_frame = tk.Frame(main_frame)
        self.graphs_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Правая часть: панель управления
        self.control_frame = tk.Frame(main_frame, width=220, bg="#e0e0e0")
        self.control_frame.pack(side=tk.RIGHT, fill=tk.Y)
        self.control_frame.pack_propagate(False)  # Не изменять ширину

        # --- ПРОКРУТКА В ПАНЕЛИ УПРАВЛЕНИЯ ---
        canvas = tk.Canvas(self.control_frame, bg="#e0e0e0")
        scrollbar = ttk.Scrollbar(self.control_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas, bg="#e0e0e0")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        # --- УСТАНОВИТЬ ШИРИНУ ОКНА ВНУТРИ CANVAS ---
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", width=215)  # Указать ширину
        # ------------------------------------------

        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=(0, 2))
        scrollbar.pack(side="right", fill="y")
        # ------------------------------------

        self.cursor_pos = None  # (x, y) — только для отрисовки

        # --- ГРАФИКИ (левая часть) ---
        self.profile_canvas = tk.Canvas(self.graphs_frame, width=600, height=300, bg="white")
        self.profile_canvas.pack()
        self.profile_graph = ProfileGraph(
            self.profile_canvas,
            x_min_view=sim.x_min,
            x_max_view=sim.x_max
        )

        # --- НОВОЕ: график силы ---
        self.force_profile_canvas = tk.Canvas(self.graphs_frame, width=600, height=300, bg="white")
        self.force_profile_canvas.pack()
        self.force_profile_graph = ForceProfileGraph(
            self.force_profile_canvas,
            x_min_view=sim.x_min,
            x_max_view=sim.x_max
        )
        # ------------------------------------

        self.force_canvas = tk.Canvas(self.graphs_frame, width=600, height=150, bg="#f0f0f0")
        self.force_canvas.pack()
        self.force_graph = DualForceGraph(self.force_canvas)

        self.velocity_canvas = tk.Canvas(self.graphs_frame, width=600, height=150, bg="#f5f5f5")
        self.velocity_canvas.pack()
        self.velocity_graph = VelocityGraph(self.velocity_canvas)

        # --- график для силы привода ---
        self.target_force_canvas = tk.Canvas(self.graphs_frame, width=600, height=150, bg="#f9f9f9")
        self.target_force_canvas.pack()
        self.target_force_graph = TargetForceGraph(self.target_force_canvas)
        # ------------------------------------

        # --- график для силы затухания ---
        self.decel_force_canvas = tk.Canvas(self.graphs_frame, width=600, height=150, bg="#f9f9f9")
        self.decel_force_canvas.pack()
        self.decel_force_graph = DecelerationForceGraph(self.decel_force_canvas)
        # ------------------------------------

        # --- НОВОЕ: график для статического трения ---
        self.static_friction_canvas = tk.Canvas(self.graphs_frame, width=600, height=150, bg="#f9f9f9")
        self.static_friction_canvas.pack()
        self.static_friction_graph = StaticFrictionForceGraph(self.static_friction_canvas)
        # ------------------------------------

        # --- НОВОЕ: график для кинетического трения ---
        self.kinetic_friction_canvas = tk.Canvas(self.graphs_frame, width=600, height=150, bg="#f9f9f9")
        self.kinetic_friction_canvas.pack()
        self.kinetic_friction_graph = KineticFrictionForceGraph(self.kinetic_friction_canvas)
        # ------------------------------------

        # --- ЭЛЕМЕНТЫ УПРАВЛЕНИЯ (правая часть) ---
        # --- КНОПКИ ПЕРЕКЛЮЧЕНИЯ РЕЖИМОВ ---
        mode_frame = tk.Frame(self.scrollable_frame, bg="#e0e0e0")
        mode_frame.pack(pady=5, fill=tk.X)

        self.mode_btn = tk.Button(mode_frame, text="Переключить режим", command=self.toggle_mode)
        self.mode_btn.pack(padx=2)

        self.target_ctrl_btn = tk.Button(mode_frame, text="Target Ctrl", command=self.toggle_target_control)
        self.target_ctrl_btn.pack(padx=2)

        self.speed_ctrl_btn = tk.Button(mode_frame, text="Speed Ctrl", command=self.toggle_speed_control)
        self.speed_ctrl_btn.pack(padx=2)
        # ------------------------------------

        # --- ЭЛЕМЕНТЫ УПРАВЛЕНИЯ ДЛЯ ПОЗИЦИОННОГО УПРАВЛЕНИЯ ---
        control_frame = tk.Frame(self.scrollable_frame, bg="#e0e0e0")
        control_frame.pack(pady=5, fill=tk.X)

        tk.Label(control_frame, text="Цель (пружина):", bg="#e0e0e0").pack(anchor=tk.W)
        self.target_entry = tk.Entry(control_frame, width=10)
        self.target_entry.pack()
        self.target_entry.insert(0, "0.0")

        self.set_target_btn = tk.Button(control_frame, text="Уст. позицию", command=self.set_target_position)
        self.set_target_btn.pack(pady=2)
        # -----------------------------------------------------------------

        tk.Label(control_frame, text="Damping (tgt):", bg="#e0e0e0").pack(anchor=tk.W)
        self.damping_entry = tk.Entry(control_frame, width=10)
        self.damping_entry.pack()
        self.damping_entry.insert(0, str(self.sim.target_damping))

        self.set_damping_btn = tk.Button(control_frame, text="Уст. damping", command=self.set_damping)
        self.set_damping_btn.pack(pady=2)
        # -----------------------------------------------------------------

        # --- ЭЛЕМЕНТЫ УПРАВЛЕНИЯ ДЛЯ СКОРОСТНОГО УПРАВЛЕНИЯ ---
        speed_control_frame = tk.Frame(self.scrollable_frame, bg="#e0e0e0")
        speed_control_frame.pack(pady=5, fill=tk.X)

        tk.Label(speed_control_frame, text="Цель (скоростное):", bg="#e0e0e0").pack(anchor=tk.W)
        self.target_speed_entry = tk.Entry(speed_control_frame, width=10)
        self.target_speed_entry.pack()
        self.target_speed_entry.insert(0, "0.0")

        tk.Label(speed_control_frame, text="Max Speed:", bg="#e0e0e0").pack(anchor=tk.W)
        self.max_speed_entry = tk.Entry(speed_control_frame, width=10)
        self.max_speed_entry.pack()
        self.max_speed_entry.insert(0, "10.0")

        tk.Label(speed_control_frame, text="Zone Width:", bg="#e0e0e0").pack(anchor=tk.W)
        self.zone_width_entry = tk.Entry(speed_control_frame, width=10)
        self.zone_width_entry.pack()
        self.zone_width_entry.insert(0, "50.0")

        self.set_speed_target_btn = tk.Button(speed_control_frame, text="Уст. скорость", command=self.set_speed_target_position)
        self.set_speed_target_btn.pack(pady=2)
        # -----------------------------------------------------------------

        # --- ЭЛЕМЕНТЫ УПРАВЛЕНИЯ ДЛЯ ТРЕНИЯ ---
        friction_frame = tk.Frame(self.scrollable_frame, bg="#e0e0e0")
        friction_frame.pack(pady=5, fill=tk.X)

        tk.Label(friction_frame, text="Static Friction:", bg="#e0e0e0").pack(anchor=tk.W)
        self.static_friction_entry = tk.Entry(friction_frame, width=10)
        self.static_friction_entry.pack()
        self.static_friction_entry.insert(0, str(self.sim.static_friction_force))

        tk.Label(friction_frame, text="Kinetic Friction:", bg="#e0e0e0").pack(anchor=tk.W)
        self.kinetic_friction_entry = tk.Entry(friction_frame, width=10)
        self.kinetic_friction_entry.pack()
        self.kinetic_friction_entry.insert(0, str(self.sim.kinetic_friction_force))

        self.set_friction_btn = tk.Button(friction_frame, text="Уст. трение", command=self.set_friction)
        self.set_friction_btn.pack(pady=2)
        # -----------------------------------------------------------------

        # --- ЭЛЕМЕНТЫ УПРАВЛЕНИЯ ДЛЯ ВЯЗКОСТИ ---
        damping_frame = tk.Frame(self.scrollable_frame, bg="#e0e0e0")
        damping_frame.pack(pady=5, fill=tk.X)

        tk.Label(damping_frame, text="Damping (std):", bg="#e0e0e0").pack(anchor=tk.W)
        self.damping_std_entry = tk.Entry(damping_frame, width=10)
        self.damping_std_entry.pack()
        self.damping_std_entry.insert(0, str(self.sim.damping))

        self.set_damping_std_btn = tk.Button(damping_frame, text="Уст. std", command=self.set_damping_std)
        self.set_damping_std_btn.pack(pady=2)

        tk.Label(damping_frame, text="Damping (imp):", bg="#e0e0e0").pack(anchor=tk.W)
        self.damping_imp_entry = tk.Entry(damping_frame, width=10)
        self.damping_imp_entry.pack()
        self.damping_imp_entry.insert(0, str(self.sim.impedance_damping))

        self.set_damping_imp_btn = tk.Button(damping_frame, text="Уст. imp", command=self.set_damping_imp)
        self.set_damping_imp_btn.pack(pady=2)
        # ------------------------------------

        # Привязка мыши
        self.profile_canvas.bind("<Button-1>", self.on_mouse_down)
        self.profile_canvas.bind("<B1-Motion>", self.on_mouse_move)
        self.profile_canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        # НОВОЕ: привязка мыши к графику силы
        self.force_profile_canvas.bind("<Button-1>", self.on_mouse_down)
        self.force_profile_canvas.bind("<B1-Motion>", self.on_mouse_move)
        self.force_profile_canvas.bind("<ButtonRelease-1>", self.on_mouse_up)

        self.animate()

    def toggle_mode(self):
        self.sim.toggle_impedance_control()
        mode = "Impedance" if self.sim.use_impedance_control else "Standard"
        print(f"Режим изменён на: {mode}")

    def toggle_target_control(self):
        self.sim.toggle_target_control()
        mode = "ON" if self.sim.use_target_control else "OFF"
        print(f"Target Control изменён на: {mode}")

    def toggle_speed_control(self):
        self.sim.toggle_speed_control()
        mode = "ON" if self.sim.use_speed_control else "OFF"
        print(f"Speed Control изменён на: {mode}")

    def set_target_position(self):
        try:
            target_x = float(self.target_entry.get())
            self.sim.set_target_position(target_x)
        except ValueError:
            print("Некорректное значение для целевой позиции")

    def set_damping(self):
        try:
            damping = float(self.damping_entry.get())
            self.sim.target_damping = damping
        except ValueError:
            print("Некорректное значение для демпфирования")

    def set_speed_target_position(self):
        try:
            x = float(self.target_speed_entry.get())
            max_speed = float(self.max_speed_entry.get())
            zone_width = float(self.zone_width_entry.get())
            self.sim.set_target_position_speed_control(x, max_speed, zone_width)
        except ValueError:
            print("Некорректное значение для скоростного управления")

    # --- методы для установки трения ---
    def set_friction(self):
        try:
            static_force = float(self.static_friction_entry.get())
            kinetic_force = float(self.kinetic_friction_entry.get())
            self.sim.set_friction_forces(static_force, kinetic_force)
        except ValueError:
            print("Некорректное значение для трения")
    # ------------------------------------

    # --- методы для установки вязкости ---
    def set_damping_std(self):
        try:
            damping = float(self.damping_std_entry.get())
            self.sim.damping = damping
        except ValueError:
            print("Некорректное значение для damping (std)")

    def set_damping_imp(self):
        try:
            damping = float(self.damping_imp_entry.get())
            self.sim.impedance_damping = damping
        except ValueError:
            print("Некорректное значение для damping (imp)")
    # ------------------------------------

    def on_mouse_down(self, event):
        # Выбираем активный график для захвата (можно уточнить через event.widget)
        # Для простоты, будем считать, что захват происходит на любом из них
        # Но лучше проверить, на каком canvas произошло событие
        # Однако, в текущей реализации, мы просто обновляем cursor_x и ставим dragging
        # Это может работать не очень точно, если объекты на разных графиках имеют разные координаты
        # Но если ось X одинакова, то всё ок.
        if abs(event.x - self.sim.state.x) <= 10:
            self.sim.state.dragging = True
            self.cursor_pos = (event.x, event.y)
            self.sim.cursor_x = float(event.x)

    def on_mouse_move(self, event):
        if self.sim.state.dragging:
            self.cursor_pos = (event.x, event.y)
            self.sim.cursor_x = float(event.x)  # ✅ правильно: cursor_x

    def on_mouse_up(self, event):
        self.sim.state.dragging = False
        self.cursor_pos = None
        self.sim.cursor_x = None  # ✅ правильно: cursor_x

    def animate(self):
        F_haptic, F_ext = self.sim.step()
        # --- получаем и добавляем силу привода ---
        F_target = self.sim._calculate_target_force() if self.sim.use_target_control else 0.0
        F_speed = self.sim._calculate_speed_control_force() if self.sim.use_speed_control else 0.0
        self.target_force_graph.add(F_target + F_speed)
        # -----------------------------------------------

        # --- ИЗМЕНЕНО: сила затухания теперь это сила трения, зависящая от скорости ---
        friction_force = self.sim._calculate_friction_force()
        self.decel_force_graph.add(friction_force)
        # -------------------------------------------------

        # --- НОВОЕ: вычисляем и добавляем статическое и кинетическое трение ---
        # Т.к. теперь в core логика трения уточнена, мы можем определить, какое трение "действует" в текущий момент.
        # Это не всегда F_static и F_kinetic отдельно. В `_calculate_friction_force` возвращается результирующая.
        # Для графиков трения будем отслеживать, движется ли объект.
        if abs(self.sim.state.vx) < self.sim.vx_threshold:
            # Объект "стоит". Статическое трение "поглощает" движущую силу.
            # В `_calculate_friction_force` возвращается 0, но для графиков мы можем отобразить потенциальную силу.
            # Т.к. в `_calculate_friction_force` мы не знаем F_move, то отображаем 0 для статического, если объект стоит.
            # Но мы можем отслеживать, если сила профиля + внешняя < static_friction, то считаем, что действует статическое.
            F_move = F_haptic + F_ext
            if abs(F_move) < self.sim.static_friction_force:
                F_static_display = -F_move  # Противодействует F_move
                F_kinetic_display = 0.0
            else:
                # Если F_move > static_friction, то объект "пытается" или уже движется.
                # В `_calculate_friction_force` будет кинетическое.
                # Но для графика мы можем отобразить кинетическое как +/- kinetic_friction_force.
                if self.sim.state.vx > 0:
                    F_kinetic_display = -self.sim.kinetic_friction_force
                elif self.sim.state.vx < 0:
                    F_kinetic_display = self.sim.kinetic_friction_force
                else: # vx == 0, но F_move > static
                    # Это переходное состояние. Пусть будет 0, если vx == 0.
                    F_kinetic_display = 0.0
                F_static_display = 0.0
        else: # Объект движется
            if self.sim.state.vx > 0:
                F_kinetic_display = -self.sim.kinetic_friction_force
            else: # vx < 0
                F_kinetic_display = self.sim.kinetic_friction_force
            F_static_display = 0.0

        self.static_friction_graph.add(F_static_display)
        self.kinetic_friction_graph.add(F_kinetic_display)
        # -------------------------------------------------

        self.velocity_graph.add(self.sim.state.vx)
        self.force_graph.add(F_haptic, F_ext)
        self.profile_graph.draw(self.sim, self.cursor_pos)
        # --- НОВОЕ: отрисовка профиля силы ---
        self.force_profile_graph.draw(self.sim, self.cursor_pos)
        # ------------------------------------
        self.force_graph.draw()
        self.velocity_graph.draw()
        self.target_force_graph.draw()
        self.decel_force_graph.draw()
        self.static_friction_graph.draw()  # <-- НОВОЕ: отрисовка
        self.kinetic_friction_graph.draw()  # <-- НОВОЕ: отрисовка
        self.root.after(int(self.sim.dt * 1000), self.animate)

    def run(self):
        self.root.mainloop()
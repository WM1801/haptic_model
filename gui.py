#gui.py
# -------------------------------------------------
# GUI: зависит от tkinter, НЕ зависит от логики
# -------------------------------------------------
try:
    import tkinter as tk
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
            u = sim.profile.potential(x)
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
        u_obj = sim.profile.potential(obj_x)
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
        c.create_text(300, 20, text=f"Профиль: U(x) | x={obj_x:.1f} | F={F:+.1f}",
                    font=("Arial", 12))


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


# --- НОВОЕ: график для силы привода ---
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


class HapticGUI:
    def __init__(self, sim: 'HapticSimulation'):
        self.sim = sim
        self.root = tk.Tk()
        self.root.title("Гаптическая симуляция — с 'резинкой'")
        self.cursor_pos = None  # (x, y) — только для отрисовки

        # Холсты
        self.profile_canvas = tk.Canvas(self.root, width=600, height=300, bg="white")
        self.profile_canvas.pack()
        self.profile_graph = ProfileGraph(
            self.profile_canvas,
            x_min_view=sim.x_min,
            x_max_view=sim.x_max
        )

        self.force_canvas = tk.Canvas(self.root, width=600, height=150, bg="#f0f0f0")
        self.force_canvas.pack()
        self.force_graph = DualForceGraph(self.force_canvas)

        self.velocity_canvas = tk.Canvas(self.root, width=600, height=150, bg="#f5f5f5")
        self.velocity_canvas.pack()
        self.velocity_graph = VelocityGraph(self.velocity_canvas)

        # --- НОВОЕ: график для силы привода ---
        self.target_force_canvas = tk.Canvas(self.root, width=600, height=150, bg="#f9f9f9")
        self.target_force_canvas.pack()
        self.target_force_graph = TargetForceGraph(self.target_force_canvas)
        # ------------------------------------

        # --- ЭЛЕМЕНТЫ УПРАВЛЕНИЯ ДЛЯ ПОЗИЦИОННОГО УПРАВЛЕНИЯ ---
        control_frame = tk.Frame(self.root)
        control_frame.pack()

        tk.Label(control_frame, text="Целевая позиция (пружина):").pack(side=tk.LEFT)
        self.target_entry = tk.Entry(control_frame, width=10)
        self.target_entry.pack(side=tk.LEFT)
        self.target_entry.insert(0, "0.0")  # Значение по умолчанию

        self.set_target_btn = tk.Button(control_frame, text="Установить позицию", command=self.set_target_position)
        self.set_target_btn.pack(side=tk.LEFT)

        tk.Label(control_frame, text="Damping:").pack(side=tk.LEFT)
        self.damping_entry = tk.Entry(control_frame, width=10)
        self.damping_entry.pack(side=tk.LEFT)
        self.damping_entry.insert(0, str(self.sim.target_damping))  # Текущее значение

        self.set_damping_btn = tk.Button(control_frame, text="Установить", command=self.set_damping)
        self.set_damping_btn.pack(side=tk.LEFT)
        # -----------------------------------------------------------------

        # --- НОВОЕ: элементы управления для скоростного управления ---
        speed_control_frame = tk.Frame(self.root)
        speed_control_frame.pack()

        tk.Label(speed_control_frame, text="Цель (скоростное):").pack(side=tk.LEFT)
        self.target_speed_entry = tk.Entry(speed_control_frame, width=10)
        self.target_speed_entry.pack(side=tk.LEFT)
        self.target_speed_entry.insert(0, "0.0")

        tk.Label(speed_control_frame, text="Max Speed:").pack(side=tk.LEFT)
        self.max_speed_entry = tk.Entry(speed_control_frame, width=10)
        self.max_speed_entry.pack(side=tk.LEFT)
        self.max_speed_entry.insert(0, "10.0")

        tk.Label(speed_control_frame, text="Zone Width:").pack(side=tk.LEFT)
        self.zone_width_entry = tk.Entry(speed_control_frame, width=10)
        self.zone_width_entry.pack(side=tk.LEFT)
        self.zone_width_entry.insert(0, "50.0")

        self.set_speed_target_btn = tk.Button(speed_control_frame, text="Уст. скорость", command=self.set_speed_target_position)
        self.set_speed_target_btn.pack(side=tk.LEFT)
        # -----------------------------------------------------------------

        # Привязка мыши
        self.profile_canvas.bind("<Button-1>", self.on_mouse_down)
        self.profile_canvas.bind("<B1-Motion>", self.on_mouse_move)
        self.profile_canvas.bind("<ButtonRelease-1>", self.on_mouse_up)

        self.animate()

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

    def on_mouse_down(self, event):
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
        # --- НОВОЕ: получаем и добавляем силу привода ---
        F_target = self.sim._calculate_target_force()
        F_speed = self.sim._calculate_speed_control_force()
        # Общая сила привода для отображения (можно выбрать одну или сумму)
        self.target_force_graph.add(F_target + F_speed)  # или только F_target, или F_speed
        # -----------------------------------------------
        self.velocity_graph.add(self.sim.state.vx)
        self.force_graph.add(F_haptic, F_ext)
        self.profile_graph.draw(self.sim, self.cursor_pos)
        self.force_graph.draw()
        self.velocity_graph.draw()
        self.target_force_graph.draw()  # <-- НОВОЕ: отрисовка
        self.root.after(int(self.sim.dt * 1000), self.animate)

    def run(self):
        self.root.mainloop()
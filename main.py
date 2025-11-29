import tkinter as tk
import numpy as np

# -------------------------------------------------
# Класс: виртуальный объект (рычаг / шарик)
# -------------------------------------------------
class HapticObject:
    def __init__(self, x=300.0, mass=50000.0, radius=8.0):
        self.x = float(x)
        self.vx = 0.0
        self.mass = mass
        self.radius = radius
        self.dragging = False

    def apply_force(self, F, dt, damping=2.0):
        if self.dragging:
            self.vx = 0.0
            return
        a = F / self.mass - damping * self.vx / self.mass
        self.vx += a * dt
        self.x += self.vx * dt

    def clamp(self, x_min, x_max):
        self.x = max(x_min, min(x_max, self.x))


# -------------------------------------------------
# Класс: мир с профилем поверхности
# -------------------------------------------------
class HapticWorld:
    def __init__(self, x0=300, width=100, slope_w=30, U0=500, is_pit=False):
        self.x0 = x0
        self.width = width
        self.slope_w = slope_w
        self.U0 = U0
        self.is_pit = is_pit

    def _smoothstep(self, a, b, x):
        if x <= a:
            return 0.0
        if x >= b:
            return 1.0
        t = (x - a) / (b - a)
        return t * t * (3 - 2 * t)

    def U(self, x):
        left_start = self.x0 - self.width / 2 - self.slope_w
        left_end = self.x0 - self.width / 2
        right_start = self.x0 + self.width / 2
        right_end = self.x0 + self.width / 2 + self.slope_w

        left_ramp = self._smoothstep(left_start, left_end, x)
        right_ramp = 1.0 - self._smoothstep(right_start, right_end, x)

        u_val = self.U0 * min(left_ramp, right_ramp)
        return -u_val if self.is_pit else u_val

    def force_at(self, x, dx=1.0):
        dU = (self.U(x + dx) - self.U(x - dx)) / (2 * dx)
        return -dU

    def toggle_profile(self):
        self.is_pit = not self.is_pit


# -------------------------------------------------
# Основное приложение
# -------------------------------------------------
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Гаптический мир с графиком силы")

        # Мир и объект
        self.world = HapticWorld(x0=300, width=100, slope_w=30, U0=500, is_pit=False)
        self.obj = HapticObject(x=300.0, mass=5.0, radius=8.0)

        # Параметры
        self.dt = 0.02
        self.x_min, self.x_max = 50, 550
        self.force_history = []
        self.max_history = 300  # сколько точек хранить
        self.current_force = 0.0

        # Основной холст (профиль)
        self.canvas = tk.Canvas(root, width=600, height=300, bg="white")
        self.canvas.pack()

        # Холст для графика силы
        self.force_canvas = tk.Canvas(root, width=600, height=150, bg="#f0f0f0")
        self.force_canvas.pack()

        # Кнопка
        self.btn = tk.Button(root, text="Переключить: Горка ↔ Ямка", command=self.toggle_profile)
        self.btn.pack()

        # Привязка мыши
        self.canvas.bind("<Button-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)

        self.animate()

    def toggle_profile(self):
        self.world.toggle_profile()

    def on_mouse_down(self, event):
        if abs(event.x - self.obj.x) <= self.obj.radius:
            self.obj.dragging = True

    def on_mouse_move(self, event):
        if self.obj.dragging:
            self.obj.x = max(self.x_min, min(self.x_max, event.x))

    def on_mouse_up(self, event):
        self.obj.dragging = False

    def animate(self):
        # Обновление физики
        self.current_force = self.world.force_at(self.obj.x)
        self.obj.apply_force(self.current_force, self.dt)
        self.obj.clamp(self.x_min, self.x_max)

        # Сохраняем силу в историю
        self.force_history.append(self.current_force)
        if len(self.force_history) > self.max_history:
            self.force_history.pop(0)

        # Перерисовка
        self.redraw()
        self.root.after(int(self.dt * 1000), self.animate)

    def redraw(self):
        # --- Основной холст: профиль U(x) ---
        c1 = self.canvas
        c1.delete("all")

        xs = np.linspace(self.x_min, self.x_max, 500)
        us = [self.world.U(x) for x in xs]
        u_min, u_max = min(us), max(us)
        if u_max == u_min:
            u_max = u_min + 1
        ys = [250 - 80 * (u - u_min) / (u_max - u_min) for u in us]  # чуть выше, чтобы было место

        points = []
        for x, y in zip(xs, ys):
            points.extend([int(x), int(y)])
        c1.create_line(points, fill="lightgray", width=2)
        c1.create_line(self.x_min, 250, self.x_max, 250, fill="gray", dash=(2, 2))
        c1.create_oval(self.obj.x - self.obj.radius, 242,
                       self.obj.x + self.obj.radius, 258, fill="red")

        typ = "Ямка" if self.world.is_pit else "Горка"
        c1.create_text(300, 20, text=f"Профиль: {typ} | x={self.obj.x:.1f} | F={self.current_force:+.1f}", font=("Arial", 12))

        # --- Холст силы ---
        c2 = self.force_canvas
        c2.delete("all")

        if not self.force_history:
            return

        # Найдём масштаб по Y
        F_min = min(self.force_history)
        F_max = max(self.force_history)
        F_range = max(1.0, F_max - F_min)
        F_center = (F_max + F_min) / 2

        # Рисуем кривую силы
        h = c2.winfo_height()
        w = c2.winfo_width()
        points = []
        for i, F in enumerate(self.force_history):
            x_screen = i * (w / len(self.force_history))
            # Отображаем относительно центра (чтобы F=0 была посередине, если возможно)
            y_screen = h / 2 - (F - 0.0) * (h / 2) / max(abs(F_min), abs(F_max), 1.0)
            points.extend([x_screen, y_screen])

        if len(points) >= 4:
            c2.create_line(points, fill="blue", width=2)

        # Линия F = 0
        c2.create_line(0, h / 2, w, h / 2, fill="black", dash=(2, 2))

        # Подписи
        c2.create_text(50, 20, text=f"Сила F = {self.current_force:+.1f}", anchor="w", font=("Arial", 10))
        c2.create_text(w - 50, h - 10, text="время →", anchor="e", font=("Arial", 9))


# -------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()

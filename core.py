# -------------------------------------------------
# ЧИСТАЯ МОДЕЛЬ: никаких импортов GUI, только логика
# -------------------------------------------------

class HapticObjectState:
    """Состояние объекта — только данные, без логики"""
    def __init__(self, x=0.0, vx=0.0):
        self.x = float(x)
        self.vx = float(vx)
        self.dragging = False  # флаг внешнего управления


class HapticProfile:
    """Профиль поверхности: ямка или горка в виде сглаженной трапеции"""
    def __init__(self, x0=0.0, width=10.0, slope_w=2.0, strength=10.0, is_pit=False):
        self.x0 = x0
        self.width = width
        self.slope_w = slope_w
        self.strength = strength
        self.is_pit = is_pit

    def _smoothstep(self, a, b, x):
        if x <= a:
            return 0.0
        if x >= b:
            return 1.0
        t = (x - a) / (b - a)
        return t * t * (3 - 2 * t)

    def potential(self, x):
        left_start = self.x0 - self.width / 2 - self.slope_w
        left_end = self.x0 - self.width / 2
        right_start = self.x0 + self.width / 2
        right_end = self.x0 + self.width / 2 + self.slope_w

        left_ramp = self._smoothstep(left_start, left_end, x)
        right_ramp = 1.0 - self._smoothstep(right_start, right_end, x)

        u_val = self.strength * min(left_ramp, right_ramp)
        return -u_val if self.is_pit else u_val

    def force(self, x, dx=1e-3):
        dU = (self.potential(x + dx) - self.potential(x - dx)) / (2 * dx)
        return -dU


class HapticSimulation:
    """Главный симулятор — чистая физика, без GUI"""
    def __init__(self, x_min=-100.0, x_max=100.0, mass=1.0, damping=0.5):
        self.x_min = x_min
        self.x_max = x_max
        self.mass = mass
        self.damping = damping
        self.dt = 0.01
        self.drag_spring_k = 20.0  # жёсткость "резинки"

        self.profile = HapticProfile()
        self.state = HapticObjectState(x=0.0)
        self.cursor_x = None  # только X — система 1D

    def set_profile(self, **kwargs):
        for k, v in kwargs.items():
            if hasattr(self.profile, k):
                setattr(self.profile, k, v)

    def toggle_profile_type(self):
        self.profile.is_pit = not self.profile.is_pit

    def step(self):
        """Один шаг симуляции — всегда работает"""
        external = 0.0
        if self.state.dragging and self.cursor_x is not None:
            external = self.drag_spring_k * (self.cursor_x - self.state.x)

        F_haptic = self.profile.force(self.state.x)
        F_total = F_haptic + external

        a = F_total / self.mass - self.damping * self.state.vx / self.mass
        self.state.vx += a * self.dt
        self.state.x += self.state.vx * self.dt

        # Ограничение диапазона
        if self.state.x < self.x_min:
            self.state.x = self.x_min
            self.state.vx = 0.0
        elif self.state.x > self.x_max:
            self.state.x = self.x_max
            self.state.vx = 0.0

        return F_haptic, external

    def get_current_force(self):
        return self.profile.force(self.state.x)


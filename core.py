#core.py
# -------------------------------------------------
# ЧИСТАЯ МОДЕЛЬ: никаких импортов GUI, только логика
# -------------------------------------------------
import math


class HapticObjectState:
    """Состояние объекта — только данные, без логики"""
    def __init__(self, x=0.0, vx=0.0):
        self.x = float(x)
        self.vx = float(vx)
        self.dragging = False  # флаг внешнего управления

# Сглаживание
def smoothstep(a, b, x):
    if x <= a:
        return 0.0
    if x >= b:
        return 1.0
    t = (x - a) / (b - a)
    return t * t * (3 - 2 * t)

#библиотека функций 
def constant(x, b=0.0):
    return b

def linear(x, a=0.0, b=0.0):
    return a * x + b

def trapezoid(x, x0=0.0, height=1.0, base_a=10.0, base_b=2.0, is_pit=False):
    """
    x0 - центр трапеции
    height - высота трапеции (или глубина, если is_pit = True)
    base_a - размер оснований (плоская часть) 
    base_b - длинна склонов (суммарно по 2)
    """
    half_a = base_a / 2
    half_b = base_b / 2
    start_slope = x0 - half_a - half_b
    end_slope = x0 + half_a + half_b
    
    if x < start_slope or x > end_slope:
        return 0.0

    # Правильное вычисление сглаженных склонов
    left_ramp = smoothstep(start_slope, x0 - half_a, x)
    right_ramp = 1.0 - smoothstep(x0 + half_a, end_slope, x)
    u_val = height * min(left_ramp, right_ramp)

    return -u_val if is_pit else u_val


def semicircle(x, x0=0.0, radius=5.0, is_pit=False):   
    """
    x0 - центр окружности
    radius - радиус
    """
    if abs(x - x0) > radius:
        return 0.0
    y = math.sqrt(radius ** 2 - (x - x0) ** 2)
    return -y if is_pit else y


def sine_wave_sum(x, components=None): 
    """
    components: список словарей с ключами: 'amplitude', 'frequency', 'phase'
    Пример: [{'amplitude': 1.0, 'frequency': 0.1, 'phase': 0}, ...]
    """
    if components is None:
        components = []
    # Используем только логику цикла, без дублирования
    total = 0.0
    for comp in components: 
        amp = comp.get('amplitude', 0.0)
        freq = comp.get('frequency', 0.0)
        phase = comp.get('phase', 0.0)
        total += amp * math.sin(freq * x + phase)
    return total  # Возвращаем накопленное значение


class PiecewiseProfile: 
    """
    Профиль, состоящий из комбинации базовых функций.
    Содержит список словарей: {'func': func, 'params': {...}}
    """
    def __init__(self, functions=None):
        self.functions = functions or []

    def add_function(self, func, **params):
        self.functions.append({'func': func, 'params': params})

    def potential(self, x):
        total = 0.0
        for f in self.functions:
            total += f['func'](x, **f['params'])
        return total

    def force(self, x, dx=1e-3):
        dU = (self.potential(x + dx) - self.potential(x - dx)) / (2 * dx)
        return -dU
    

class HapticSimulation:
    """Главный симулятор — чистая физика, без GUI"""
    def __init__(self, x_min=-100.0, x_max=100.0, mass=1.0, damping=0.1):
        self.x_min = x_min
        self.x_max = x_max
        self.mass = mass
        self.damping = damping
        self.dt = 0.01
        self.drag_spring_k = 0.1 # жёсткость "резинки"

        self.constant_force = 0.0  #сухое трение 

        self.profile = PiecewiseProfile()
        self.state = HapticObjectState(x=0.0)
        self.cursor_x = None  # только X — система 1D
        self.force_threshold = 1.001
        self.f_max = 150

    def set_profile(self, profile):
        #принимает объект PiecewiseProfile
        self.profile = profile

    def get_current_force(self):
        # Теперь не включает постоянную силу
        return self.profile.force(self.state.x)

    def set_constant_force(self, force):
        """Устанавливает силу сопротивления (например, трение)"""
        self.constant_force = abs(force)  # всегда положительная величина

    def step(self):
        """Один шаг симуляции — всегда работает"""
        external = 0.0
        if self.state.dragging and self.cursor_x is not None:
            # виртуальное усилие от мышь -> сила 
            raw_force = self.drag_spring_k * (self.cursor_x - self.state.x)
            
            #порог срабатывания (мертвая зона)
            if abs(raw_force) < self.force_threshold: 
                external = 0.0
            else: 
                #ограничение максимума 
                external = max(-self.f_max, min (self.f_max, raw_force))
        else: 
            external = 0.0

        F_haptic = self.profile.force(self.state.x)
        friction_force = 0.0
        if (abs(external) > self.constant_force):
            #Если внешняя сила преодолевает сопротивление, сила сопротивления направлена против
            friction_force = -self.constant_force * (1 if external > 0 else -1)
        else: 
            # Если внешней силы недостаточно, сила сопротивления полностью компенсирует её
            friction_force = -external

        # --- ИСПРАВЛЕНО: постоянная сила (трение) добавляется как friction_force ---
        F_total = F_haptic + external + friction_force

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

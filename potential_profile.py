import math

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
    Содержит список словарей: {'func': func, 'params': {...}, 'override': bool}
    Если override=True и функция активна (func != 0), то её значение заменяет собой сумму остальных.
    """
    def __init__(self, functions=None):
        self.functions = functions or []

    def add_function(self, func, override=False, **params):
        self.functions.append({'func': func, 'params': params, 'override': override})

    def potential(self, x):
        override_val = None
        total = 0.0
        for f in self.functions:
            val = f['func'](x, **f['params'])
            if f['override'] and val != 0:
                # Если функция с override и она активна (val != 0), возвращаем только её
                return val
            elif not f['override']:
                total += val

        # Если не было override-функций, возвращаем сумму
        return total

    def force(self, x, dx=1e-3):
        dU = (self.potential(x + dx) - self.potential(x - dx)) / (2 * dx)
        return -dU
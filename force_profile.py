class ForceProfile:
    """
    Профиль, состоящий из комбинации функций, возвращающих силу F(x).
    Содержит список словарей: {'func': func, 'params': {...}, 'override': bool}
    Если override=True и функция активна (func != 0), то её значение заменяет собой сумму остальных.
    """
    def __init__(self, functions=None):
        self.functions = functions or []

    def add_function(self, func, override=False, **params):
        self.functions.append({'func': func, 'params': params, 'override': override})

    def force(self, x):
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

def constant_force(x, magnitude=0.0):
    """Постоянная сила"""
    return magnitude

def linear_force(x, k=0.0, x_eq=0.0):
    """Линейная сила (например, пружина: F = -k * (x - x_eq))"""
    return -k * (x - x_eq)

def trapezoid_force(x, x0=0.0, max_force=1.0, base_a=10.0, base_b=2.0, is_negative=False):
    """
    Сила в форме трапеции.
    max_force - максимальная сила на склоне.
    base_a - длина плоской части (где F = 0)
    base_b - длина склонов (суммарно).
    """
    from potential_profile import smoothstep
    half_a = base_a / 2
    half_b = base_b / 2
    start_slope = x0 - half_a - half_b
    end_slope = x0 + half_a + half_b
    
    if x < start_slope or x > end_slope:
        return 0.0

    # Плавный переход на склонах (аналогично smoothstep)
    left_ramp = smoothstep(start_slope, x0 - half_a, x)
    right_ramp = 1.0 - smoothstep(x0 + half_a, end_slope, x)
    force_val = max_force * min(left_ramp, right_ramp)

    # Определяем, к какому краю ближе
    dist_to_left = abs(x - start_slope)
    dist_to_right = abs(x - end_slope)

    # Направление силы — к ближайшему краю
    if dist_to_left < dist_to_right:
        # Ближе к левому краю
        direction = -1  # Влево
    else:
        # Ближе к правому краю
        direction = 1   # Вправо

    result_force = force_val * direction

    # is_negative инвертирует направление силы
    if is_negative:
        result_force = -result_force

    return result_force
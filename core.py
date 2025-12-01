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
    

class HapticSimulation:
    """Главный симулятор — чистая физика, без GUI"""
    def __init__(self, x_min=-100.0, x_max=100.0, mass=1.0, damping=0.1):
        self.x_min = x_min
        self.x_max = x_max
        self.mass = mass
        self.damping = damping
        self.dt = 0.01
        self.drag_spring_k = 0.1 # жёсткость "резинки" для пользователя

        self.constant_force = 0.0  #сухое трение 

        self.profile = PiecewiseProfile()
        self.state = HapticObjectState(x=0.0)
        self.cursor_x = None  # только X — система 1D
        self.force_threshold = 1.001
        self.f_max = 150
        #---порог для скорости ---
        self.vx_threshold = 0.1

        # --- ПАРАМЕТРЫ ДЛЯ СИЛЫ ПРУЖИНЫ К ЦЕЛИ ---
        self.target_x = None
        self.target_spring_k = 1.0  # жёсткость пружины к целевой позиции
        self.target_damping = 0.5   # демпфирование для ограничения скорости
        self.target_max_force = 100.0  # максимальная сила привода
        # ----------------------------------------

        # --- НОВОЕ: параметры для управления по скорости ---
        self.target_speed_x = None
        self.target_max_speed = 10.0
        self.target_zone_width = 50.0
        # ----------------------------------------------

        # --- НОВОЕ: параметры Impedance Control ---
        self.use_impedance_control = False
        self.impedance_mass = 1.0
        self.impedance_damping = 0.1
        self.impedance_stiffness = 0.0  # жёсткость к x_desired (например, от привода)
        # ---------------------------------------

        # --- НОВОЕ: флаги для переключения режимов управления ---
        self.use_target_control = False
        self.use_speed_control = False
        # ---------------------------------------------------------

    def set_profile(self, profile):
        #принимает объект PiecewiseProfile
        self.profile = profile

    def get_current_force(self):
        # Теперь включает силу от профиля и силу трения
        F_profile = self.profile.force(self.state.x)
        F_friction = self._calculate_friction_force()
        return F_profile + F_friction

    def set_constant_force(self, force):
        """Устанавливает силу сопротивления (например, трение)"""
        self.constant_force = abs(force)  # всегда положительная величина

    # --- МЕТОД ДЛЯ ВКЛЮЧЕНИЯ/ВЫКЛЮЧЕНИЯ Impedance Control ---
    def toggle_impedance_control(self):
        self.use_impedance_control = not self.use_impedance_control

    # --- НОВОЕ: методы для включения/выключения режимов управления ---
    def toggle_target_control(self):
        self.use_target_control = not self.use_target_control

    def toggle_speed_control(self):
        self.use_speed_control = not self.use_speed_control
    # ---------------------------------------------------------

    # --- МЕТОД ДЛЯ УСТАНОВКИ ЦЕЛЕВОЙ ПОЗИЦИИ (ПРУЖИНА) ---
    def set_target_position(self, x):
        """Устанавливает целевую позицию для привода (пружина)"""
        self.target_x = x

    # --- НОВОЕ: метод для установки целевой позиции и параметров скорости ---
    def set_target_position_speed_control(self, x, max_speed=10.0, zone_width=50.0):
        """Устанавливает целевую позицию и параметры управления по скорости"""
        self.target_speed_x = x
        self.target_max_speed = max_speed
        self.target_zone_width = zone_width

    def _calculate_external_force(self):
        """Вычисляет внешнюю силу от пользователя (мышь/тачпад)"""
        external = 0.0
        if self.state.dragging and self.cursor_x is not None:
            raw_force = self.drag_spring_k * (self.cursor_x - self.state.x)
            if abs(raw_force) < self.force_threshold: 
                external = 0.0
            else: 
                external = max(-self.f_max, min (self.f_max, raw_force))
        return external

    # --- СИЛА, УПРАВЛЯЕМАЯ ПОЗИЦИОННО (ПРУЖИНА) ---
    def _calculate_target_force(self):
        """Вычисляет силу, стремящуюся переместить объект к target_x с ограничением скорости"""
        if self.target_x is None or not self.use_target_control:
            return 0.0

        # Пружина к целевой позиции
        spring_force = self.target_spring_k * (self.target_x - self.state.x)

        # Демпфирование для ограничения скорости (против текущей скорости)
        damping_force = -self.target_damping * self.state.vx

        raw_force = spring_force + damping_force

        # --- компенсация трения ---
        # Если raw_force направлена к цели и недостаточна, добавим "запас"
        direction_to_target = 1 if self.target_x > self.state.x else -1
        if abs(raw_force) < self.constant_force and raw_force * direction_to_target > 0:
            # raw_force направлена к цели, но слаба, увеличим её
            raw_force = direction_to_target * self.constant_force
        # -----------------------------------

        # Ограничиваем максимальную силу
        target_force = max(-self.target_max_force, min(self.target_max_force, raw_force))

        return target_force

    # --- НОВОЕ: сила, управляемая через желаемую скорость ---
    def _calculate_speed_control_force(self):
        """Вычисляет силу, стремящуюся к целевой скорости, основанной на расстоянии до цели"""
        if self.target_speed_x is None or not self.use_speed_control:
            return 0.0

        # Вычисляем расстояние до цели
        dist_to_target = self.target_speed_x - self.state.x

        # Если близко к цели, уменьшаем скорость
        if abs(dist_to_target) < self.target_zone_width:
            # Линейное уменьшение скорости от 0 (в цели) до max_speed (на краю зоны)
            desired_speed = (abs(dist_to_target) / self.target_zone_width) * self.target_max_speed
            # Направление скорости к цели
            desired_speed *= (1 if dist_to_target > 0 else -1)
        else:
            # Далеко от цели — едем с максимальной скоростью
            desired_speed = self.target_max_speed * (1 if dist_to_target > 0 else -1)

        # Разница между желаемой и текущей скоростью
        speed_error = desired_speed - self.state.vx

        # Преобразуем ошибку скорости в силу (PID-подобный контроллер, но только P)
        # Коэффициент можно настроить
        speed_force = speed_error * 5.0  # Коэффициент усиления

        # Ограничиваем силу
        speed_force = max(-self.target_max_force, min(self.target_max_force, speed_force))

        return speed_force

    # ---  сухое трение зависит от скорости и порога ---
    def _calculate_friction_force(self):
        """
        Возвращает силу сухого трения, противоположно направленную скорости.
        F_friction = -sign(vx) * constant_force, если |vx| >= vx_threshold.
        Иначе 0.
        """
        if abs(self.state.vx) < self.vx_threshold:
            return 0.0
        elif self.state.vx > 0:
            return -self.constant_force
        elif self.state.vx < 0:
            return self.constant_force
        else:
            return 0.0  # vx == 0

    # ---------------------------------------------------------

    def _calculate_acceleration(self, F_total):
        """Вычисляет ускорение из суммарной силы"""
        return F_total / self.mass - self.damping * self.state.vx / self.mass

    def _update_state(self, a):
        """Обновляет скорость и положение"""
        self.state.vx += a * self.dt
        self.state.x += self.state.vx * self.dt

    def _apply_velocity_threshold(self):
        """Применяет порог скорости для стабилизации"""
        if abs(self.state.vx) < self.vx_threshold:
            self.state.vx = 0.0

    def _apply_position_bounds(self):
        """Ограничивает положение в пределах x_min, x_max"""
        if self.state.x < self.x_min:
            self.state.x = self.x_min
            self.state.vx = 0.0
        elif self.state.x > self.x_max:
            self.state.x = self.x_max
            self.state.vx = 0.0

    # --- ИЗМЕНЕНО: Impedance Control ---
    def _impedance_step(self):
        x_desired = self.target_x if self.target_x is not None else self.state.x
        
        F_haptic = self.profile.force(self.state.x)  # <-- Только профиль
        F_external_user = self._calculate_external_force()

        # --- УСЛОВНОЕ ВКЛЮЧЕНИЕ УПРАВЛЕНИЯ ---
        F_target = self._calculate_target_force() if self.use_target_control else 0.0
        F_speed = self._calculate_speed_control_force() if self.use_speed_control else 0.0
        # -------------------------------------

        friction_force = self._calculate_friction_force()

        # Полная внешняя сила для Impedance Control
        F_total_applied = F_haptic + F_external_user + friction_force + F_target + F_speed

        # Impedance Control: M * d²x + B * dx + K * (x - x_desired) = F_total_applied
        # Перепишем как: d²x = (F_total_applied - B * dx - K * (x - x_desired)) / M
        F_impedance = - self.impedance_damping * self.state.vx - self.impedance_stiffness * (self.state.x - x_desired)
        F_total = F_total_applied + F_impedance

        a = F_total / self.impedance_mass

        # Обновляем состояние
        self.state.vx += a * self.dt
        self.state.x += self.state.vx * self.dt

        # Применяем ограничения
        self._apply_velocity_threshold()
        self._apply_position_bounds()

        # Возвращаем силы для отладки/отображения (F_haptic, F_external_user)
        return F_haptic, F_external_user
    # ---------------------------------

    def step(self):
        """Один шаг симуляции — всегда работает"""
        if self.use_impedance_control:
            return self._impedance_step()
        else:
            external = self._calculate_external_force()
            F_haptic = self.profile.force(self.state.x)  # <-- Только профиль

            # --- УСЛОВНОЕ ВКЛЮЧЕНИЕ УПРАВЛЕНИЯ ---
            F_target = self._calculate_target_force() if self.use_target_control else 0.0
            F_speed = self._calculate_speed_control_force() if self.use_speed_control else 0.0
            # -------------------------------------

            # --- КИНЕТИЧЕСКОЕ ТРЕНИЕ (как и раньше) ---
            friction_force = self._calculate_friction_force()
            # -----------------------------------------

            # Суммируем все силы
            F_total = F_haptic + external + F_target + F_speed + friction_force

            a = self._calculate_acceleration(F_total)
            self._update_state(a)
            self._apply_velocity_threshold()
            self._apply_position_bounds()

            return F_haptic, external  # <-- Возвращаем только силу профиля
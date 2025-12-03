# core.py
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
#библиотека функций 
def constant(x, b=0.0, x_start=float('-inf'), x_end=float('inf'), f_stat=0.0, f_din=0.0):
    # Добавлены x_start, x_end для определения области действия трения
    # f_stat, f_din добавлены для передачи в PiecewiseProfile
    if x < x_start or x > x_end:
        return 0.0
    return b

def linear(x, a=0.0, b=0.0, x_start=float('-inf'), x_end=float('inf'), f_stat=0.0, f_din=0.0):
    # Добавлены x_start, x_end для определения области действия трения
    # f_stat, f_din добавлены для передачи в PiecewiseProfile
    if x < x_start or x > x_end:
        return 0.0
    return a * x + b

def trapezoid(x, x0=0.0, height=1.0, base_a=10.0, base_b=2.0, is_pit=False, f_stat=0.0, f_din=0.0, f_stat_base=None, f_din_base=None):
    """
    x0 - центр трапеции
    height - высота трапеции (или глубина, если is_pit = True)
    base_a - размер оснований (плоская часть) 
    base_b - длинна склонов (суммарно по 2)
    f_stat - сила статического трения для всей области трапеции (или склонов, если заданы *_base)
    f_din - сила кинетического трения для всей области трапеции (или склонов, если заданы *_base)
    f_stat_base - сила статического трения *только* для плоской части (base_a). Если None, используется f_stat.
    f_din_base - сила кинетического трения *только* для плоской части (base_a). Если None, используется f_din.
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


def semicircle(x, x0=0.0, radius=5.0, is_pit=False, f_stat=0.0, f_din=0.0):   
    """
    x0 - центр окружности
    radius - радиус
    f_stat - сила статического трения для области полукруга
    f_din - сила кинетического трения для области полукруга
    """
    if abs(x - x0) > radius:
        return 0.0
    y = math.sqrt(radius ** 2 - (x - x0) ** 2)
    return -y if is_pit else y

# sine_wave_sum также можно обновить, если планируется использовать её с трением
def sine_wave_sum(x, components=None, x_start=float('-inf'), x_end=float('inf'), f_stat=0.0, f_din=0.0): 
    """
    components: список словарей с ключами: 'amplitude', 'frequency', 'phase'
    Пример: [{'amplitude': 1.0, 'frequency': 0.1, 'phase': 0}, ...]
    f_stat, f_din - силы трения для области, где действует функция (требуется указать x_start, x_end)
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
    
    def get_local_friction(self, x):
        """
        Возвращает локальные параметры трения (static, kinetic) для позиции x.
        Если x не попадает ни в один элемент с трением, возвращает (None, None).
        """
        # Проходим по функциям в обратном порядке, чтобы при пересечении
        # приоритет отдавался последней добавленной (если так задумано)
        for f in reversed(self.functions):
            func = f['func']
            params = f['params']

            # Проверяем, активен ли элемент и есть ли у него параметры трения
            friction_static = params.get('f_stat', 0.0)
            friction_kinetic = params.get('f_din', 0.0)

            # Проверяем, находится ли x внутри "активной" зоны функции
            is_inside = False
            # --- Проверка для constant ---
            if func.__name__ == 'constant':
                x_start = params.get('x_start', float('-inf'))
                x_end = params.get('x_end', float('inf'))
                if x_start <= x <= x_end and (friction_static > 0 or friction_kinetic > 0):
                    is_inside = True

            # --- Проверка для linear ---
            elif func.__name__ == 'linear':
                x_start = params.get('x_start', float('-inf'))
                x_end = params.get('x_end', float('inf'))
                if x_start <= x <= x_end and (friction_static > 0 or friction_kinetic > 0):
                    is_inside = True

            # --- Проверка для trapezoid ---
            elif func.__name__ == 'trapezoid' and (friction_static > 0 or friction_kinetic > 0):
                x0 = params['x0']
                base_a = params.get('base_a', 10.0)
                base_b = params.get('base_b', 2.0)
                half_a = base_a / 2
                half_b = base_b / 2
                start_slope = x0 - half_a - half_b
                end_slope = x0 + half_a + half_b
                # Проверяем, внутри ли x области трапеции
                if start_slope <= x <= end_slope:
                    # Тогда возвращаем либо f_stat, f_din (для плоской части и склонов),
                    # либо f_stat_base, f_din_base (только для плоской части).
                    # f_stat_base, f_din_base - для плоской части (base_a).
                    # f_stat, f_din - для "всего" элемента трапеции.
                    # Проверим, на плоской ли части мы:
                    start_flat = x0 - half_a
                    end_flat = x0 + half_a
                    if start_flat <= x <= end_flat:
                        # Используем f_stat_base, f_din_base, если они заданы, иначе f_stat, f_din
                        fs = params.get('f_stat_base', friction_static)
                        fd = params.get('f_din_base', friction_kinetic)
                    else:
                        # Используем f_stat, f_din для склонов
                        fs = friction_static
                        fd = friction_kinetic
                    return fs, fd # НАХОДИТСЯ ВНУТРИ БЛОКА elif func.__name__ == 'trapezoid'
                # Если x не внутри трапеции, is_inside останется False для этой функции

            # --- Проверка для semicircle ---
            elif func.__name__ == 'semicircle' and (friction_static > 0 or friction_kinetic > 0):
                x0 = params['x0']
                radius = params['radius']
                # Проверяем, внутри ли x области полукруга
                if abs(x - x0) <= radius:
                    is_inside = True

            # --- Проверка для sine_wave_sum ---
            # elif func.__name__ == 'sine_wave_sum' and (friction_static > 0 or friction_kinetic > 0):
                # Предположим, что sine_wave_sum имеет трение везде, где определена (или задайте диапазон)
                # Для простоты, считаем, что если f_stat или f_din заданы, она "активна" везде
                # Или добавьте x_start, x_end в sine_wave_sum
                # Пока просто проверим, есть ли трение
                # Чтобы было точно, лучше добавить x_start, x_end к sine_wave_sum
                # x_start_sine = params.get('x_start', float('-inf'))
                # x_end_sine = params.get('x_end', float('inf'))
                # if x_start_sine <= x <= x_end_sine and (friction_static > 0 or friction_kinetic > 0):
                #    is_inside = True
                # Пока примем, что если трение задано, но диапазон не указан, оно не применяется
                # или применяется "везде", что может быть нежелательно.
                # Лучше добавить x_start, x_end к sine_wave_sum в её определении.
                # Пока оставим как есть, если не задан диапазон, трение не применяется.
                # Пока не реализуем, если нет явного диапазона.

            if is_inside and (friction_static > 0 or friction_kinetic > 0):
                return friction_static, friction_kinetic

        # Если не попал ни в один элемент с трением, возвращаем глобальные значения или (0, 0)
        # Возвращаем (None, None), чтобы вызывающий код мог понять, что нужно использовать глобальные.
        return None, None


class HapticSimulation:
    """Главный симулятор — чистая физика, без GUI"""
    def __init__(self, x_min=-100.0, x_max=100.0, mass=1.0, damping=0.1):
        self.x_min = x_min
        self.x_max = x_max
        self.mass = mass
        self.damping = damping
        self.dt = 0.01
        self.drag_spring_k = 0.1 # жёсткость "резинки" для пользователя

        # --- Трение ---
        self.static_friction_force = 0.0
        self.kinetic_friction_force = 0.0
        # ----------------

        self.profile = PiecewiseProfile()
        self.state = HapticObjectState(x=0.0)
        self.cursor_x = None  # только X — система 1D
        self.force_threshold = 1.001
        self.f_max = 150
        #---порог для скорости ---
        self.vx_threshold = 0.01 

        # --- ПАРАМЕТРЫ ДЛЯ СИЛЫ ПРУЖИНЫ К ЦЕЛИ ---
        self.target_x = None
        self.target_spring_k = 1.0  # жёсткость пружины к целевой позиции
        self.target_damping = 0.5   # демпфирование для ограничения скорости
        self.target_max_force = 100.0  # максимальная сила привода
        # ----------------------------------------

        # --- параметры для управления по скорости ---
        self.target_speed_x = None
        self.target_max_speed = 10.0
        self.target_zone_width = 50.0
        # ----------------------------------------------

        # --- параметры Impedance Control ---
        self.use_impedance_control = False
        self.impedance_mass = 1.0
        self.impedance_damping = 0.1
        self.impedance_stiffness = 0.0  # жёсткость к x_desired (например, от привода)
        # ---------------------------------------

        # --- флаги для переключения режимов управления ---
        self.use_target_control = False
        self.use_speed_control = False
        # ---------------------------------------------------------

    def set_profile(self, profile):
        #принимает объект PiecewiseProfile
        self.profile = profile

    def get_current_force(self):
        # Теперь возвращает только силу профиля
        return self.profile.force(self.state.x)

    def get_user_feel_force(self):
        # Сила, которую ощущает пользователь: профиль + трение
        F_profile = self.profile.force(self.state.x)
        F_friction = self._calculate_friction_force() # Использует локальное трение внутри
        # Для отображения: суммируем силу профиля и трение
        # Важно: это не сила, действующая на объект, а сила, которую "ощущает" пользователь
        return F_profile + F_friction

    def set_static_friction_force(self, force):
        """Устанавливает силу статического трения"""
        self.static_friction_force = abs(force)  # всегда положительная величина

    def set_kinetic_friction_force(self, force):
        """Устанавливает силу кинетического трения"""
        self.kinetic_friction_force = abs(force)  # всегда положительная величина

    def set_friction_forces(self, static_force, kinetic_force):
        """Устанавливает обе силы трения"""
        self.set_static_friction_force(static_force)
        self.set_kinetic_friction_force(kinetic_force)

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

    # ---  сухое трение зависит от скорости, порога и локального профиля ---
    def _calculate_friction_force(self):
        """
        Возвращает силу сухого трения, противоположно направленную скорости.
        Использует локальные параметры трения из профиля, если они заданы для текущей позиции.
        Иначе использует глобальные параметры.
        """
        # Получаем локальные параметры трения
        local_static, local_kinetic = self.profile.get_local_friction(self.state.x)

        # Выбираем параметры: локальные или глобальные
        f_static_to_use = local_static if local_static is not None else self.static_friction_force
        f_kinetic_to_use = local_kinetic if local_kinetic is not None else self.kinetic_friction_force

        # --- сухое трение зависит от скорости и порога, используя выбранные параметры ---
        if abs(self.state.vx) < self.vx_threshold:
            # Объект "стоит". В этой функции мы не знаем F_move, но в симуляции оно будет учитываться.
            # Поэтому возвращаем 0, если |F_move| < f_static_to_use, иначе - не 0 (это обрабатывается в step)
            # Для возврата силы трения как таковой, когда объект "стоит", возвращаем 0.
            # Реальное влияние статического трения обрабатывается в step.
            # Этот метод возвращает *кинетическое* трение, если объект движется, или 0, если стоит.
            return 0.0
        else:
            # Объект движется. Кинетическое трение против скорости.
            if self.state.vx > 0:
                return -f_kinetic_to_use
            elif self.state.vx < 0:
                return f_kinetic_to_use
            else: # vx == 0
                return 0.0
        # ---------------------------------------------------------


    # --- НОВЫЙ МЕТОД: расчёт движущей силы с учётом локального трения ---
    def _calculate_moving_force_with_friction(self, F_move):
        """
        Принимает движущую силу F_move (F_profile + F_external_user).
        Возвращает результирующую силу после применения локального трения.
        """
        # Получаем локальные параметры трения
        local_static, local_kinetic = self.profile.get_local_friction(self.state.x)
        f_static_to_use = local_static if local_static is not None else self.static_friction_force
        f_kinetic_to_use = local_kinetic if local_kinetic is not None else self.kinetic_friction_force

        # --- Применение (локального) трения к движущей силе ---
        if abs(self.state.vx) < self.vx_threshold:
            # Объект "стоит"
            if abs(F_move) < f_static_to_use:
                # Сила недостаточна для страгивания. Трение компенсирует F_move.
                # Результирующая сила на движение = 0.
                F_move_and_frict = 0.0
            else:
                # Сила достаточна для страгивания. Применяем кинетическое трение.
                # Направление кинетического трения против *текущей* скорости (даже если она близка к 0).
                # Если vx = 0, направление кинетического трения определяется направлением F_move.
                if self.state.vx > 0:
                    friction_force = -f_kinetic_to_use
                elif self.state.vx < 0:
                    friction_force = f_kinetic_to_use
                else: # vx == 0
                    # Направление кинетического трения, когда vx=0, определяется направлением силы, вызывающей движение.
                    # F_move вызывает движение. Если F_move > 0, кинетическое трение = -f_kinetic_to_use.
                    # Если F_move < 0, кинетическое трение = +f_kinetic_to_use.
                    if F_move > 0:
                        friction_force = -f_kinetic_to_use
                    elif F_move < 0:
                        friction_force = f_kinetic_to_use
                    else: # F_move == 0, но это не должно было сюда попасть (F_move >= f_static_to_use, f_static > 0)
                         friction_force = 0.0 # На всякий случай
                F_move_and_frict = F_move + friction_force
        else:
            # Объект движется. Кинетическое трение против текущей скорости.
            if self.state.vx > 0:
                friction_force = -f_kinetic_to_use
            else: # self.state.vx < 0 (так как else от abs(vx) < threshold)
                friction_force = f_kinetic_to_use
            F_move_and_frict = F_move + friction_force
        # ---------------------------------------------------------
        return F_move_and_frict
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

    # ---  Impedance Control ---
    def _impedance_step(self):
        x_desired = self.target_x if self.target_x is not None else self.state.x
        
        F_haptic = self.profile.force(self.state.x)

        F_external_user = self._calculate_external_force()

        # --- УСЛОВНОЕ ВКЛЮЧЕНИЕ УПРАВЛЕНИЯ ---
        F_target = self._calculate_target_force() if self.use_target_control else 0.0
        F_speed = self._calculate_speed_control_force() if self.use_speed_control else 0.0
        # -------------------------------------

        F_move = F_haptic + F_external_user
        F_control = F_target + F_speed

        # --- Применение (локального) трения к движущей силе ---
        F_move_and_frict = self._calculate_moving_force_with_friction(F_move)

        # Полная внешняя сила для Impedance Control
        F_total_applied = F_move_and_frict + F_control

        # Impedance Control: M * d²x + B * dx + K * (x - x_desired) = F_total_applied
        # Перепишем как: d²x = (F_total_applied - B * dx - K * (x - x_desired)) / M
        F_impedance = - self.impedance_damping * self.state.vx - self.impedance_stiffness * (self.state.x - x_desired)
        F_total = F_total_applied + F_impedance

        a = F_total / self.impedance_mass

        # проверка, не изменит ли ускорение направление скорости ---
        # Вычисляем новую скорость
        new_vx = self.state.vx + a * self.dt

        # Если новая скорость имеет противоположный знак, ограничиваем a
        if self.state.vx != 0 and (new_vx * self.state.vx < 0):
            # Требуемое ускорение, чтобы остановить за dt
            required_a_to_stop = -self.state.vx / self.dt
            # Ограничиваем a
            if a * self.state.vx < 0:  # a тормозит
                if a < required_a_to_stop and self.state.vx > 0:
                    a = required_a_to_stop
                elif a > required_a_to_stop and self.state.vx < 0:
                    a = required_a_to_stop
                # Обновляем F_total, чтобы оно соответствовало новому a
                F_total = a * self.impedance_mass

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
            F_haptic = self.profile.force(self.state.x)

            external = self._calculate_external_force()

            # --- УСЛОВНОЕ ВКЛЮЧЕНИЕ УПРАВЛЕНИЯ ---
            F_target = self._calculate_target_force() if self.use_target_control else 0.0
            F_speed = self._calculate_speed_control_force() if self.use_speed_control else 0.0
            # -------------------------------------

            F_move = F_haptic + external
            F_control = F_target + F_speed

            # --- Применение (локального) трения к движущей силе ---
            F_move_and_frict = self._calculate_moving_force_with_friction(F_move)
            
            # Суммируем движущую и управляющую силы
            F_total = F_move_and_frict + F_control
            
            a = self._calculate_acceleration(F_total)

            # --- НОВОЕ: проверка, не изменит ли ускорение направление скорости ---
            # Вычисляем новую скорость
            new_vx = self.state.vx + a * self.dt

            # Если новая скорость имеет противоположный знак, ограничиваем a
            if self.state.vx != 0 and (new_vx * self.state.vx < 0):
                # Требуемое ускорение, чтобы остановить за dt
                required_a_to_stop = -self.state.vx / self.dt
                # Ограничиваем a
                if a * self.state.vx < 0:  # a тормозит
                    if a < required_a_to_stop and self.state.vx > 0:
                        a = required_a_to_stop
                    elif a > required_a_to_stop and self.state.vx < 0:
                        a = required_a_to_stop
                    # Обновляем F_total, чтобы оно соответствовало новому a
                    F_total = a * self.mass  # Используем self.mass, т.к. вызываем _calculate_acceleration

            # Обновляем состояние
            self.state.vx += a * self.dt
            self.state.x += self.state.vx * self.dt
            # ---------------------------------------------------------

            # Применяем ограничения
            self._apply_velocity_threshold()
            self._apply_position_bounds()

            return F_haptic, external  # <-- Возвращаем только силу профиля и внешнюю

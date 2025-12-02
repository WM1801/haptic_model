#main.py
from potential_profile import constant, linear, trapezoid, semicircle, sine_wave_sum, PiecewiseProfile
from force_profile import constant_force, linear_force, trapezoid_force,  ForceProfile
from core import HapticSimulation
from gui import HapticGUI  # Теперь HapticGUI импортируется из gui.py
import math


# -------------------------------------------------
# MAIN
# -------------------------------------------------
if __name__ == "__main__":
    # Создаём чистую модель
    sim = HapticSimulation(
        x_min=50.0,
        x_max=550.0,
        mass=5.0,
        damping=2.0
    )

    # Установим постоянную силу (например, сопротивление движению)
    sim.set_kinetic_friction_force(5)
    sim.set_static_friction_force(7)

    #Создаем профиль 
    profile = PiecewiseProfile()
    # Пример: добавим трапецию и синусоиду
    profile.add_function(constant, b=0.0, override=False)
    #profile.add_function(semicircle, x0=100, radius=10, is_pit=False, override=True)
    #profile.add_function(trapezoid, x0=300, height=200, base_a=100, base_b=100, is_pit=False, override=False)
    #profile.add_function(sine_wave_sum, components=[
    #    {'amplitude': 1.0, 'frequency': 0.2, 'phase': 0},
    #    {'amplitude': 0.5, 'frequency': 0.5, 'phase': math.pi / 4}
    #])
    
    #profile.add_function(trapezoid, x0=300, height=500, base_a=100, base_b=30, is_pit=False)
    #profile.add_function(sine_wave_sum, components=[
    #    {'amplitude': 5.0, 'frequency': 0.2, 'phase': 0},
    #    {'amplitude': 2.0, 'frequency': 0.5, 'phase': math.pi / 4}
    #])

    force_profile = ForceProfile()
    force_profile.add_function(constant_force, magnitude=0.0)
    #force_profile.add_function(linear_force, k=0.0, x_eq=0.0)
    force_profile.add_function(trapezoid_force, x0=300, max_force=30, base_a=100, base_b=30, is_negative=False)
    #force_profile.add_function(sine_wave_sum, components=[
    #    {'amplitude': 5.0, 'frequency': 0.2, 'phase': 0},
    #    {'amplitude': 2.0, 'frequency': 0.5, 'phase': math.pi / 4}
    #])

    # Применяем профиль
    sim.potential_profile = profile  # Изменено: напрямую присваиваем, т.к. set_profile теперь для совместимости
    sim.force_profile = force_profile
    sim.toggle_impedance_control() 
    # Запускаем GUI
    app = HapticGUI(sim)
    app.run()
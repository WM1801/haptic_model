#main.py

from core import HapticSimulation, PiecewiseProfile, constant, linear, trapezoid, semicircle, sine_wave_sum
from gui import HapticGUI
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
    sim.set_constant_force(10.0)

    #Создаем профиль 
    profile = PiecewiseProfile()
    # Пример: добавим трапецию и синусоиду
    profile.add_function(constant, b=0.0)
    #profile.add_function(trapezoid, x0=300, height=500, base_a=100, base_b=30, is_pit=False)
    #profile.add_function(sine_wave_sum, components=[
    #    {'amplitude': 5.0, 'frequency': 0.2, 'phase': 0},
    #    {'amplitude': 2.0, 'frequency': 0.5, 'phase': math.pi / 4}
    #])

    # Применяем профиль
    sim.set_profile(profile)

    # Запускаем GUI
    app = HapticGUI(sim)
    app.run()
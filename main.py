#main.py

from core import HapticSimulation
from gui import HapticGUI



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
    sim.set_profile(x0=300, width=100, slope_w=30, strength=500, is_pit=False)

    # Запускаем GUI
    app = HapticGUI(sim)
    app.run()
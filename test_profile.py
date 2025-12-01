import unittest
from core import PiecewiseProfile, semicircle, trapezoid, constant

# ---  функция для построения графика ---
def plot_profile(profile, x_min, x_max, steps=500):
    import matplotlib.pyplot as plt
    from matplotlib.widgets import Button

    fig, ax = plt.subplots(figsize=(10, 6))
    plt.subplots_adjust(bottom=0.2)

    xs = []
    us = []
    dx = (x_max - x_min) / steps
    for i in range(steps + 1):
        x = x_min + i * dx
        u = profile.potential(x)
        xs.append(x)
        us.append(u)

    ax.plot(xs, us, label='Potential U(x)', color='blue')
    ax.set_title('Профиль потенциала U(x)')
    ax.set_xlabel('x')
    ax.set_ylabel('U(x)')
    ax.grid(True)
    ax.legend()

    # --- Устанавливаем соразмерность ---
    ax.set_aspect('equal', adjustable='box')
    # ------------------------------------

    # --- Устанавливаем фиксированный ylim ---
    y_max = max(us) if us else 1
    y_min = min(us) if us else 0
    ax.set_ylim(y_min - 200, y_max + 200)  # добавим немного отступа
    # ---------------------------------------

    # --- Функции для кнопок ---
    def zoom_in(event):
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        ax.set_xlim([x * 0.8 for x in xlim])
        ax.set_ylim([y * 0.8 for y in ylim])
        ax.set_aspect('equal', adjustable='box')  # Восстанавливаем соразмерность
        fig.canvas.draw()

    def zoom_out(event):
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        ax.set_xlim([x * 1.25 for x in xlim])
        ax.set_ylim([y * 1.25 for y in ylim])
        ax.set_aspect('equal', adjustable='box')  # Восстанавливаем соразмерность
        fig.canvas.draw()

    def reset_view(event):
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min - 1, y_max + 1)  # восстанавливаем фиксированный ylim
        ax.set_aspect('equal', adjustable='box')  # Восстанавливаем соразмерность
        fig.canvas.draw()
    # ---------------------------

    # --- Создание кнопок ---
    ax_zoom_in = plt.axes([0.3, 0.05, 0.1, 0.075])
    ax_zoom_out = plt.axes([0.41, 0.05, 0.1, 0.075])
    ax_reset = plt.axes([0.52, 0.05, 0.1, 0.075])

    btn_zoom_in = Button(ax_zoom_in, 'Zoom In')
    btn_zoom_out = Button(ax_zoom_out, 'Zoom Out')
    btn_reset = Button(ax_reset, 'Reset')

    btn_zoom_in.on_clicked(zoom_in)
    btn_zoom_out.on_clicked(zoom_out)
    btn_reset.on_clicked(reset_view)
    # -----------------------

    plt.show()



class TestPiecewiseProfile(unittest.TestCase):

    def test_constant_function(self):
        """Проверяем, что constant возвращает b"""
        profile = PiecewiseProfile()
        profile.add_function(constant, b=5.0)
        self.assertEqual(profile.potential(0), 5.0)
        self.assertEqual(profile.potential(100), 5.0)

    def test_semicircle_in_range(self):
        """Проверяем полуокружность в центре"""
        profile = PiecewiseProfile()
        profile.add_function(semicircle, x0=100, radius=20, is_pit=False)
        # В центре полуокружности высота = радиус
        self.assertAlmostEqual(profile.potential(100), 20.0, places=2)
        # На краях = 0
        self.assertAlmostEqual(profile.potential(120), 0.0, places=2)
        self.assertAlmostEqual(profile.potential(80), 0.0, places=2)

    def test_semicircle_out_of_range(self):
        """Проверяем полуокружность вне диапазона"""
        profile = PiecewiseProfile()
        profile.add_function(semicircle, x0=100, radius=20, is_pit=False)
        self.assertEqual(profile.potential(50), 0.0)
        self.assertEqual(profile.potential(150), 0.0)

    def test_trapezoid_in_range(self):
        """Проверяем трапецию в центре"""
        profile = PiecewiseProfile()
        profile.add_function(trapezoid, x0=300, height=2, base_a=10, base_b=2, is_pit=False)
        # В центре трапеции (плоская часть) высота = height
        self.assertAlmostEqual(profile.potential(300), 2.0, places=2)

    def test_trapezoid_out_of_range(self):
        """Проверяем трапецию вне диапазона"""
        profile = PiecewiseProfile()
        profile.add_function(trapezoid, x0=300, height=2, base_a=10, base_b=2, is_pit=False)
        # Допустим, ширина трапеции = base_a + base_b = 12, т.е. [294, 306]
        self.assertEqual(profile.potential(290), 0.0)
        self.assertEqual(profile.potential(310), 0.0)

    def test_sum_of_functions(self):
        """Проверяем, что potential суммирует функции"""
        profile = PiecewiseProfile()
        profile.add_function(semicircle, x0=100, radius=20, is_pit=False)  # в x=100 -> 20
        profile.add_function(trapezoid, x0=300, height=2, base_a=10, base_b=2, is_pit=False)  # в x=100 -> 0

        self.assertAlmostEqual(profile.potential(100), 20.0, places=2)
        self.assertAlmostEqual(profile.potential(300), 2.0, places=2)

    def test_force_calculation(self):
        """Проверяем, что force возвращает разумное значение"""
        profile = PiecewiseProfile()
        profile.add_function(semicircle, x0=100, radius=20, is_pit=False)
        force_at_100 = profile.force(100)
        # В центре симметричной функции сила должна быть ~0
        self.assertAlmostEqual(force_at_100, 0.0, places=1)

        force_at_edge = profile.force(119.9)  # рядом с краем
        # Сила должна быть отлична от нуля
        self.assertNotAlmostEqual(force_at_edge, 0.0, places=1)

    # --- НОВЫЙ ТЕСТ: проверка конкретного профиля ---
    def test_specific_profile(self):
        """Тестируем конкретный профиль из main.py"""
        profile = PiecewiseProfile()
        profile.add_function(constant, b=0.0)
        profile.add_function(semicircle, x0=100, radius=20, is_pit=False)  # пик в 20
        profile.add_function(trapezoid, x0=300, height=2, base_a=10, base_b=50, is_pit=False)  # пик в 2

        # Проверим значения в ключевых точках
        # x = 100: только semicircle активна
        self.assertAlmostEqual(profile.potential(100), 20.0, places=2)
        # x = 300: только trapezoid активна (ширина 60, т.е. [270, 330])
        self.assertAlmostEqual(profile.potential(300), 2.0, places=2)
        # x = 200: обе функции должны давать 0
        self.assertAlmostEqual(profile.potential(200), 0.0, places=2)
        # x = 0: обе функции дают 0
        self.assertAlmostEqual(profile.potential(0), 0.0, places=2)

        # Проверим, что сила в центре полуокружности ~0
        self.assertAlmostEqual(profile.force(100), 0.0, places=1)

        # Проверим, что сила в центре трапеции ~0
        self.assertAlmostEqual(profile.force(300), 0.0, places=1)

        # Проверим, что сила на краю полуокружности отлична от 0
        force_near_edge = profile.force(119.9)
        self.assertNotAlmostEqual(force_near_edge, 0.0, places=1)

    # ---------------------------------------------

if __name__ == '__main__':
    # Запуск тестов
    unittest.main(exit=False)  # Не завершаем после тестов

    # --- Построение графика ---
    print("\n--- Рисуем график профиля ---")
    profile = PiecewiseProfile()
    profile.add_function(constant, b=0.0)
    profile.add_function(semicircle, x0=100, radius=50, is_pit=False)
    profile.add_function(trapezoid, x0=300, height=20, base_a=10, base_b=50, is_pit=False)

    plot_profile(profile, x_min=0, x_max=400)
    # --------------------------

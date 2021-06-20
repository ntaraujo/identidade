from kivy.clock import Clock
from kivy.properties import NumericProperty
from kivy.uix.widget import Widget
from kivymd.app import MDApp
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.image import Image


class Game(Screen):
    def on_enter(self, *args):
        Clock.schedule_interval(self.update, 1 / 30)

    def game_over(self):
        # Clock.unschedule(self.update, 1 / 30)
        self.ids.player.x = self.width / 1.25
        self.ids.player.y = self.height / 20
        self.ids.player.speed_y = 1000
        self.ids.player.speed_x = 500

    def update(self, *args):
        self.ids.player.speed_y += -self.height * 3 * 1 / 30
        self.ids.player.y += self.ids.player.speed_y * 1 / 30
        self.ids.player.x -= self.ids.player.speed_x * 1 / 30
        if not (0 < self.ids.player.y < self.height) or not (0 < self.ids.player.x < self.width):
            self.game_over()

    def on_touch_down(self, touch):
        self.ids.player.speed_y = self.height
        self.ids.player.speed_x *= -1


class Manager(ScreenManager):
    pass


class Player(Image):
    speed_y = NumericProperty(1000)
    speed_x = NumericProperty(500)


class Bird(Widget):
    pass


class Trampoline(Image):
    pass


class Identidade(MDApp):
    pass


if __name__ in ('__main__', '__android__'):
    Identidade().run()

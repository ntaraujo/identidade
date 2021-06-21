from kivy.animation import Animation
from kivy.clock import Clock
from kivy.properties import NumericProperty
from kivymd.app import MDApp
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.image import Image
from random import choice, randrange


class Game(Screen):
    birds = []

    def on_enter(self, *args):
        Clock.schedule_interval(self.update, 1 / 30)
        Clock.schedule_interval(self.put_bird, 2)

    def put_bird(self, *args):
        bird = Bird(y=randrange(0, self.height), x=choice((0, self.width)))
        self.add_widget(bird)
        self.birds.append(bird)

    def game_over(self):
        # Clock.unschedule(self.update, 1 / 30)
        # Clock.unschedule(self.put_bird, 2)
        self.ids.player.x = self.width / 1.25
        self.ids.player.y = self.height / 20
        self.ids.player.speed_y = 1000
        self.ids.player.speed_x = 500
        for b in self.birds:
            b.anim.cancel(b)
            self.remove_widget(b)
        self.birds = []

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


class Bird(Image):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        game_screen = MDApp.get_running_app().root.get_screen('game')
        x = game_screen.width if self.x == 0 else 0
        self.anim = Animation(y=game_screen.ids.player.y, x=x, duration=0.5)
        self.anim.bind(on_complete=self.vanish)
        self.anim.start(self)

    def vanish(self, *args):
        game_screen = MDApp.get_running_app().root.get_screen('game')
        game_screen.remove_widget(self)
        game_screen.birds.remove(self)


class Trampoline(Image):
    pass


class Identidade(MDApp):
    pass


if __name__ in ('__main__', '__android__'):
    Identidade().run()

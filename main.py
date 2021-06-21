from kivy.animation import Animation
from kivy.clock import Clock
from kivy.properties import NumericProperty
from kivy.uix.widget import Widget
from kivymd.app import MDApp
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.image import Image
from random import random


class Manager(ScreenManager):
    pass


class Game(Screen):
    obstacles = []
    score = NumericProperty()

    def __init__(self, **kw):
        global game
        game = self
        super().__init__(**kw)

    def on_enter(self, *args):
        Clock.schedule_interval(self.update, 1/30)
        Clock.schedule_interval(self.put_obstacle, 2)

    def put_obstacle(self, *args):
        gap = self.width / 2
        position = (self.width - gap) * random()
        height = self.height * 0.05
        obstacle_left = Obstacle(y=self.height, width=position, height=height)
        obstacle_right = Obstacle(y=self.height, x=position+gap, width=self.width-position-gap, height=height)
        self.add_widget(obstacle_left)
        self.obstacles.append(obstacle_left)
        self.add_widget(obstacle_right)
        self.obstacles.append(obstacle_right)

    def on_pre_enter(self, *args):
        player.x = self.width * 0.9
        player.y = self.height / 20
        player.speed_y = 1000
        player.speed_x = 500

    def update(self, *args):
        player.speed_y += -self.height * 4 * 1 / 30
        player.y += player.speed_y * 1 / 30
        player.x -= player.speed_x * 1 / 30
        if not 0 < player.y < self.height or not 0 < player.x < self.width or self.player_collided():
            self.game_over()

    def game_over(self):
        Clock.unschedule(self.update, 1/30)
        Clock.unschedule(self.put_obstacle, 1)
        for ob in self.obstacles:
            ob.anim.cancel(ob)
            self.remove_widget(ob)
        self.obstacles = []
        root.current = 'game_over'

    @staticmethod
    def collided(wid1, wid2):
        if wid2.x <= wid1.x + wid1.width and wid2.x + wid2.width >= wid1.x and \
                wid2.y <= wid1.y + wid1.height and wid2.y + wid2.height >= wid1.y:
            return True
        return False

    def player_collided(self):
        for ob in self.obstacles:
            if self.collided(player, ob):
                return True
        return False

    def on_touch_down(self, touch):
        player.speed_y = self.height
        player.speed_x *= -1


class Player(Widget):
    speed_y = NumericProperty(1000)
    speed_x = NumericProperty(500)

    def __init__(self, **kwargs):
        global player
        player = self
        super().__init__(**kwargs)


class Menu(Screen):
    pass


class GameOver(Screen):
    pass


class Obstacle(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.anim = Animation(y=-self.height, duration=3)
        self.anim.bind(on_complete=self.vanish)
        self.anim.start(self)

    def vanish(self, *args):
        game.remove_widget(self)
        game.obstacles.remove(self)


class Identidade(MDApp):
    def build(self):
        global root
        root = self.root
        self.theme_cls.theme_style = "Dark"


if __name__ in ('__main__', '__android__'):
    app = Identidade()
    app.run()

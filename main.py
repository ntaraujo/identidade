from kivy.animation import Animation
from kivy.clock import Clock
from kivy.properties import NumericProperty
from kivy.uix.widget import Widget
from kivymd.app import MDApp
from kivy.uix.screenmanager import Screen, ScreenManager
from random import random, choice
from kivy.core.audio import SoundLoader


class Manager(ScreenManager):
    pass


class Game(Screen):
    obstacles = []
    score = NumericProperty()
    level = NumericProperty(0)
    speed_y_parameter = 5 / 4
    interval = 2
    duration = 3
    height_gap = NumericProperty()
    game_height = NumericProperty()
    random_obstacle = None

    def __init__(self, **kw):
        global game
        game = self
        self.music = SoundLoader.load('lofi.mp3')
        if self.music:
            self.music.loop = True
            self.music.play()
        super().__init__(**kw)

    def next_level(self):
        self.level += 1
        self.duration -= self.duration / 8
        self.speed_y_parameter -= self.speed_y_parameter / 8
        speed_y = self.height * self.speed_y_parameter
        player.speed_y = speed_y if player.speed_y >= 0 else -speed_y

        Clock.unschedule(self.put_obstacle, self.interval)
        self.interval -= self.interval / 8
        Clock.schedule_interval(self.put_obstacle, self.interval)

    def on_enter(self, *args):
        player.speed_y = self.height * self.speed_y_parameter
        player.speed_x = self.width * 0.75
        Clock.schedule_interval(self.update, 1 / 30)
        Clock.schedule_interval(self.put_obstacle, 2)

    def put_obstacle(self, *args):
        gap = self.width / 2
        position = (self.width - gap) * random()
        height = self.height * 0.02
        obstacle_left = Obstacle(y=self.height, width=position, height=height)
        obstacle_right = Obstacle(y=self.height, x=position + gap, width=self.width - position - gap, height=height)
        self.add_widget(obstacle_left)
        self.obstacles.append(obstacle_left)
        self.add_widget(obstacle_right)
        self.obstacles.append(obstacle_right)

    def on_pre_enter(self, *args):
        player.x = self.width * 0.9
        player.y = self.height / 20
        self.score = 0
        self.level = 0
        self.speed_y_parameter = 5 / 4
        self.interval = 2
        self.duration = 3

    def update(self, *args):
        player.speed_y += -self.height * 4 * 1 / 30
        player.y += player.speed_y * 1 / 30
        player.x -= player.speed_x * 1 / 30
        if not -self.height_gap < player.y < self.game_height or not 0 < player.x < self.width:
            self.game_over()
        else:
            ob = self.obstacle_collided()
            if ob is None:
                return
            elif ob == self.random_obstacle and ob.color == app.theme_cls.primary_color:
                ob.color = app.theme_cls.accent_color
                Clock.schedule_once(lambda *a: setattr(self, 'random_obstacle', None), 2)
                player.speed_y *= -1
                self.next_level()
            else:
                self.game_over()

    def game_over(self):
        Clock.unschedule(self.update, 1 / 30)
        Clock.unschedule(self.put_obstacle, 2)
        for ob in self.obstacles:
            ob.anim.cancel(ob)
            self.remove_widget(ob)
        self.obstacles = []
        game_over.high_score = max(game_over.high_score, self.score)
        root.current = 'game_over'

    def obstacle_collided(self):
        for ob in self.obstacles:
            if player.collide_widget(ob):
                return ob
        return None

    def on_touch_down(self, touch):
        player.speed_y = self.height
        player.speed_x *= -1

    def obstacle_choice(self):
        self.random_obstacle = choice(self.obstacles)
        self.random_obstacle.color = app.theme_cls.primary_color


class Player(Widget):
    speed_y = NumericProperty()
    speed_x = NumericProperty()

    def __init__(self, **kwargs):
        global player
        player = self
        super().__init__(**kwargs)


class Menu(Screen):
    pass


class GameOver(Screen):
    high_score = NumericProperty()

    def __init__(self, **kw):
        global game_over
        game_over = self
        super().__init__(**kw)


class Obstacle(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.anim = Animation(y=-self.height, duration=game.duration)
        self.anim.bind(on_complete=self.vanish)
        self.anim.start(self)

    def vanish(self, *args):
        game.score += 0.5
        game.remove_widget(self)
        game.obstacles.remove(self)

        if game.score % 4 == 0:
            game.obstacle_choice()


class Identidade(MDApp):
    def build(self):
        global root
        root = self.root
        self.theme_cls.theme_style = "Dark"


if __name__ in ('__main__', '__android__'):
    app = Identidade()
    app.run()

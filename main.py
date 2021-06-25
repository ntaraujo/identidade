# -*- coding: utf-8 -*-
from kivy import Config
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import NumericProperty, DictProperty
from kivy.uix.widget import Widget
from kivymd.app import MDApp
from kivy.uix.screenmanager import Screen, ScreenManager
from random import random, randrange, choice
from kivy.core.audio import SoundLoader
from kivymd.uix.button import MDRectangleFlatButton
from kivymd.uix.dialog import MDDialog
from json import load
from webbrowser import open as web_open

from kivymd.uix.progressbar import MDProgressBar

MDProgressBar
default_settings = {
    'volume': 100,
    'fps': 30,
    'high_score': 0,
    'theme_style': 'Dark'
}
Config.adddefaultsection('identidade')
Config.setdefaults('identidade', default_settings)


class Dialog(MDDialog):
    # auto_dismiss do not have effect on ESC functionality
    def _handle_keyboard(self, window, key, *largs):
        if key == 27:
            self.dismiss()
            return True


class Manager(ScreenManager):
    pass


class Game(Screen):
    obstacles = []
    score = NumericProperty()
    level = NumericProperty()
    spf = NumericProperty()
    speed_y_parameter = 5 / 4
    interval = 2
    duration = 3
    height_gap = NumericProperty()
    game_height = NumericProperty()
    width_gap = NumericProperty()
    game_width = NumericProperty()
    random_obstacle = None
    paused = False

    with open('dialogs.json', 'r', encoding='utf-8') as dialogs:
        dialogs = load(dialogs)

    def __init__(self, **kw):
        global game
        game = self
        self.dialog = None
        super().__init__(**kw)

    def next_level(self, obstacle_running=True):
        self.level += 1
        self.duration -= self.duration / 8
        self.speed_y_parameter -= self.speed_y_parameter / 8
        speed_y = self.height * self.speed_y_parameter
        player.speed_y = speed_y if player.speed_y >= 0 else -speed_y

        if obstacle_running:
            Clock.unschedule(self.put_obstacle, self.interval)
        self.interval -= self.interval / 8
        Clock.schedule_interval(self.put_obstacle, self.interval)

    def on_enter(self, *args):
        if not self.paused:
            player.speed_y = self.height * self.speed_y_parameter
            player.speed_x = self.width * 0.75
        else:
            self.paused = False
        self.play()

    def play(self, obstacle=True):
        Clock.schedule_interval(self.update, self.spf)
        if obstacle:
            Clock.schedule_interval(self.put_obstacle, self.interval)

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
        if not self.paused:
            player.x = self.width * 0.9
            player.y = self.height / 20
            self.score = 0
            self.level = 0
            self.speed_y_parameter = 5 / 4
            self.interval = 2
            self.duration = 3
        else:
            self.paused = False

    def update(self, *args):
        player.speed_y += -self.height * 4 * self.spf
        player.y += player.speed_y * self.spf
        player.x -= player.speed_x * self.spf
        if not -self.height_gap < player.y < self.game_height or not -self.width_gap < player.x < self.game_width:
            self.game_over()
        else:
            ob = self.obstacle_collided()
            if ob is None:
                return
            elif ob == self.random_obstacle:
                ob.color = app.theme_cls.accent_color
                self.random_obstacle = None
                if player.speed_y < 0:
                    player.speed_y *= -1
                player.speed_x *= -1
                self.show_dialog()
            else:
                self.game_over()

    def show_dialog(self, *args):
        self.stop_and_clear()
        try:
            info = self.dialogs[self.level].copy()
        except IndexError:  # no more dialogs
            self.play(obstacle=False)
            self.next_level(obstacle_running=False)
            return

        def dismiss_dialog(*_):
            self.dialog.dismiss()

        btns_info = info.pop("buttons", None)
        if btns_info is None:
            button = MDRectangleFlatButton(text="Peguei!")
            button.bind(on_release=dismiss_dialog)
            buttons = [button]
        else:
            buttons = []
            for btn_info in btns_info:
                button = MDRectangleFlatButton(text=btn_info['text'])
                if 'link' in btn_info:

                    def open_button_link(_, link=btn_info['link']):
                        web_open(link)

                    button.bind(on_release=open_button_link)
                else:
                    button.bind(on_release=dismiss_dialog)
                buttons.append(button)
        app.dialog_button = buttons[-1]
        self.dialog = Dialog(auto_dismiss=False, buttons=buttons, **info)
        self.dialog.bind(on_dismiss=self.dismissed_dialog)
        self.dialog.open()

    def dismissed_dialog(self, *args):
        self.play(obstacle=False)
        self.next_level(obstacle_running=False)

    def stop_and_clear(self):
        Clock.unschedule(self.update, self.spf)
        Clock.unschedule(self.put_obstacle, self.interval)
        for ob in self.obstacles:
            ob.anim.cancel(ob)
            self.remove_widget(ob)
        self.obstacles = []

    def game_over(self):
        self.stop_and_clear()
        app.settings['high_score'] = max(app.settings['high_score'], self.score)
        root.current = 'game_over'

    def pause(self):
        self.stop_and_clear()
        self.paused = True
        pause.game_score = self.score
        pause.game_level = self.level
        root.current = 'pause'

    def obstacle_collided(self):
        for ob in self.obstacles:
            if player.collide_widget(ob):
                return ob
        return None

    def on_touch_down(self, touch):
        player.jump()
        return super().on_touch_down(touch)

    def obstacle_choice(self):
        # heavy, looks like there is only one possible obstacle
        obs = iter(self.obstacles)
        c = randrange(0, int(len(self.obstacles) / 2))
        for index, (o1, o2) in enumerate(zip(obs, obs)):
            if index == c:
                self.random_obstacle = o1 if o1.width > o2.width else o2
                break
        else:
            self.random_obstacle = choice(self.obstacles)
            print('obstacle_choice fail')
        self.random_obstacle.color = app.theme_cls.primary_color


class Player(Widget):
    speed_y = NumericProperty()
    speed_x = NumericProperty()

    def __init__(self, **kwargs):
        global player
        player = self
        super().__init__(**kwargs)

    def jump(self):
        self.speed_y = game.height
        self.speed_x *= -1


class Menu(Screen):
    pass


class GameOver(Screen):
    def __init__(self, **kw):
        global game_over
        game_over = self
        super().__init__(**kw)


class Pause(Screen):
    game_score = NumericProperty()
    game_level = NumericProperty()

    def __init__(self, **kw):
        global pause
        pause = self
        super().__init__(**kw)


class Setting(Screen):
    pass


class Tutorial(Screen):
    pass


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
    dialog_button = None
    settings = DictProperty({
        'volume': Config.getfloat('identidade', 'volume'),
        'fps': Config.getfloat('identidade', 'fps'),
        'high_score': Config.getfloat('identidade', 'high_score'),
        'theme_style': Config.get('identidade', 'theme_style')
    })

    def __init__(self, **kwargs):
        self.music = SoundLoader.load('lofi.ogg')
        if self.music:
            self.music.loop = True
            self.music.volume = self.settings['volume'] / 100
            self.music.play()
        else:
            print('[identidade] lofi.ogg not worked')

            class FakeMusic:
                volume = 100

            self.music = FakeMusic()
        super().__init__(**kwargs)

    def build(self):
        global root
        root = self.root
        self.theme_cls.theme_style = self.settings['theme_style']

        Window.bind(on_keyboard=self.keyboard_handler)

    def keyboard_handler(self, window, key, *args):
        if key == 27:  # ESC or back button
            if root.current == 'game' and not isinstance(app.root_window.children[0], Dialog):
                game.pause()
                return True
            elif root.current in ('setting', 'tutorial'):
                root.current = 'menu'
                return True
        elif key == 32:  # space
            if root.current == 'game':
                player.jump()
                return True
        elif key == 13:  # enter
            if self.dialog_button is None:
                if root.current in ('menu', 'game_over', 'pause'):
                    root.current = 'game'
                    return True
            else:
                self.dialog_button.dispatch('on_press')
                self.dialog_button.dispatch('on_release')
                self.dialog_button = None

    def on_pause(self):
        self.save()
        if root.current == 'game' and not isinstance(app.root_window.children[0], Dialog):
            game.pause()
        return True

    def on_stop(self):
        self.save()

    def save(self):
        Config.setall('identidade', self.settings)
        Config.write()
        print('[identidade] Settings saved')

    def to_default(self, option):
        self.settings[option] = default_settings[option]


if __name__ in ('__main__', '__android__'):
    app = Identidade()
    app.run()

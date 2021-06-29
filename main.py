# -*- coding: utf-8 -*-
from kivy import Config
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import NumericProperty, DictProperty, BooleanProperty, StringProperty
from kivy.uix.widget import Widget
from kivymd.app import MDApp
from kivy.uix.screenmanager import Screen, ScreenManager
from random import random, randrange, choice
from kivy.core.audio import SoundLoader
from kivymd.uix.button import MDRectangleFlatButton
from kivymd.uix.dialog import MDDialog
from json import load
from webbrowser import open as web_open
from kivy.utils import platform

default_settings = {
    'volume': 100,
    'fps': 30,
    'high_status': 0,
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
    loses = NumericProperty()
    status = NumericProperty()
    playing = False

    with open('dialogs.json', 'r', encoding='utf-8') as dialogs:
        dialogs = load(dialogs)

    with open(
            'tutorial-mobile.json' if platform in ('android', 'ios') else 'tutorial-desktop.json',
            'r', encoding='utf-8'
    ) as tutorial:
        tutorial = load(tutorial)
    tutorial_step = 0

    message = StringProperty(tutorial[0])

    def __init__(self, **kw):
        global game
        game = self
        self.dialog = None
        super().__init__(**kw)

    def next_level(self, obstacle_running=True):
        self.level += 1

        if not app.tutorial:
            self.duration -= self.duration / 8
            self.speed_y_parameter -= self.speed_y_parameter / 8

            if obstacle_running:
                Clock.unschedule(self.put_obstacle, self.interval)
            self.interval -= self.interval / 8
            Clock.schedule_interval(self.put_obstacle, self.interval)

        speed_y = self.height * self.speed_y_parameter
        player.speed_y = speed_y if player.speed_y >= 0 else -speed_y

    def on_enter(self, *args):
        if not self.paused:
            player.speed_y = self.height * self.speed_y_parameter
            player.speed_x = self.width * 0.75
            if app.tutorial:
                Animation(center=self.center, d=1).start(player)
            else:
                new_pos = self.width * 0.9, self.height / 20
                Animation(pos=(self.width * 0.9, self.height / 20), d=1).start(player)
                Clock.schedule_once(self.play, 1.2)
        else:
            self.paused = False

    def play(self, *args, obstacle=True):
        Clock.schedule_interval(self.update, self.spf)
        if obstacle:
            Clock.schedule_interval(self.put_obstacle, self.interval)
        self.playing = True

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
            self.score = 0
            self.level = 0
            self.loses = 0
            self.speed_y_parameter = 5 / 4
            self.interval = 2
            self.duration = 3
        else:
            self.paused = False

        if app.tutorial:
            self.tutorial_step = 0
            self.message = self.tutorial[0]
            Clock.schedule_interval(self.update_tutorial, 8)

    def update_tutorial(self, *args):
        self.tutorial_step += 1
        if self.tutorial_step == 5:
            Clock.schedule_interval(self.put_obstacle, self.interval)
        try:
            self.message = self.tutorial[self.tutorial_step]
        except IndexError:
            pass

    def update(self, *args):
        player.speed_y += -self.height * 4 * self.spf
        player.y += player.speed_y * self.spf
        player.x -= player.speed_x * self.spf
        in_edges = True
        if app.tutorial:
            if -self.height_gap > player.y:
                player.y = -self.height_gap
                player.jump(horizontal=False)
            elif player.y + player.height > self.game_height:
                player.y = self.game_height - player.height
            elif -self.width_gap > player.x:
                player.x = -self.width_gap
                player.speed_x *= -1
            elif player.x + player.width > self.game_width:
                player.x = self.game_width - player.width
                player.speed_x *= -1
            else:
                in_edges = False
        elif -self.height_gap < player.y < self.game_height and -self.width_gap < player.x < self.game_width:
            in_edges = False

        if in_edges:
            self.game_over()
            return

        ob = self.obstacle_collided()
        if ob is None:
            return
        elif ob == self.random_obstacle:
            ob.color = app.theme_cls.accent_color
            self.random_obstacle = None
            self.show_dialog()
        elif not ob.collided:
            self.game_over()

        if not ob.collided:
            ob.collided = True
            if player.speed_y < 0:
                player.speed_y *= -1
            player.speed_x *= -1

    def show_dialog(self, *args):
        if app.tutorial:
            self.next_level()
            return

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
        Clock.unschedule(self.update_tutorial, 8)
        for ob in self.obstacles:
            ob.anim.cancel(ob)
            self.remove_widget(ob)
        self.obstacles = []
        self.playing = False

    def game_over(self):
        if app.tutorial:
            self.loses += 1
            return

        self.stop_and_clear()
        app.settings['high_status'] = max(app.settings['high_status'], self.status)
        root.current = 'game_over'

    def pause(self):
        self.stop_and_clear()
        self.paused = True
        # noqas bcs pause global variable has the same name as this function
        pause.ids.title.text = str(int(self.status))  # noqa
        pause.ids.title.text_color = app.theme_cls.error_color if self.status < 0 else app.theme_cls.primary_color  # noqa
        pause.ids.subtitle.text = ''  # noqa
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
        if app.tutorial and self.tutorial_step < 9:
            return

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

    def jump(self, horizontal=True):
        if app.tutorial and self.center == game.center:
            Clock.schedule_interval(game.update, game.spf)
            game.playing = True
        if not game.playing:
            return

        self.speed_y = game.height
        if horizontal:
            self.speed_x *= -1


class Menu(Screen):
    def on_enter(self, *args):
        if app.tutorial:
            game.paused = False
        app.tutorial = False


class GameOver(Screen):
    def __init__(self, **kw):
        global game_over
        game_over = self
        super().__init__(**kw)


class Pause(Screen):
    def __init__(self, **kw):
        global pause
        pause = self
        super().__init__(**kw)


class Setting(Screen):
    pass


class Obstacle(Widget):
    collided = BooleanProperty(False)

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
        'high_status': Config.getfloat('identidade', 'high_status'),
        'theme_style': Config.get('identidade', 'theme_style')
    })
    tutorial = BooleanProperty(False)

    def __init__(self, **kwargs):
        self.music = SoundLoader.load('lofi.ogg')
        if self.music:
            self.music.loop = True
            self.music.volume = self.settings['volume'] / 100
            self.music.play()  # noqa pycharm says it is FakeMusic here
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
            elif root.current in ('setting', 'tutorial', 'game_over'):
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
                elif root.current == 'setting':
                    root.current_screen.ids.save_button.dispatch('on_press')
                    root.current_screen.ids.save_button.dispatch('on_release')
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

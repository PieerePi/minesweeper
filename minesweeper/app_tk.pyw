# coding=utf8
"""
由Tkinter实现的扫雷GUI
"""
from __future__ import unicode_literals
import webbrowser

try:
    import tkinter as tk
except ImportError:
    import Tkinter as tk
try:
    from tkinter import messagebox
except ImportError:
    import tkMessageBox as messagebox

from core import Game
from helpers import GameHelpers
from helpers import level_config
import widgets
import static


class App(tk.Frame):
    def __init__(self):
        tk.Frame.__init__(self)
        self.master.title(static.APP_NAME)
        self.master.resizable(False, False)
        self.master.iconbitmap(static.images('mine.ico'))
        self.pack(expand=tk.NO, fill=tk.BOTH)
        self.map_frame = None
        mine_map = level_config.map('primary')
        self._create_map_frame(mine_map)
        self.create_top_menu()

    def create_top_menu(self):
        top = self.winfo_toplevel()
        menu_bar = tk.Menu(top)
        top['menu'] = menu_bar

        game_menu = tk.Menu(menu_bar)
        game_menu.add_command(label='开始', command=self.map_frame.start)
        game_menu.add_command(label='重置', command=self.map_frame.reset)
        game_menu.add_separator()
        game_menu.add_command(label='退出', command=self.exit_app)
        menu_bar.add_cascade(label='游戏', menu=game_menu)

        map_menu = tk.Menu(menu_bar)
        self.level = tk.StringVar()
        self.level.set('primary')
        for level, label in level_config.choices:
            map_menu.add_radiobutton(label=label,
                                     variable=self.level,
                                     value=level,
                                     command=self.select_map_level)
        map_menu.add_separator()
        map_menu.add_command(label='自定义...', command=self.create_custom_map)
        menu_bar.add_cascade(label='地图', menu=map_menu)

        about_menu = tk.Menu(menu_bar)
        about_menu.add_command(label='主页', command=lambda: webbrowser.open_new_tab(static.HOME_URL))
        about_menu.add_command(label='关于...', command=self.show_about_info)
        menu_bar.add_cascade(label='关于', menu=about_menu)

    def select_map_level(self):
        level = self.level.get()
        mine_map = level_config.map(level)
        self._create_map_frame(mine_map)

    def _create_map_frame(self, mine_map):
        if self.map_frame:
            self.map_frame.pack_forget()
        self.map_frame = GameFrame(mine_map)
        self.map_frame.pack(side=tk.TOP)

    def create_custom_map(self):
        params = {
            'width': self.map_frame.game.width,
            'height': self.map_frame.game.height,
            'mine_number': self.map_frame.game.mine_number
        }
        return widgets.MapParamsInputDialog(self, callback=App.get_map_params, initial=params)

    def get_map_params(self, params_dict):
        new_map = GameHelpers.create_from_mine_number(**params_dict)
        self._create_map_frame(new_map)

    def exit_app(self):
        self.quit()

    def show_about_info(self):
        widgets.view_file(self, '关于', static.static_file('project.txt'))


class GameFrame(tk.Frame):
    def __init__(self, mine_map):
        tk.Frame.__init__(self)
        self._create_controller_frame()
        self.map_frame = tk.Frame(self, relief=tk.GROOVE, borderwidth=2)
        self.map_frame.pack(side=tk.TOP, expand=tk.YES, padx=10, pady=10)
        self.ignore_next_button_click = 0
        self.is_left_button_clicked = 0
        self.game = Game(mine_map)
        height, width = mine_map.height, mine_map.width
        self.bt_map = [[None for _ in range(0, width)] for _ in range(0, height)]
        for x in range(0, height):
            for y in range(0, width):
                self.bt_map[x][y] = tk.Button(self.map_frame, text='', width=3, height=1,
                                              command=lambda px=x, py=y: self.left_button_click(px, py))
                self.bt_map[x][y].config(static.style('grid.unknown'))

                def _mark_mine(event, self=self, x=x, y=y):
                    return self.mark_grid_as_mine(event, x, y)

                def _button_released(event, self=self, x=x, y=y):
                    # print(event, x, y)
                    # 对于左右键同时按下，还要过滤掉下一个冗余的事件
                    if self.ignore_next_button_click == 1 and (event.state == 256 or event.state == 1024):
                        # print("ignore", event)
                        self.ignore_next_button_click = 0
                        return
                    # <ButtonRelease-1>
                    if event.state == 256:
                        # 由于tkinter的问题，在这个回调中，无法让当前按钮的状态置为relief=tk.SUNKEN
                        # 所以还是在上面让按钮绑定了事件，在left_button_click中去做实际的动作
                        # 因为按钮绑定的事件处理，已经有格子内部外部动作有效无效的处理，所以这儿一直设置为1
                        self.is_left_button_clicked = 1
                    # 释放的时候，没有移出格子，表示动作有效
                    elif event.x >= 0 and event.x <= 36 and event.y >= 0 and event.y <= 34:
                        # <ButtonRelease-3>
                        if event.state == 1024:
                            self.mark_grid_as_mine(event, x, y)
                        # <ButtonRelease-1> + <ButtonRelease-3>
                        elif event.state == 1280:
                            self.double_button_click(x, y)
                            # 对于左右键同时按下，还要过滤掉下一个冗余的事件
                            self.ignore_next_button_click = 1
                    # 释放的时候，移出了格子，表示动作无效
                    else:
                        if event.state == 1280:
                            # 对于左右键同时按下，还要过滤掉下一个冗余的事件
                            self.ignore_next_button_click = 1

                self.bt_map[x][y].bind('<ButtonRelease-1>', _button_released)
                self.bt_map[x][y].bind('<ButtonRelease-3>', _button_released)
                self.bt_map[x][y].grid(row=x, column=y)
        self._create_info_frame()

    def _create_controller_frame(self):
        self.controller_bar = tk.LabelFrame(self, text='控制', padx=5, pady=5)
        self.controller_bar.pack(side=tk.TOP, fill=tk.X, expand=tk.YES, padx=10, pady=2)
        self.start_bt = tk.Button(self.controller_bar, text='开始', relief=tk.GROOVE, command=self.start)
        self.start_bt.pack(side=tk.LEFT, expand=tk.NO, padx=4)
        self.reset_bt = tk.Button(self.controller_bar, text='重置', relief=tk.GROOVE, command=self.reset)
        self.reset_bt.pack(side=tk.LEFT, expand=tk.NO, padx=4)
        self.map_info_bt = tk.Button(self.controller_bar, text='查看', relief=tk.GROOVE, command=self._show_map_info)
        self.map_info_bt.pack(side=tk.LEFT, expand=tk.NO, padx=4)

    def _show_map_info(self):
        map_info_str = '当前地图大小：%d X %d\n地雷数目：%d' % (self.game.height, self.game.width, self.game.mine_number)
        messagebox.showinfo('当前地图', map_info_str, parent=self)

    def _create_info_frame(self):
        self.info_frame = tk.Frame(self, relief=tk.GROOVE, borderwidth=2)
        self.info_frame.pack(side=tk.TOP, fill=tk.X, expand=tk.YES, padx=10, pady=5)
        self.step_text_label = tk.Label(self.info_frame, text='步数')
        self.step_text_label.pack(side=tk.LEFT, fill=tk.X, expand=tk.NO)
        self.step_count_label = widgets.CounterLabel(self.info_frame, init_value=0, step=1)
        self.step_count_label.pack(side=tk.LEFT, fill=tk.X, expand=tk.NO)
        self.timer_text_label = tk.Label(self.info_frame, text='时间')
        self.timer_text_label.pack(side=tk.LEFT, fill=tk.X, expand=tk.NO)
        self.timer_count_label = widgets.TimerLabel(self.info_frame)
        self.timer_count_label.pack(side=tk.LEFT, fill=tk.X, expand=tk.NO)
        self.flag_text_label = tk.Label(self.info_frame, text='标记')
        self.flag_text_label.pack(side=tk.LEFT, fill=tk.X, expand=tk.NO)
        self.flag_count_label = widgets.CounterLabel(self.info_frame, init_value=0, step=1)
        self.flag_count_label.pack(side=tk.LEFT, fill=tk.X, expand=tk.NO)
        self.msg_label = widgets.MessageLabel(self.info_frame)
        self.msg_label.pack(side=tk.RIGHT)

    def start(self):
        mine_map = GameHelpers.create_from_mine_number(self.game.height, self.game.width, self.game.mine_number)
        self.game = Game(mine_map)
        for x in range(0, self.game.height):
            for y in range(0, self.game.width):
                self.bt_map[x][y]['text'] = ''
        self._draw_map()
        self.step_count_label.set_counter_value()
        self.flag_count_label.set_counter_value()
        self.timer_count_label.reset()
        if not self.timer_count_label.state:
            self.timer_count_label.start_timer()
        self.msg_label.splash('新游戏已就绪')

    def reset(self):
        self.game.reset()
        for x in range(0, self.game.height):
            for y in range(0, self.game.width):
                self.bt_map[x][y]['text'] = ''
        self._draw_map()
        self.step_count_label.set_counter_value()
        self.flag_count_label.set_counter_value()
        self.timer_count_label.reset()
        if not self.timer_count_label.state:
            self.timer_count_label.start_timer()
        self.msg_label.splash('游戏已经重置')

    def double_button_click(self, x, y):
        # 当前按钮没有解开，不能同时左右键按下
        if not self.game.swept_state_map[x][y]:
            return

        # 检查当前按钮数字和周围?的数目是否一致
        curnum = self.game.mine_map.distribute_map[x][y]
        nearquestmark = 0
        scan_step = [(-1, 0), (0, 1), (1, 0), (0, -1), (-1, 1), (-1, -1), (1, 1), (1, -1)]
        for o_x, o_y in scan_step:
            d_x, d_y = x + o_x, y + o_y
            if self.game.mine_map.is_in_map((d_x, d_y)) and not self.game.swept_state_map[d_x][d_y] and self.bt_map[d_x][d_y]['text'] == '?':
                nearquestmark += 1
        if nearquestmark == 0 or curnum != nearquestmark:
            return

        # 逐一解开周围还没有解开并且不为?的按钮
        state = None
        for o_x, o_y in scan_step:
            d_x, d_y = x + o_x, y + o_y
            if self.game.mine_map.is_in_map((d_x, d_y)) and not self.game.swept_state_map[d_x][d_y] and self.bt_map[d_x][d_y]['text'] != '?':
                state = self.game.play((d_x, d_y))
                if state != Game.STATE_PLAY:
                    break

        self.step_count_label.set_counter_value(str(self.game.cur_step))
        self._draw_map()
        if state == Game.STATE_SUCCESS:
            self.timer_count_label.stop_timer()
            self.msg_label.splash('恭喜你，游戏通关了')
            messagebox.showinfo('提示', '恭喜你通关了！', parent=self)
        elif state == Game.STATE_FAIL:
            self.timer_count_label.stop_timer()
            self.msg_label.splash('很遗憾，游戏失败')
            messagebox.showerror('提示', '很遗憾，游戏失败！', parent=self)

    def left_button_click(self, x, y):
        if self.is_left_button_clicked == 1:
            self.is_left_button_clicked = 0
            self.sweep_mine(x, y)

    def sweep_mine(self, x, y):
        if self.game.swept_state_map[x][y]:
            return
        if not self.timer_count_label.state:
            self.timer_count_label.start_timer()
        state = self.game.play((x, y))
        self.step_count_label.set_counter_value(str(self.game.cur_step))
        self._draw_map()
        if state == Game.STATE_SUCCESS:
            self.timer_count_label.stop_timer()
            self.msg_label.splash('恭喜你，游戏通关了')
            messagebox.showinfo('提示', '恭喜你通关了！', parent=self)
        elif state == Game.STATE_FAIL:
            self.timer_count_label.stop_timer()
            self.msg_label.splash('很遗憾，游戏失败')
            messagebox.showerror('提示', '很遗憾，游戏失败！', parent=self)

    def mark_grid_as_mine(self, event, x, y):
        if self.game.state == Game.STATE_PLAY and not self.game.swept_state_map[x][y]:
            cur_text = self.bt_map[x][y]['text']
            if cur_text == '?':
                cur_text = ''
                self.flag_count_label.decrease()
            elif cur_text == '':
                cur_text = '?'
                self.flag_count_label.increase()
            self.bt_map[x][y]['text'] = cur_text

    def _draw_map(self):
        # 重画地图
        for i in range(0, self.game.height):
            for j in range(0, self.game.width):
                if self.game.swept_state_map[i][j]:
                    if self.game.mine_map.is_mine((i, j)):
                        self.bt_map[i][j].config(static.style('grid.mine'))
                    else:
                        tmp = self.game.mine_map.distribute_map[i][j]
                        self.bt_map[i][j].config(static.style('grid.swept', num=tmp))
                else:
                    if self.bt_map[i][j]['text'] == '?':
                        self.bt_map[i][j].config(static.style('grid.marked'))
                    else:
                        self.bt_map[i][j].config(static.style('grid.unknown'))


def main():
    app = App()
    app.mainloop()


if __name__ == '__main__':
    main()

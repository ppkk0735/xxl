import kivy
kivy.require('2.1.0')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.modalview import ModalView
from kivy.graphics import Color, Rectangle, Line
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import ListProperty, NumericProperty, StringProperty
import random
import copy
from functools import partial

# 尝试导入 PIL（用于图片识别）
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# 颜色配置 (6种)
COLOR_HEX = {
    0: '#FF4444', 1: '#FF8C00', 2: '#FFD700',
    3: '#32CD32', 4: '#1E90FF', 5: '#9370DB'
}
COLOR_RGB = {
    0: (255,68,68), 1: (255,140,0), 2: (255,215,0),
    3: (50,205,50), 4: (30,144,255), 5: (147,112,219)
}
COLOR_NAMES = {0:'红',1:'橙',2:'黄',3:'绿',4:'蓝',5:'紫'}

# ------------------- 游戏核心逻辑 (完全移植) -------------------
class MatchGame:
    def __init__(self, rows=6, cols=6, num_types=6):
        self.rows = rows
        self.cols = cols
        self.num_types = num_types
        self.board = []
        self.score = 0
        self.generate_board()

    def generate_board(self):
        self.board = [[0]*self.cols for _ in range(self.rows)]
        for r in range(self.rows):
            for c in range(self.cols):
                if c>=2 and self.board[r][c-1]==self.board[r][c-2]:
                    forbidden={self.board[r][c-1]}
                    if r>=2 and self.board[r-1][c]==self.board[r-2][c]:
                        forbidden.add(self.board[r-1][c])
                    available=[t for t in range(self.num_types) if t not in forbidden]
                    self.board[r][c]=random.choice(available) if available else 0
                else:
                    if r>=2 and self.board[r-1][c]==self.board[r-2][c]:
                        forbidden={self.board[r-1][c]}
                        if c>=2 and self.board[r][c-1]==self.board[r][c-2]:
                            forbidden.add(self.board[r][c-1])
                        available=[t for t in range(self.num_types) if t not in forbidden]
                        self.board[r][c]=random.choice(available) if available else 0
                    else:
                        self.board[r][c]=random.randint(0,self.num_types-1)
        self.score=0

    def set_board_from_list(self, board_list):
        if len(board_list)!=self.rows or len(board_list[0])!=self.cols:
            return False
        self.board=board_list
        self.score=0
        return True

    def find_matches(self, board):
        matched=set()
        rows,cols=len(board),len(board[0])
        for r in range(rows):
            for c in range(cols-2):
                if board[r][c]==board[r][c+1]==board[r][c+2] and board[r][c]!=-1:
                    end=c+2
                    while end+1<cols and board[r][end+1]==board[r][c]:
                        end+=1
                    for k in range(c,end+1):
                        matched.add((r,k))
        for c in range(cols):
            for r in range(rows-2):
                if board[r][c]==board[r+1][c]==board[r+2][c] and board[r][c]!=-1:
                    end=r+2
                    while end+1<rows and board[end+1][c]==board[r][c]:
                        end+=1
                    for k in range(r,end+1):
                        matched.add((k,c))
        return matched

    def apply_gravity(self, board):
        rows,cols=len(board),len(board[0])
        moved=False
        for c in range(cols):
            write_row=rows-1
            for r in range(rows-1,-1,-1):
                if board[r][c]!=-1:
                    if r!=write_row:
                        board[write_row][c]=board[r][c]
                        board[r][c]=-1
                        moved=True
                    write_row-=1
            for r in range(write_row,-1,-1):
                board[r][c]=-1
        return moved

    def simulate_swap(self, board, r1,c1,r2,c2):
        sim_board=copy.deepcopy(board)
        sim_board[r1][c1],sim_board[r2][c2]=sim_board[r2][c2],sim_board[r1][c1]
        total_score=total_eliminated=chain=0
        while True:
            matches=self.find_matches(sim_board)
            if not matches:
                break
            chain+=1
            eliminated=len(matches)
            total_eliminated+=eliminated
            coefficient=1+(chain-1)*0.1
            total_score+=eliminated*coefficient
            for r,c in matches:
                sim_board[r][c]=-1
            self.apply_gravity(sim_board)
        return total_score,total_eliminated,chain

    def find_best_move(self):
        best_score=-1
        best_move=None
        best_eliminated=best_chain=0
        for r in range(self.rows):
            for c in range(self.cols):
                if c+1<self.cols and self.board[r][c]!=self.board[r][c+1]:
                    score,eliminated,chain=self.simulate_swap(self.board,r,c,r,c+1)
                    if score>best_score:
                        best_score=score
                        best_move=(r,c,r,c+1)
                        best_eliminated=eliminated
                        best_chain=chain
                if r+1<self.rows and self.board[r][c]!=self.board[r+1][c]:
                    score,eliminated,chain=self.simulate_swap(self.board,r,c,r+1,c)
                    if score>best_score:
                        best_score=score
                        best_move=(r,c,r+1,c)
                        best_eliminated=eliminated
                        best_chain=chain
        if best_move is None:
            return None,0,0,0
        return best_move,best_score,best_eliminated,best_chain

    def execute_move(self, r1,c1,r2,c2):
        self.board[r1][c1],self.board[r2][c2]=self.board[r2][c2],self.board[r1][c1]
        total_score=total_eliminated=chain=0
        col_stats={c:{'count':0,'score':0.0} for c in range(self.cols)}
        while True:
            matches=self.find_matches(self.board)
            if not matches:
                break
            chain+=1
            eliminated=len(matches)
            total_eliminated+=eliminated
            coefficient=1+(chain-1)*0.1
            total_score+=eliminated*coefficient
            for r,c in matches:
                col_stats[c]['count']+=1
                col_stats[c]['score']+=coefficient
            for r,c in matches:
                self.board[r][c]=-1
            self.apply_gravity(self.board)
        self.score+=total_score
        return total_score,total_eliminated,chain,col_stats

    def has_valid_move(self):
        best_move,_,_,_=self.find_best_move()
        return best_move is not None

# ------------------- 自定义网格控件 (用于绘制彩色方块) -------------------
class BoardGrid(GridLayout):
    def __init__(self, game, **kwargs):
        super(BoardGrid, self).__init__(**kwargs)
        self.game = game
        self.cols = self.game.cols
        self.rows = self.game.rows
        self.cell_size = 60  # 像素，可在kv中调整
        self.highlighted = []  # [(r,c), ...]
        self.build_grid()

    def build_grid(self):
        self.clear_widgets()
        board = self.game.board
        for r in range(self.rows):
            for c in range(self.cols):
                btn = Button(
                    text=COLOR_NAMES.get(board[r][c], '') if board[r][c] != -1 else '',
                    background_color=self.get_color(board[r][c]),
                    color=(1,1,1,1),
                    font_size='12sp',
                    size_hint=(None, None),
                    size=(self.cell_size, self.cell_size),
                )
                btn.r = r
                btn.c = c
                self.add_widget(btn)
        self.apply_highlights()

    def get_color(self, idx):
        if idx == -1:
            return (0.9,0.9,0.9,1)  # 空位灰色
        hex_color = COLOR_HEX.get(idx, '#CCCCCC')
        # 转换hex到rgb 0-1
        hex_color = hex_color.lstrip('#')
        r,g,b = tuple(int(hex_color[i:i+2], 16)/255.0 for i in (0,2,4))
        return (r,g,b,1)

    def apply_highlights(self):
        # 遍历所有子控件（Button），根据其r,c判断是否高亮
        for child in self.children:
            if hasattr(child, 'r') and hasattr(child, 'c'):
                if (child.r, child.c) in self.highlighted:
                    child.background_color = (1,0.84,0,1)  # 金色
                    # 添加星标（文字）
                    child.text = '⭐' + child.text
                else:
                    # 恢复
                    idx = self.game.board[child.r][child.c]
                    child.background_color = self.get_color(idx)
                    child.text = COLOR_NAMES.get(idx, '') if idx != -1 else ''

    def update_board(self):
        self.build_grid()

    def set_highlight(self, positions):
        self.highlighted = positions
        self.apply_highlights()

    def clear_highlight(self):
        self.highlighted = []
        self.apply_highlights()

# ------------------- 主界面 -------------------
class MatchGameWidget(BoxLayout):
    def __init__(self, **kwargs):
        super(MatchGameWidget, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 10
        self.spacing = 10

        self.game = MatchGame(6,6,6)
        self.best_move_info = None

        # 标题
        self.title_label = Label(text='✨ 消消乐最佳方案 ✨', font_size='20sp', size_hint_y=None, height=50)
        self.add_widget(self.title_label)

        # 棋盘网格（使用自定义控件）
        self.board_grid = BoardGrid(self.game, size_hint=(1, None), height=400)
        self.add_widget(self.board_grid)

        # 信息显示区域（滚动文本框）
        self.info_text = TextInput(
            text='点击 "生成盘面" 开始',
            readonly=True,
            multiline=True,
            font_size='14sp',
            size_hint_y=None,
            height=150,
            background_color=(0.95,0.95,0.95,1)
        )
        self.add_widget(self.info_text)

        # 按钮布局
        btn_layout = BoxLayout(size_hint_y=None, height=60, spacing=5)
        self.btn_generate = Button(text='🔄 生成', on_press=self.generate_board)
        self.btn_find = Button(text='🔍 最佳', on_press=self.find_best)
        self.btn_execute = Button(text='▶ 执行', on_press=self.execute_best)
        self.btn_import = Button(text='📷 导入', on_press=self.import_image)
        btn_layout.add_widget(self.btn_generate)
        btn_layout.add_widget(self.btn_find)
        btn_layout.add_widget(self.btn_execute)
        btn_layout.add_widget(self.btn_import)
        self.add_widget(btn_layout)

        # 状态栏
        self.status_label = Label(text='💡 提示：生成盘面或导入图片', font_size='14sp', size_hint_y=None, height=30)
        self.add_widget(self.status_label)

        # 初始显示
        self.update_info('欢迎！点击 "生成" 开始新盘面。')

    def update_info(self, text):
        self.info_text.text = text

    def set_status(self, text):
        self.status_label.text = text

    def generate_board(self, instance):
        self.game.generate_board()
        self.board_grid.update_board()
        self.board_grid.clear_highlight()
        self.best_move_info = None
        self.update_info('🎮 新盘面已生成！点击 "最佳" 求解。\n得分：每块1分×递增系数(1.0,1.1,1.2...)')
        self.set_status('✅ 新盘面已生成')

    def find_best(self, instance):
        best_move, score, eliminated, chain = self.game.find_best_move()
        if best_move is None:
            self.update_info('❌ 没有可用的移动！请重新生成。')
            self.set_status('❌ 无可用移动')
            self.board_grid.clear_highlight()
            return
        r1,c1,r2,c2 = best_move
        self.board_grid.set_highlight([(r1,c1),(r2,c2)])
        self.best_move_info = (r1,c1,r2,c2,score,eliminated,chain)
        info = (f'🏆 最佳方案\n'
                f'交换: ({r1+1},{c1+1}) ↔ ({r2+1},{c2+1})\n'
                f'预期得分: {score:.1f}  消除: {eliminated}块  连锁: {chain}轮\n'
                f'点击 "执行" 查看每列详情')
        self.update_info(info)
        self.set_status(f'🎯 交换({r1+1},{c1+1})和({r2+1},{c2+1})')

    def execute_best(self, instance):
        if self.best_move_info is None:
            self.update_info('⚠️ 请先点击 "最佳" 寻找方案。')
            return
        r1,c1,r2,c2,_,_,_ = self.best_move_info
        total_score,total_elim,chain,col_stats = self.game.execute_move(r1,c1,r2,c2)
        self.board_grid.update_board()
        self.board_grid.clear_highlight()
        self.best_move_info = None

        info = f'🎉 执行完成！\n总得分: {total_score:.1f}  总消除: {total_elim}块  连锁: {chain}轮\n'
        info += '各列统计 (列号: 消除块数, 得分):\n'
        for c in range(self.game.cols):
            if col_stats[c]['count'] > 0:
                info += f'  第{c+1}列: {col_stats[c]["count"]}块, {col_stats[c]["score"]:.1f}分\n'
        info += f'累计总分: {self.game.score:.1f}'
        self.update_info(info)
        self.set_status(f'✅ 完成！总得分 {self.game.score:.1f}')
        if not self.game.has_valid_move():
            self.update_info(self.info_text.text + '\n⚠️ 无可用移动，建议重新生成。')
            self.set_status('⚠️ 无可用移动')

    def import_image(self, instance):
        if not PIL_AVAILABLE:
            self.update_info('❌ 未安装Pillow库，无法识别图片。\n请安装: pip install Pillow')
            return

        # 使用文件选择器（Android上会调用系统文件选择器）
        from kivy.uix.filechooser import FileChooserListView
        from kivy.uix.popup import Popup
        from kivy.uix.boxlayout import BoxLayout

        content = BoxLayout(orientation='vertical')
        filechooser = FileChooserListView()
        content.add_widget(filechooser)
        btn_layout = BoxLayout(size_hint_y=None, height=50)
        confirm = Button(text='确认')
        cancel = Button(text='取消')
        btn_layout.add_widget(confirm)
        btn_layout.add_widget(cancel)
        content.add_widget(btn_layout)

        popup = Popup(title='选择图片', content=content, size_hint=(0.9,0.9))
        def on_confirm(btn):
            if filechooser.selection:
                path = filechooser.selection[0]
                popup.dismiss()
                self.process_image(path)
        def on_cancel(btn):
            popup.dismiss()
        confirm.bind(on_press=on_confirm)
        cancel.bind(on_press=on_cancel)
        popup.open()

    def process_image(self, path):
        try:
            img = Image.open(path).convert('RGB')
        except Exception as e:
            self.update_info(f'❌ 无法打开图片: {e}')
            return

        sample = 20
        target_w = self.game.cols * sample
        target_h = self.game.rows * sample
        img_resized = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
        board = []
        for r in range(self.game.rows):
            row = []
            for c in range(self.game.cols):
                x = c * sample + sample//2
                y = r * sample + sample//2
                box = (x-5, y-5, x+5, y+5)
                region = img_resized.crop(box)
                pixels = region.getdata()
                avg_r = sum(p[0] for p in pixels)//len(pixels)
                avg_g = sum(p[1] for p in pixels)//len(pixels)
                avg_b = sum(p[2] for p in pixels)//len(pixels)
                best_idx = min(COLOR_RGB.keys(),
                               key=lambda idx: (avg_r-COLOR_RGB[idx][0])**2 +
                                               (avg_g-COLOR_RGB[idx][1])**2 +
                                               (avg_b-COLOR_RGB[idx][2])**2)
                row.append(best_idx)
            board.append(row)

        if self.game.set_board_from_list(board):
            self.board_grid.update_board()
            self.board_grid.clear_highlight()
            self.best_move_info = None
            self.update_info('📷 图片识别完成！盘面已加载。')
            self.set_status('✅ 导入成功，可点击 "最佳"')
        else:
            self.update_info('❌ 识别结果与盘面尺寸不匹配！')

# ------------------- 应用类 -------------------
class MatchApp(App):
    def build(self):
        # 设置窗口默认大小（手机屏幕自适应）
        Window.size = (480, 720)
        return MatchGameWidget()

if __name__ == '__main__':
    MatchApp().run()

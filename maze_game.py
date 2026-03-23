# -*- coding: utf-8 -*-
"""
@file:    maze_game.py
@brief:   [贪吃蛇小游戏，可以连接单片机]
@author:  [小浩同学/GitHub：embuxpie]
@version: 0.1.0
@license: MIT  
@repo:    https://github.com/embuxpie/wangpeng_sensor
@date:    2026-02-04
"""
import pygame
import sys
import serial
import threading
from pygame.locals import *
from serial.tools import list_ports

# 初始化pygame
pygame.init()

# 游戏常量
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 1000
CELL_SIZE = 40
FPS = 60

# 颜色定义
BACKGROUND = (240, 240, 240)  # 浅灰色背景
MAZE_COLOR = (173, 216, 230)  # 浅蓝色迷宫墙
WALL_COLOR = (100, 150, 200)  # 迷宫墙边框
PATH_COLOR = (255, 255, 255)  # 白色通道
PLAYER_COLOR = (255, 0, 0)    # 红色玩家
START_COLOR = (255, 100, 100)  # 浅红色起点
GOAL_COLOR = (0, 200, 0)      # 绿色终点
INTERMEDIATE_COLOR = (255, 200, 0)  # 黄色中间点
TEXT_COLOR = (50, 50, 50)     # 文本颜色
INFO_BG = (220, 220, 220)     # 信息背景色
SERIAL_COLOR = (100, 100, 200)  # 串口状态颜色

# 迷宫地图 (0=墙, 1=通道, 2=起点, 3=终点, 4=中间点)
maze_map = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 2, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0],
    [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0],
    [0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0],
    [0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0],
    [0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
    [0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
    [0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 0],
    [0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0],
    [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0],
    [0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0],
    [0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 0],
    [0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 1, 0],
    [0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 1, 0],
    [0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0],
    [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 4, 1, 1, 1, 1, 1, 1, 4, 1, 0],
    [0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0],
    [0, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0],
    [0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 3, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
]

# 计算迷宫在屏幕上的位置
MAZE_WIDTH = len(maze_map[0]) * CELL_SIZE
MAZE_HEIGHT = len(maze_map) * CELL_SIZE
MAZE_X = (WINDOW_WIDTH - MAZE_WIDTH) // 2
MAZE_Y = (WINDOW_HEIGHT - MAZE_HEIGHT) // 2 + 60  # 向下移动，为顶部信息栏留出空间

class SerialController:
    def __init__(self, game):
        self.game = game
        self.ser = None
        self.serial_thread = None
        self.running = False
        self.connected = False
        self.last_received = "无数据"
        
    def connect(self, port, baudrate=115200):
        """连接串口"""
        try:
            if self.ser and self.ser.is_open:
                self.ser.close()
                
            self.ser = serial.Serial(port, baudrate, timeout=0.1)
            self.connected = True
            self.running = True
            
            # 启动串口读取线程
            self.serial_thread = threading.Thread(target=self.read_serial)
            self.serial_thread.daemon = True
            self.serial_thread.start()
            
            return True
        except Exception as e:
            print(f"串口连接失败: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """断开串口连接"""
        self.running = False
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.connected = False
    
    def read_serial(self):
        """读取串口数据"""
        while self.running and self.connected:
            try:
                if self.ser and self.ser.in_waiting > 0:
                    data = self.ser.readline().decode('utf-8').strip()
                    if data:
                        self.last_received = data
                        self.process_serial_data(data)
            except Exception as e:
                print(f"串口读取错误: {e}")
                break
    
    def process_serial_data(self, data):
        """处理串口接收到的数据"""
        # 根据单片机发送的数字控制游戏
        # 2=上, 4=左, 6=右, 8=下
        if not self.game.game_over:
            if data == '2':  # 上
                self.game.player.move(0, -1)
            elif data == '4':  # 左
                self.game.player.move(-1, 0)
            elif data == '6':  # 右
                self.game.player.move(1, 0)
            elif data == '8':  # 下
                self.game.player.move(0, 1)
            
            # 检查是否获胜
            if self.game.player.check_win():
                self.game.win = True
                self.game.game_over = True

class Player:
    def __init__(self, maze):
        self.maze = maze
        self.find_start_position()
        self.moves = 0
        self.collected_points = 0
        self.total_intermediate_points = self.count_intermediate_points()
        self.start_time = pygame.time.get_ticks()
        self.playing_time = 0
        
    def find_start_position(self):
        """在迷宫中找到起点位置"""
        for y, row in enumerate(self.maze):
            for x, cell in enumerate(row):
                if cell == 2:  # 起点
                    self.start_x = x
                    self.start_y = y
                    self.x = x
                    self.y = y
                    return
    
    def reset(self):
        """重置玩家到起点"""
        self.x = self.start_x
        self.y = self.start_y
        self.moves = 0
        self.collected_points = 0
        self.start_time = pygame.time.get_ticks()
        self.playing_time = 0
    
    def count_intermediate_points(self):
        """计算迷宫中的中间点数量"""
        count = 0
        for row in self.maze:
            for cell in row:
                if cell == 4:  # 中间点
                    count += 1
        return count
    
    def move(self, dx, dy):
        """尝试移动玩家"""
        new_x = self.x + dx
        new_y = self.y + dy
        
        # 检查是否在迷宫范围内
        if 0 <= new_y < len(self.maze) and 0 <= new_x < len(self.maze[0]):
            # 检查目标位置是否是墙
            if self.maze[new_y][new_x] != 0:
                # 记录移动
                self.moves += 1
                
                # 检查是否收集到中间点
                if self.maze[new_y][new_x] == 4:
                    self.collected_points += 1
                    # 移除中间点（将其设为通道）
                    self.maze[new_y][new_x] = 1
                
                # 更新玩家位置
                self.x = new_x
                self.y = new_y
                return True
        return False
    
    def update_time(self):
        """更新游戏时间"""
        if not self.check_win():
            self.playing_time = (pygame.time.get_ticks() - self.start_time) // 1000
    
    def check_win(self):
        """检查玩家是否到达终点"""
        return self.maze[self.y][self.x] == 3

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("走迷宫游戏 - 支持单片机控制")
        
        # 尝试加载中文字体
        try:
            font_paths = [
                "C:/Windows/Fonts/simhei.ttf",  # 黑体
                "C:/Windows/Fonts/msyh.ttc",   # 微软雅黑
                "C:/Windows/Fonts/simsun.ttc", # 宋体
            ]
            
            self.font = None
            for font_path in font_paths:
                try:
                    self.font = pygame.font.Font(font_path, 36)
                    self.small_font = pygame.font.Font(font_path, 24)
                    print(f"成功加载字体: {font_path}")
                    break
                except:
                    continue
            
            if self.font is None:
                self.font = pygame.font.SysFont(None, 36)
                self.small_font = pygame.font.SysFont(None, 24)
                print("使用默认字体，可能无法显示中文")
        except:
            self.font = pygame.font.SysFont(None, 36)
            self.small_font = pygame.font.SysFont(None, 24)
            print("字体加载失败，使用默认字体")
        
        self.clock = pygame.time.Clock()
        
        # 初始化串口控制器
        self.serial_controller = SerialController(self)
        
        # 获取可用串口
        self.available_ports = self.get_available_ports()
        self.selected_port = "COM3"
        
        self.reset_game()

        # 显示启动弹窗
        self.show_startup_popup()
    
    def show_startup_popup(self):
        """显示启动信息弹窗"""
        popup_width = 600
        popup_height = 700
        popup_x = (WINDOW_WIDTH - popup_width) // 2
        popup_y = (WINDOW_HEIGHT - popup_height) // 2
        
        # 弹窗颜色定义
        POPUP_BG = (255, 253, 240)  # 米白色背景
        TITLE_COLOR = (30, 30, 120)  # 深蓝色标题
        TEXT_COLOR = (50, 50, 50)    # 正文深灰色
        HIGHLIGHT_COLOR = (200, 50, 50)  # 高亮色
        BUTTON_COLOR = (70, 130, 180)    # 按钮蓝色
        BUTTON_HOVER_COLOR = (100, 160, 210)  # 按钮悬停色
        
        # 确定按钮的矩形区域
        button_width, button_height = 160, 55
        button_x = popup_x + (popup_width - button_width) // 2
        button_y = popup_y + popup_height - button_height - 30
        button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
        
        button_hovered = False
        popup_active = True
        
        # 弹窗主循环
        while popup_active:
            mouse_pos = pygame.mouse.get_pos()
            button_hovered = button_rect.collidepoint(mouse_pos)
            
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == MOUSEBUTTONDOWN:
                    if event.button == 1:  # 左键点击
                        if button_rect.collidepoint(mouse_pos):
                            popup_active = False  # 点击确定，关闭弹窗
                elif event.type == KEYDOWN:
                    if event.key in (K_RETURN, K_SPACE, K_ESCAPE, K_KP_ENTER):
                        popup_active = False  # 按回车、空格、ESC或小键盘回车也可关闭
            
            # 绘制弹窗背景和边框
            pygame.draw.rect(self.screen, POPUP_BG, (popup_x, popup_y, popup_width, popup_height))
            pygame.draw.rect(self.screen, (180, 180, 180), (popup_x, popup_y, popup_width, popup_height), 4)
            
            # 绘制标题
            title_text = self.font.render("迷宫游戏 - 启动信息", True, TITLE_COLOR)
            self.screen.blit(title_text, (popup_x + (popup_width - title_text.get_width()) // 2, popup_y + 30))
            
            # 绘制作者和项目信息
            info_lines = [
                "欢迎使用迷宫游戏！",
                "",
                f"作者: 小浩同学 (GitHub: embuxpie)",
                f"版本: 0.1.0",
                f"发布日期: 2026-02-04",
                f"许可证: MIT License",
                "",
                "项目仓库:",
                "https://github.com/embuxpie/wangpeng_sensor",
                "",
                "游戏说明:",
                "• 键盘方向键或单片机控制角色移动",
                "• 红色方块为玩家，绿色方块为终点",
                "• 收集所有黄色方块以获得更高分数",
                "• 按 R 键随时重新开始游戏"
            ]
            
            line_height = 32
            for i, line in enumerate(info_lines):
                if "https://github.com" in line:
                    # 项目地址用特殊颜色强调
                    text_surface = self.small_font.render(line, True, (0, 100, 200))
                elif line.startswith("•"):
                    # 游戏说明项
                    text_surface = self.small_font.render(line, True, (80, 80, 80))
                elif "作者:" in line or "版本:" in line:
                    # 关键信息用深色
                    text_surface = self.small_font.render(line, True, (40, 40, 40))
                else:
                    text_surface = self.small_font.render(line, True, TEXT_COLOR)
                
                self.screen.blit(text_surface, (popup_x + 40, popup_y + 90 + i * line_height))
            
            # 绘制分隔线
            pygame.draw.line(self.screen, (200, 200, 200), 
                           (popup_x + 30, button_y - 25), 
                           (popup_x + popup_width - 30, button_y - 25), 2)
            
            # 绘制确定按钮
            current_button_color = BUTTON_HOVER_COLOR if button_hovered else BUTTON_COLOR
            pygame.draw.rect(self.screen, current_button_color, button_rect, border_radius=8)
            pygame.draw.rect(self.screen, (40, 40, 40), button_rect, 2, border_radius=8)
            
            button_text = self.small_font.render("确定 (Enter)", True, (255, 255, 255))
            self.screen.blit(button_text, (button_rect.centerx - button_text.get_width() // 2, 
                                         button_rect.centery - button_text.get_height() // 2))
            
            # 底部提示
            hint_text = self.small_font.render("点击确定按钮或按 Enter 键开始游戏", True, (120, 120, 120))
            self.screen.blit(hint_text, (popup_x + (popup_width - hint_text.get_width()) // 2, popup_y + popup_height - 25))
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        # 弹窗关闭后，清屏回到默认背景色，为游戏主界面做准备
        self.screen.fill(BACKGROUND)
        pygame.display.flip()
    
    def get_available_ports(self):
        """获取可用串口列表"""
        ports = list_ports.comports()
        return [port.device for port in ports]
    
    def connect_serial(self):
        """连接串口"""
        if self.selected_port:
            success = self.serial_controller.connect(self.selected_port)
            return success
        return False
    
    def disconnect_serial(self):
        """断开串口连接"""
        self.serial_controller.disconnect()
    
    def reset_game(self):
        """重置游戏状态"""
        # 重新加载迷宫地图
        self.original_maze = [
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 2, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0],
            [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0],
            [0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0],
            [0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0],
            [0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
            [0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
            [0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 0],
            [0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0],
            [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0],
            [0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0],
            [0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 0],
            [0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 1, 0],
            [0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 1, 0],
            [0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0],
            [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 4, 1, 1, 1, 1, 1, 1, 4, 1, 0],
            [0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0],
            [0, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0],
            [0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 3, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        ]
        
        # 创建迷宫副本
        self.maze = [row[:] for row in self.original_maze]
        self.player = Player(self.maze)
        self.game_over = False
        self.win = False
    
    def handle_events(self):
        """处理游戏事件"""
        for event in pygame.event.get():
            if event.type == QUIT:
                if self.serial_controller.connected:
                    self.serial_controller.disconnect()
                pygame.quit()
                sys.exit()
                
            if event.type == KEYDOWN:
                if event.key == K_r:  # 按R键重新开始
                    self.reset_game()
                    return
                    
                if not self.game_over:
                    if event.key == K_UP:
                        self.player.move(0, -1)
                    elif event.key == K_DOWN:
                        self.player.move(0, 1)
                    elif event.key == K_LEFT:
                        self.player.move(-1, 0)
                    elif event.key == K_RIGHT:
                        self.player.move(1, 0)
                    
                    # 检查是否获胜
                    if self.player.check_win():
                        self.win = True
                        self.game_over = True
    
    def draw_maze(self):
        """绘制迷宫"""
        # 绘制迷宫背景
        pygame.draw.rect(self.screen, MAZE_COLOR, 
                        (MAZE_X, MAZE_Y, MAZE_WIDTH, MAZE_HEIGHT))
        
        # 绘制迷宫单元格
        for y, row in enumerate(self.maze):
            for x, cell in enumerate(row):
                rect_x = MAZE_X + x * CELL_SIZE
                rect_y = MAZE_Y + y * CELL_SIZE
                
                if cell == 0:  # 墙
                    pygame.draw.rect(self.screen, WALL_COLOR, 
                                   (rect_x, rect_y, CELL_SIZE, CELL_SIZE))
                elif cell == 1:  # 通道
                    pygame.draw.rect(self.screen, PATH_COLOR, 
                                   (rect_x, rect_y, CELL_SIZE, CELL_SIZE))
                elif cell == 2:  # 起点 - 使用浅红色
                    pygame.draw.rect(self.screen, PATH_COLOR, 
                                   (rect_x, rect_y, CELL_SIZE, CELL_SIZE))
                    # 起点标记
                    pygame.draw.rect(self.screen, START_COLOR, 
                                   (rect_x + 5, rect_y + 5, CELL_SIZE - 10, CELL_SIZE - 10))
                elif cell == 3:  # 终点 - 使用绿色
                    pygame.draw.rect(self.screen, PATH_COLOR, 
                                   (rect_x, rect_y, CELL_SIZE, CELL_SIZE))
                    # 终点标记
                    pygame.draw.rect(self.screen, GOAL_COLOR, 
                                   (rect_x + 5, rect_y + 5, CELL_SIZE - 10, CELL_SIZE - 10))
                elif cell == 4:  # 中间点 - 使用黄色
                    pygame.draw.rect(self.screen, PATH_COLOR, 
                                   (rect_x, rect_y, CELL_SIZE, CELL_SIZE))
                    # 中间点标记
                    pygame.draw.rect(self.screen, INTERMEDIATE_COLOR, 
                                   (rect_x + 8, rect_y + 8, CELL_SIZE - 16, CELL_SIZE - 16))
        
        # 绘制网格线
        for x in range(len(self.maze[0]) + 1):
            pygame.draw.line(self.screen, WALL_COLOR, 
                           (MAZE_X + x * CELL_SIZE, MAZE_Y), 
                           (MAZE_X + x * CELL_SIZE, MAZE_Y + MAZE_HEIGHT), 2)
        
        for y in range(len(self.maze) + 1):
            pygame.draw.line(self.screen, WALL_COLOR, 
                           (MAZE_X, MAZE_Y + y * CELL_SIZE), 
                           (MAZE_X + MAZE_WIDTH, MAZE_Y + y * CELL_SIZE), 2)
    
    def draw_player(self):
        """绘制玩家"""
        player_x = MAZE_X + self.player.x * CELL_SIZE
        player_y = MAZE_Y + self.player.y * CELL_SIZE
        
        # 绘制玩家（红色方块）
        pygame.draw.rect(self.screen, PLAYER_COLOR, 
                        (player_x + 5, player_y + 5, CELL_SIZE - 10, CELL_SIZE - 10))
        
        # 在玩家方块上添加一个白色边框使其更明显
        pygame.draw.rect(self.screen, (255, 255, 255), 
                        (player_x + 5, player_y + 5, CELL_SIZE - 10, CELL_SIZE - 10), 2)
    
    def draw_info_panel(self):
        """绘制顶部信息面板"""
        # 绘制信息面板背景
        info_rect = pygame.Rect(0, 0, WINDOW_WIDTH, 80)
        pygame.draw.rect(self.screen, INFO_BG, info_rect)
        pygame.draw.line(self.screen, (150, 150, 150), (0, 80), (WINDOW_WIDTH, 80), 2)
        
        # 游戏标题
        title_text = self.font.render("走迷宫游戏 - 支持单片机控制（小浩）", True, TEXT_COLOR)
        self.screen.blit(title_text, (WINDOW_WIDTH // 2 - title_text.get_width() // 2, 10))
        
        # 控制说明
        control_text = self.small_font.render("键盘: ↑↓←→ 移动, R键重新开始 | 单片机: 2=上, 4=左, 6=右, 8=下", True, TEXT_COLOR)
        self.screen.blit(control_text, (WINDOW_WIDTH // 2 - control_text.get_width() // 2, 45))
        
        # 游戏信息
        time_text = self.small_font.render(f"时间: {self.player.playing_time:03d}", True, TEXT_COLOR)
        moves_text = self.small_font.render(f"步数: {self.player.moves:03d}", True, TEXT_COLOR)
        points_text = self.small_font.render(f"收集: {self.player.collected_points:01d}/{self.player.total_intermediate_points:01d}", True, TEXT_COLOR)
        
        # 左侧信息
        self.screen.blit(time_text, (20, 20))
        self.screen.blit(moves_text, (20, 45))
        
        # 右侧信息
        self.screen.blit(points_text, (WINDOW_WIDTH - points_text.get_width() - 20, 45))
    
    def draw_serial_info(self):
        """绘制串口信息"""
        # 串口状态
        status = "已连接" if self.serial_controller.connected else "未连接"
        status_color = (0, 150, 0) if self.serial_controller.connected else (150, 0, 0)
        
        status_text = self.small_font.render(f"串口状态: {status}", True, status_color)
        self.screen.blit(status_text, (WINDOW_WIDTH - status_text.get_width() - 20, 20))
        
        # 最后接收到的数据
        data_text = self.small_font.render(f"最后接收: {self.serial_controller.last_received}", True, SERIAL_COLOR)
        self.screen.blit(data_text, (WINDOW_WIDTH - data_text.get_width() - 20, 70))
    
    def draw_game_over(self):
        """绘制游戏结束画面"""
        if self.game_over and self.win:
            # 半透明覆盖层
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))  # 半透明黑色
            self.screen.blit(overlay, (0, 0))
            
            # 胜利消息
            win_text = self.font.render("恭喜！你成功走出了迷宫！", True, (255, 255, 255))
            self.screen.blit(win_text, (WINDOW_WIDTH // 2 - win_text.get_width() // 2, WINDOW_HEIGHT // 2 - 50))
            
            # 重新开始提示
            restart_text = self.small_font.render("按 R 键重新开始游戏", True, (255, 255, 255))
            self.screen.blit(restart_text, (WINDOW_WIDTH // 2 - restart_text.get_width() // 2, WINDOW_HEIGHT // 2 + 10))
    
    def run(self):
        """运行游戏主循环"""
        # 尝试自动连接串口
        if self.available_ports:
            print(f"尝试连接串口: {self.selected_port}")
            if self.connect_serial():
                print("串口连接成功！")
            else:
                print("串口连接失败，请检查连接")
        
        while True:
            self.handle_events()
            
            # 更新游戏时间
            self.player.update_time()
            
            # 填充背景
            self.screen.fill(BACKGROUND)
            
            # 绘制信息面板
            self.draw_info_panel()
            
            # 绘制串口信息
            self.draw_serial_info()
            
            # 绘制迷宫
            self.draw_maze()
            
            # 绘制玩家
            self.draw_player()
            
            # 绘制游戏结束画面
            if self.game_over:
                self.draw_game_over()
            
            # 更新屏幕
            pygame.display.flip()
            self.clock.tick(FPS)

def main():
    """主函数"""
    print("游戏开始！")
    print("控制方式:")
    print("  1. 键盘方向键控制角色移动")
    print("  2. 单片机矩阵按键: 2=上, 4=左, 6=右, 8=下")
    print("  3. 按R键可以重新开始游戏")
    print("红色方块是玩家，绿色方块是终点")
    print("黄色方块是中间点，收集它们可以获得更高分数")
    print("祝你游戏愉快！")
    
    game = Game()
    game.run()

if __name__ == "__main__":
    main()
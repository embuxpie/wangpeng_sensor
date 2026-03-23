import pygame
import sys
import random
import serial
import threading
from pygame.locals import *
from serial.tools import list_ports

# 初始化pygame
pygame.init()

# 游戏常量
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 900
BLOCK_SIZE = 30
GRID_WIDTH = 10
GRID_HEIGHT = 20
GRID_OFFSET_X = (SCREEN_WIDTH - GRID_WIDTH * BLOCK_SIZE) // 2
GRID_OFFSET_Y = 50
FPS = 60

# 颜色定义
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)

# 方块形状定义
SHAPES = [
    [[1, 1, 1, 1]],  # I
    [[1, 1], [1, 1]],  # O
    [[0, 1, 0], [1, 1, 1]],  # T
    [[0, 1, 1], [1, 1, 0]],  # S
    [[1, 1, 0], [0, 1, 1]],  # Z
    [[1, 0, 0], [1, 1, 1]],  # J
    [[0, 0, 1], [1, 1, 1]]   # L
]

# 方块颜色
SHAPE_COLORS = [CYAN, YELLOW, PURPLE, GREEN, RED, BLUE, ORANGE]

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
        # 2=上(旋转), 4=左, 6=右, 8=下(加速下落)
        if not self.game.game_over:
            if data == '2':  # 上 - 旋转
                self.game.rotate_piece()
            elif data == '4':  # 左 - 左移
                self.game.move_piece(-1, 0)
            elif data == '6':  # 右 - 右移
                self.game.move_piece(1, 0)
            elif data == '8':  # 下 - 加速下落
                self.game.move_piece(0, 1)

class TetrisGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("俄罗斯方块 - 支持单片机控制")
        
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
                    self.font = pygame.font.Font(font_path, 24)
                    self.big_font = pygame.font.Font(font_path, 36)
                    self.small_font = pygame.font.Font(font_path, 18)
                    print(f"成功加载字体: {font_path}")
                    break
                except:
                    continue
            
            if self.font is None:
                self.font = pygame.font.SysFont(None, 24)
                self.big_font = pygame.font.SysFont(None, 36)
                self.small_font = pygame.font.SysFont(None, 18)
                print("使用默认字体，可能无法显示中文")
        except:
            self.font = pygame.font.SysFont(None, 24)
            self.big_font = pygame.font.SysFont(None, 36)
            self.small_font = pygame.font.SysFont(None, 18)
            print("字体加载失败，使用默认字体")
        
        self.clock = pygame.time.Clock()
        
        # 初始化串口控制器
        self.serial_controller = SerialController(self)
        
        # 获取可用串口
        self.available_ports = self.get_available_ports()
        self.selected_port = "COM3" if self.available_ports else ""
        
        self.reset_game()

        # 显示启动弹窗
        self.show_startup_popup()
    
    def show_startup_popup(self):
        """显示启动信息弹窗"""
        popup_width = 600
        popup_height = 900
        popup_x = (SCREEN_WIDTH - popup_width) // 2
        popup_y = (SCREEN_HEIGHT - popup_height) // 2
        
        # 弹窗颜色定义
        POPUP_BG = (255, 253, 240)  # 米白色背景
        TITLE_COLOR = (30, 30, 120)  # 深蓝色标题
        TEXT_COLOR = (50, 50, 50)    # 正文深灰色
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
            title_text = self.font.render("俄罗斯方块游戏 - 启动信息", True, TITLE_COLOR)
            self.screen.blit(title_text, (popup_x + (popup_width - title_text.get_width()) // 2, popup_y + 30))
            
            # 绘制游戏信息
            info_lines = [
                "欢迎使用俄罗斯方块游戏！",
                "",
                f"作者: 小浩同学 (GitHub: embuxpie)",
                f"版本: 0.1.0",
                f"发布日期: 2026-02-04",
                f"许可证: MIT License",
                "项目仓库:",
                "https://github.com/embuxpie/wangpeng_sensor",
                "embuxpie@outlook.com",
                "游戏简介:",
                "• 经典的俄罗斯方块游戏，支持单片机控制",
                "• 消除完整的行来获得分数",
                "• 随着等级提高，方块下落速度会加快",
                "",
                "控制方式:",
                "键盘控制:",
                "  ↑ 键 - 旋转方块",
                "  ← → 键 - 左右移动方块",
                "  ↓ 键 - 加速下落",
                "  P 键 - 暂停/继续游戏",
                "  R 键 - 重新开始游戏",
                "",
                "单片机控制 (4x4矩阵按键):",
                "  2 键 - 旋转方块",
                "  4 键 - 左移方块",
                "  6 键 - 右移方块",
                "  8 键 - 加速下落",
                "",
                "串口连接:",
                f"可用端口: {', '.join(self.available_ports) if self.available_ports else '无'}",
                f"默认连接: {self.selected_port}"
            ]
            
            line_height = 24
            for i, line in enumerate(info_lines):
                if line.startswith("游戏简介:") or line.startswith("控制方式:") or line.startswith("计分规则:") or line.startswith("串口连接:"):
                    # 分类标题
                    text_surface = self.small_font.render(line, True, (0, 100, 200))
                elif line.startswith("•"):
                    # 列表项
                    text_surface = self.small_font.render(line, True, (80, 80, 80))
                elif line.startswith("  ") or line.startswith("   "):
                    # 控制说明子项
                    text_surface = self.small_font.render(line, True, (60, 60, 60))
                elif "可用端口:" in line or "默认连接:" in line:
                    # 串口信息
                    text_surface = self.small_font.render(line, True, (0, 120, 0))
                else:
                    text_surface = self.small_font.render(line, True, TEXT_COLOR)
                
                self.screen.blit(text_surface, (popup_x + 40, popup_y + 80 + i * line_height))
            
            # 绘制分隔线
            pygame.draw.line(self.screen, (200, 200, 200), 
                           (popup_x + 30, button_y - 25), 
                           (popup_x + popup_width - 30, button_y - 25), 2)
            
            # 绘制确定按钮
            current_button_color = BUTTON_HOVER_COLOR if button_hovered else BUTTON_COLOR
            pygame.draw.rect(self.screen, current_button_color, button_rect, border_radius=8)
            pygame.draw.rect(self.screen, (40, 40, 40), button_rect, 2, border_radius=8)
            
            button_text = self.small_font.render("开始游戏 (Enter)", True, (255, 255, 255))
            self.screen.blit(button_text, (button_rect.centerx - button_text.get_width() // 2, 
                                         button_rect.centery - button_text.get_height() // 2))
            
            # 底部提示
            hint_text = self.small_font.render("点击确定按钮或按 Enter 键开始游戏", True, (120, 120, 120))
            self.screen.blit(hint_text, (popup_x + (popup_width - hint_text.get_width()) // 2, popup_y + popup_height - 25))
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        # 弹窗关闭后，清屏回到默认背景色，为游戏主界面做准备
        self.screen.fill(BLACK)
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
        self.grid = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.current_piece = self.new_piece()
        self.next_piece = self.new_piece()
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.fall_speed = 0.5  # 初始下落速度（秒）
        self.fall_time = 0
        self.game_over = False
        self.paused = False
    
    def new_piece(self):
        """创建新方块"""
        shape_idx = random.randint(0, len(SHAPES) - 1)
        return {
            'shape': SHAPES[shape_idx],
            'color': SHAPE_COLORS[shape_idx],
            'x': GRID_WIDTH // 2 - len(SHAPES[shape_idx][0]) // 2,
            'y': 0
        }
    
    def valid_position(self, piece, x_offset=0, y_offset=0):
        """检查位置是否有效"""
        for y, row in enumerate(piece['shape']):
            for x, cell in enumerate(row):
                if cell:
                    new_x = piece['x'] + x + x_offset
                    new_y = piece['y'] + y + y_offset
                    
                    # 检查边界
                    if new_x < 0 or new_x >= GRID_WIDTH or new_y >= GRID_HEIGHT:
                        return False
                    
                    # 检查是否与已有方块重叠
                    if new_y >= 0 and self.grid[new_y][new_x]:
                        return False
        return True
    
    def move_piece(self, x_offset, y_offset):
        """移动当前方块"""
        if self.valid_position(self.current_piece, x_offset, y_offset):
            self.current_piece['x'] += x_offset
            self.current_piece['y'] += y_offset
            return True
        return False
    
    def rotate_piece(self):
        """旋转当前方块"""
        # 创建旋转后的形状
        shape = self.current_piece['shape']
        rotated = list(zip(*shape[::-1]))  # 顺时针旋转90度
        rotated_shape = [list(row) for row in rotated]
        
        old_shape = self.current_piece['shape']
        self.current_piece['shape'] = rotated_shape
        
        # 如果旋转后位置无效，则恢复原形状
        if not self.valid_position(self.current_piece):
            self.current_piece['shape'] = old_shape
    
    def lock_piece(self):
        """将当前方块锁定到网格中"""
        for y, row in enumerate(self.current_piece['shape']):
            for x, cell in enumerate(row):
                if cell:
                    grid_y = self.current_piece['y'] + y
                    grid_x = self.current_piece['x'] + x
                    if grid_y >= 0:  # 确保不在顶部之上
                        self.grid[grid_y][grid_x] = self.current_piece['color']
        
        # 检查是否有完整的行
        self.clear_lines()
        
        # 生成新方块
        self.current_piece = self.next_piece
        self.next_piece = self.new_piece()
        
        # 检查游戏是否结束
        if not self.valid_position(self.current_piece):
            self.game_over = True
    
    def clear_lines(self):
        """清除完整的行并计分"""
        lines_to_clear = []
        for y in range(GRID_HEIGHT):
            if all(self.grid[y]):
                lines_to_clear.append(y)
        
        for line in lines_to_clear:
            # 移除该行
            del self.grid[line]
            # 在顶部添加新行
            self.grid.insert(0, [0 for _ in range(GRID_WIDTH)])
        
        # 更新分数
        if lines_to_clear:
            self.lines_cleared += len(lines_to_clear)
            self.score += [100, 300, 500, 800][min(len(lines_to_clear) - 1, 3)] * self.level
            
            # 更新等级和速度
            self.level = self.lines_cleared // 10 + 1
            self.fall_speed = max(0.05, 0.5 - (self.level - 1) * 0.05)
    
    def draw_grid(self):
        """绘制游戏网格"""
        # 绘制背景
        pygame.draw.rect(self.screen, BLACK, 
                        (GRID_OFFSET_X, GRID_OFFSET_Y, 
                         GRID_WIDTH * BLOCK_SIZE, GRID_HEIGHT * BLOCK_SIZE))
        
        # 绘制网格线
        for x in range(GRID_WIDTH + 1):
            pygame.draw.line(self.screen, GRAY, 
                           (GRID_OFFSET_X + x * BLOCK_SIZE, GRID_OFFSET_Y),
                           (GRID_OFFSET_X + x * BLOCK_SIZE, 
                            GRID_OFFSET_Y + GRID_HEIGHT * BLOCK_SIZE), 1)
        
        for y in range(GRID_HEIGHT + 1):
            pygame.draw.line(self.screen, GRAY,
                           (GRID_OFFSET_X, GRID_OFFSET_Y + y * BLOCK_SIZE),
                           (GRID_OFFSET_X + GRID_WIDTH * BLOCK_SIZE, 
                            GRID_OFFSET_Y + y * BLOCK_SIZE), 1)
        
        # 绘制已锁定的方块
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                if self.grid[y][x]:
                    pygame.draw.rect(self.screen, self.grid[y][x],
                                   (GRID_OFFSET_X + x * BLOCK_SIZE + 1,
                                    GRID_OFFSET_Y + y * BLOCK_SIZE + 1,
                                    BLOCK_SIZE - 2, BLOCK_SIZE - 2))
    
    def draw_current_piece(self):
        """绘制当前下落的方块"""
        for y, row in enumerate(self.current_piece['shape']):
            for x, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(self.screen, self.current_piece['color'],
                                   (GRID_OFFSET_X + (self.current_piece['x'] + x) * BLOCK_SIZE + 1,
                                    GRID_OFFSET_Y + (self.current_piece['y'] + y) * BLOCK_SIZE + 1,
                                    BLOCK_SIZE - 2, BLOCK_SIZE - 2))
    
    def draw_next_piece(self):
        """绘制下一个方块预览"""
        # 绘制预览区域标题
        next_text = self.font.render("下一个:", True, WHITE)
        self.screen.blit(next_text, (GRID_OFFSET_X + GRID_WIDTH * BLOCK_SIZE + 20, GRID_OFFSET_Y))
        
        # 绘制预览区域背景
        preview_x = GRID_OFFSET_X + GRID_WIDTH * BLOCK_SIZE + 20
        preview_y = GRID_OFFSET_Y + 40
        pygame.draw.rect(self.screen, BLACK, (preview_x, preview_y, 5 * BLOCK_SIZE, 5 * BLOCK_SIZE))
        
        # 绘制下一个方块
        for y, row in enumerate(self.next_piece['shape']):
            for x, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(self.screen, self.next_piece['color'],
                                   (preview_x + x * BLOCK_SIZE + 1,
                                    preview_y + y * BLOCK_SIZE + 1,
                                    BLOCK_SIZE - 2, BLOCK_SIZE - 2))
    
    def draw_info(self):
        """绘制游戏信息"""
        # 绘制游戏标题
        title_text = self.big_font.render("俄罗斯方块", True, WHITE)
        self.screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 10))
        
        # 绘制分数
        score_text = self.font.render(f"分数: {self.score}", True, WHITE)
        self.screen.blit(score_text, (GRID_OFFSET_X + GRID_WIDTH * BLOCK_SIZE + 20, GRID_OFFSET_Y + 150))
        
        # 绘制等级
        level_text = self.font.render(f"等级: {self.level}", True, WHITE)
        self.screen.blit(level_text, (GRID_OFFSET_X + GRID_WIDTH * BLOCK_SIZE + 20, GRID_OFFSET_Y + 180))
        
        # 绘制消除行数
        lines_text = self.font.render(f"消除行数: {self.lines_cleared}", True, WHITE)
        self.screen.blit(lines_text, (GRID_OFFSET_X + GRID_WIDTH * BLOCK_SIZE + 20, GRID_OFFSET_Y + 210))
        
        # 绘制控制说明
        controls_y = GRID_OFFSET_Y + 250
        controls = [
            "控制说明:",
            "键盘:",
            "↑ - 旋转",
            "← → - 左右移动",
            "↓ - 加速下落",
            "P - 暂停/继续",
            "R - 重新开始",
            "",
            "单片机:",
            "2 - 旋转",
            "4 - 左移",
            "6 - 右移",
            "8 - 加速下落"
        ]
        
        for i, text in enumerate(controls):
            control_text = self.small_font.render(text, True, WHITE)
            self.screen.blit(control_text, (GRID_OFFSET_X + GRID_WIDTH * BLOCK_SIZE + 20, controls_y + i * 25))
    
    def draw_serial_info(self):
        """绘制串口信息"""
        # 串口状态
        status = "已连接" if self.serial_controller.connected else "未连接"
        status_color = GREEN if self.serial_controller.connected else RED
        
        status_text = self.small_font.render(f"串口状态: {status}", True, status_color)
        self.screen.blit(status_text, (20, SCREEN_HEIGHT - 60))
        
        # 最后接收到的数据
        data_text = self.small_font.render(f"最后接收: {self.serial_controller.last_received}", True, WHITE)
        self.screen.blit(data_text, (20, SCREEN_HEIGHT - 30))
    
    def draw_pause_screen(self):
        """绘制暂停画面"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        
        pause_text = self.big_font.render("游戏暂停", True, WHITE)
        self.screen.blit(pause_text, (SCREEN_WIDTH // 2 - pause_text.get_width() // 2, SCREEN_HEIGHT // 2 - 50))
        
        continue_text = self.font.render("按 P 键继续", True, WHITE)
        self.screen.blit(continue_text, (SCREEN_WIDTH // 2 - continue_text.get_width() // 2, SCREEN_HEIGHT // 2 + 10))
    
    def draw_game_over(self):
        """绘制游戏结束画面"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        
        game_over_text = self.big_font.render("游戏结束", True, RED)
        self.screen.blit(game_over_text, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, SCREEN_HEIGHT // 2 - 50))
        
        score_text = self.font.render(f"最终分数: {self.score}", True, WHITE)
        self.screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, SCREEN_HEIGHT // 2 + 10))
        
        restart_text = self.font.render("按 R 键重新开始", True, WHITE)
        self.screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT // 2 + 50))
    
    def run(self):
        """运行游戏主循环"""
        # 尝试自动连接串口
        if self.available_ports and self.selected_port:
            print(f"尝试连接串口: {self.selected_port}")
            if self.connect_serial():
                print("串口连接成功！")
            else:
                print("串口连接失败，请检查连接")
        
        last_time = pygame.time.get_ticks()
        
        while True:
            current_time = pygame.time.get_ticks()
            delta_time = (current_time - last_time) / 1000.0  # 转换为秒
            last_time = current_time
            
            # 处理事件
            for event in pygame.event.get():
                if event.type == QUIT:
                    if self.serial_controller.connected:
                        self.serial_controller.disconnect()
                    pygame.quit()
                    sys.exit()
                
                if event.type == KEYDOWN:
                    if event.key == K_r:  # 重新开始
                        self.reset_game()
                    elif event.key == K_p:  # 暂停/继续
                        self.paused = not self.paused
                    elif not self.game_over and not self.paused:
                        if event.key == K_LEFT:  # 左移
                            self.move_piece(-1, 0)
                        elif event.key == K_RIGHT:  # 右移
                            self.move_piece(1, 0)
                        elif event.key == K_DOWN:  # 加速下落
                            self.move_piece(0, 1)
                        elif event.key == K_UP:  # 旋转
                            self.rotate_piece()
            
            # 更新游戏状态
            if not self.game_over and not self.paused:
                self.fall_time += delta_time
                
                # 自动下落
                if self.fall_time >= self.fall_speed:
                    self.fall_time = 0
                    if not self.move_piece(0, 1):
                        self.lock_piece()
            
            # 绘制游戏
            self.screen.fill(BLACK)
            self.draw_grid()
            self.draw_current_piece()
            self.draw_next_piece()
            self.draw_info()
            self.draw_serial_info()
            
            if self.paused:
                self.draw_pause_screen()
            elif self.game_over:
                self.draw_game_over()
            
            pygame.display.flip()
            self.clock.tick(FPS)

def main():
    """主函数"""
    print("俄罗斯方块游戏开始！")
    print("控制方式:")
    print("  1. 键盘: ↑(旋转), ←→(左右移动), ↓(加速下落), P(暂停), R(重新开始)")
    print("  2. 单片机矩阵按键: 2(旋转), 4(左移), 6(右移), 8(加速下落)")
    print("祝你游戏愉快！")
    
    game = TetrisGame()
    game.run()

if __name__ == "__main__":
    main()
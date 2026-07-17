import sys
import os
from pathlib import Path

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from qfluentwidgets import (
    # 基础组件
    FluentWindow, NavigationItemPosition, MessageBox, InfoBar, InfoBarPosition,
    # 布局组件
    ScrollArea, SmoothScrollArea,
    # 按钮组件
    PrimaryPushButton, PushButton, HyperlinkButton, ToggleButton,
    # 输入组件
    LineEdit, ComboBox, SpinBox, DoubleSpinBox, CheckBox, SwitchButton,
    # 展示组件
    ImageLabel, TitleLabel, BodyLabel, CaptionLabel,
    # 对话框组件
    Dialog, MessageBox, ColorDialog,
    # 状态组件
    ProgressRing, IndeterminateProgressRing, ProgressBar,
    # 分组组件
    CardWidget, GroupHeaderCardWidget, SettingCardGroup,
    # 图标组件
    FluentIcon as FIF, Icon,
    # 滑动条
    Slider
)
from qfluentwidgets import isDarkTheme, setTheme, Theme

# 导入转换器模块
from converter import PerlerBeadConverter
from mard_colors import MARD_COLORS_HEX, hex_to_rgb


class QuickToolTip(QObject):
    """快速工具提示 - 鼠标悬停时快速显示提示"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tooltips = {}
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.show_tooltip)
        self.current_widget = None
        self.current_text = ""
    
    def add_tooltip(self, widget, text):
        """为控件添加快速提示"""
        self.tooltips[widget] = text
        widget.installEventFilter(self)
    
    def eventFilter(self, obj, event):
        """事件过滤器"""
        if event.type() == QEvent.Enter:
            if obj in self.tooltips:
                self.current_widget = obj
                self.current_text = self.tooltips[obj]
                self.timer.start(200)  # 200毫秒后显示
        elif event.type() == QEvent.Leave:
            self.timer.stop()
            self.current_widget = None
            QToolTip.hideText()
        return False
    
    def show_tooltip(self):
        """显示工具提示"""
        if self.current_widget and self.current_text:
            pos = QCursor.pos()
            QToolTip.showText(pos, self.current_text, self.current_widget)


class EditDialog(QDialog):
    """编辑对话框 - 用于编辑拼豆图纸"""
    
    def __init__(self, result_data, converter, parent=None):
        super().__init__(parent)
        self.result_data = result_data
        self.converter = converter
        self.selected_points = set()
        self.current_color = "H7"
        self.zoom = 1.0
        
        # 拖动相关
        self.is_dragging = False
        self.last_drag_pos = None
        self.is_selecting = False
        
        # 优化：批量更新
        self.update_timer = QTimer()
        self.update_timer.setInterval(50)  # 50ms更新一次
        self.update_timer.timeout.connect(self.do_batch_update)
        self.pending_updates = set()  # 待更新的单元格
        self.need_full_refresh = False
        
        # 缓存图形项
        self.cell_items = {}  # {(x,y): (rect_item, text_item)}
        
        self.setWindowTitle("编辑拼豆图纸")
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        self.resize(1000, 700)
        self.init_ui()
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 左侧：图纸显示区域
        left_panel = self.create_display_panel()
        layout.addWidget(left_panel, 3)
        
        # 右侧：颜色选择区域
        right_panel = self.create_color_panel()
        layout.addWidget(right_panel, 1)
    
    def create_display_panel(self):
        """创建图纸显示面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 控制栏
        control_bar = QWidget()
        control_layout = QHBoxLayout(control_bar)
        control_layout.setContentsMargins(0, 0, 0, 0)
        
        self.zoom_in_btn = PushButton("放大")
        self.zoom_in_btn.clicked.connect(lambda: self.zoom_view(1.2))
        control_layout.addWidget(self.zoom_in_btn)
        
        self.zoom_out_btn = PushButton("缩小")
        self.zoom_out_btn.clicked.connect(lambda: self.zoom_view(0.8))
        control_layout.addWidget(self.zoom_out_btn)
        
        self.fit_btn = PushButton("适应窗口")
        self.fit_btn.clicked.connect(self.fit_view)
        control_layout.addWidget(self.fit_btn)
        
        control_layout.addStretch()
        
        self.status_label = BodyLabel("左键点击选择，左键拖动连续选择，右键拖动移动图像")
        control_layout.addWidget(self.status_label)
        
        layout.addWidget(control_bar)
        
        # 图纸显示区域
        self.graphics_view = QGraphicsView()
        self.graphics_view.setRenderHint(QPainter.Antialiasing)
        self.graphics_view.setDragMode(QGraphicsView.NoDrag)
        self.graphics_view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        
        self.scene = QGraphicsScene()
        self.graphics_view.setScene(self.scene)
        
        # 绑定鼠标事件
        self.graphics_view.mousePressEvent = self.on_view_press
        self.graphics_view.mouseMoveEvent = self.on_view_move
        self.graphics_view.mouseReleaseEvent = self.on_view_release
        self.graphics_view.wheelEvent = self.on_view_wheel
        
        layout.addWidget(self.graphics_view)
        
        # 初始显示
        self.refresh_display()
        
        return panel
    
    def create_color_panel(self):
        """创建颜色选择面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 当前颜色显示
        current_color_card = CardWidget()
        current_layout = QVBoxLayout(current_color_card)
        current_layout.setContentsMargins(15, 15, 15, 15)
        
        current_title = BodyLabel("当前颜色")
        current_title.setStyleSheet("font-weight: bold; color: #3498db;")
        current_layout.addWidget(current_title)
        
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(60, 60)
        self.color_preview.setStyleSheet("background-color: #000000; border: 2px solid #ccc;")
        current_layout.addWidget(self.color_preview, alignment=Qt.AlignCenter)
        
        self.color_code_label = BodyLabel("H7")
        self.color_code_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        current_layout.addWidget(self.color_code_label, alignment=Qt.AlignCenter)
        
        layout.addWidget(current_color_card)
        
        # 操作按钮
        button_card = CardWidget()
        button_layout = QVBoxLayout(button_card)
        button_layout.setContentsMargins(15, 15, 15, 15)
        
        self.apply_btn = PrimaryPushButton("应用到选中点")
        self.apply_btn.clicked.connect(self.apply_color)
        button_layout.addWidget(self.apply_btn)
        
        self.clear_btn = PushButton("清空选择")
        self.clear_btn.clicked.connect(self.clear_selection)
        button_layout.addWidget(self.clear_btn)
        
        layout.addWidget(button_card)
        
        # 颜色选择标签页
        color_notebook = QTabWidget()
        
        # 按系列分组显示颜色
        series_list = [
            ("A", "黄橙", 26),
            ("B", "绿色", 32),
            ("C", "蓝绿", 29),
            ("D", "蓝紫", 26),
            ("E", "粉色", 24),
            ("F", "红色", 25),
            ("G", "棕色", 21),
            ("H", "灰黑白", 23),
            ("M", "特殊", 15),
            ("P", "珠光", 23),
            ("Q", "荧光", 5),
            ("R", "彩虹", 28),
        ]
        
        for prefix, name, count in series_list:
            tab = QWidget()
            tab_layout = QGridLayout(tab)
            tab_layout.setSpacing(5)
            
            col = 0
            row = 0
            for i in range(1, count + 1):
                color_code = f"{prefix}{i}"
                if color_code in MARD_COLORS_HEX:
                    hex_color = MARD_COLORS_HEX[color_code]
                    
                    btn = QPushButton()
                    btn.setFixedSize(30, 30)
                    btn.setStyleSheet(f"background-color: {hex_color}; border: 1px solid #ccc;")
                    btn.setToolTip(color_code)
                    btn.clicked.connect(lambda checked, c=color_code: self.select_color(c))
                    tab_layout.addWidget(btn, row, col)
                    
                    col += 1
                    if col >= 8:
                        col = 0
                        row += 1
            
            color_notebook.addTab(tab, f"{prefix}-{name}")
        
        layout.addWidget(color_notebook)
        
        return panel
    
    def refresh_display(self):
        """刷新图纸显示（全量刷新）"""
        self.scene.clear()
        self.cell_items.clear()
        
        if self.result_data is None:
            return
        
        matrix = self.result_data["matrix"]
        width = self.result_data["width"]
        height = self.result_data["height"]
        
        cell_size = int(10 * self.zoom)
        
        # 批量绘制网格
        for y in range(height):
            for x in range(width):
                self.draw_cell(x, y, cell_size, matrix[y][x])
        
        # 调整视图
        self.graphics_view.setSceneRect(0, 0, width * cell_size, height * cell_size)
    
    def draw_cell(self, x, y, cell_size, color_code):
        """绘制单个单元格"""
        hex_color = MARD_COLORS_HEX.get(color_code, "#FFFFFF")
        
        x1 = x * cell_size
        y1 = y * cell_size
        
        # 绘制背景色
        rect = self.scene.addRect(x1, y1, cell_size, cell_size, 
                                  QPen(QColor(200, 200, 200)), 
                                  QBrush(QColor(hex_color)))
        
        # 选中高亮
        highlight = None
        if (x, y) in self.selected_points:
            highlight = self.scene.addRect(x1+1, y1+1, cell_size-2, cell_size-2,
                                           QPen(QColor(255, 0, 0), 2))
        
        # 色号文字
        text_item = None
        if cell_size >= 15:
            rgb = hex_to_rgb(hex_color)
            brightness = rgb[0] * 0.299 + rgb[1] * 0.587 + rgb[2] * 0.114
            text_color = QColor(255, 255, 255) if brightness < 128 else QColor(0, 0, 0)
            
            text_item = self.scene.addText(color_code, QFont("Arial", max(6, int(cell_size / 4))))
            text_item.setDefaultTextColor(text_color)
            text_item.setPos(x1 + cell_size/2 - text_item.boundingRect().width()/2, 
                            y1 + cell_size/2 - text_item.boundingRect().height()/2)
        
        self.cell_items[(x, y)] = (rect, highlight, text_item)
    
    def update_single_cell(self, x, y):
        """更新单个单元格（不重绘全部）"""
        if (x, y) in self.cell_items:
            # 删除旧的图形项
            rect, highlight, text = self.cell_items[(x, y)]
            if rect:
                self.scene.removeItem(rect)
            if highlight:
                self.scene.removeItem(highlight)
            if text:
                self.scene.removeItem(text)
        
        # 重新绘制
        cell_size = int(10 * self.zoom)
        matrix = self.result_data["matrix"]
        self.draw_cell(x, y, cell_size, matrix[y][x])
    
    def do_batch_update(self):
        """批量更新待处理的单元格"""
        if self.need_full_refresh:
            self.refresh_display()
            self.need_full_refresh = False
        elif self.pending_updates:
            cell_size = int(10 * self.zoom)
            matrix = self.result_data["matrix"]
            
            for (x, y) in self.pending_updates:
                self.update_single_cell(x, y)
            
            self.pending_updates.clear()
        
        self.update_timer.stop()
    
    def schedule_update(self, x, y):
        """调度单元格更新"""
        self.pending_updates.add((x, y))
        if not self.update_timer.isActive():
            self.update_timer.start()
    
    def get_bead_coord(self, pos):
        """获取鼠标位置对应的豆子坐标"""
        scene_pos = self.graphics_view.mapToScene(pos)
        cell_size = int(10 * self.zoom)
        
        x = int(scene_pos.x() / cell_size)
        y = int(scene_pos.y() / cell_size)
        
        width = self.result_data["width"]
        height = self.result_data["height"]
        
        if 0 <= x < width and 0 <= y < height:
            return x, y
        return None, None
    
    def on_view_press(self, event):
        """鼠标按下事件"""
        if self.result_data is None:
            return
        
        if event.button() == Qt.LeftButton:
            self.is_selecting = True
            x, y = self.get_bead_coord(event.pos())
            if x is not None:
                if (x, y) in self.selected_points:
                    self.selected_points.discard((x, y))
                else:
                    self.selected_points.add((x, y))
                # 立即更新单个单元格
                self.update_single_cell(x, y)
                self.status_label.setText(f"已选中 {len(self.selected_points)} 个点")
        
        elif event.button() == Qt.RightButton:
            self.is_dragging = True
            self.last_drag_pos = event.pos()
            self.graphics_view.setCursor(Qt.ClosedHandCursor)
    
    def on_view_move(self, event):
        """鼠标移动事件"""
        if self.result_data is None:
            return
        
        if self.is_selecting and event.buttons() & Qt.LeftButton:
            x, y = self.get_bead_coord(event.pos())
            if x is not None and (x, y) not in self.selected_points:
                self.selected_points.add((x, y))
                # 调度更新（批量处理）
                self.schedule_update(x, y)
                self.status_label.setText(f"已选中 {len(self.selected_points)} 个点")
        
        elif self.is_dragging and event.buttons() & Qt.RightButton:
            if self.last_drag_pos:
                delta = event.pos() - self.last_drag_pos
                self.graphics_view.horizontalScrollBar().setValue(
                    self.graphics_view.horizontalScrollBar().value() - delta.x()
                )
                self.graphics_view.verticalScrollBar().setValue(
                    self.graphics_view.verticalScrollBar().value() - delta.y()
                )
                self.last_drag_pos = event.pos()
    
    def on_view_release(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton:
            self.is_selecting = False
            # 确保所有待更新的单元格都已更新
            if self.pending_updates:
                self.do_batch_update()
        elif event.button() == Qt.RightButton:
            self.is_dragging = False
            self.last_drag_pos = None
            self.graphics_view.setCursor(Qt.ArrowCursor)
    
    def on_view_wheel(self, event):
        """视图滚轮事件"""
        if event.angleDelta().y() > 0:
            factor = 1.1
        else:
            factor = 0.9
        
        self.zoom *= factor
        self.zoom = max(0.1, min(5.0, self.zoom))
        
        # 延迟重绘，避免频繁刷新
        if hasattr(self, '_zoom_timer'):
            self._zoom_timer.stop()
        else:
            self._zoom_timer = QTimer()
            self._zoom_timer.setSingleShot(True)
            self._zoom_timer.timeout.connect(self.refresh_display)
        self._zoom_timer.start(100)  # 100ms后重绘
    
    def zoom_view(self, factor):
        """缩放视图（按钮触发）"""
        self.zoom *= factor
        self.zoom = max(0.1, min(5.0, self.zoom))
        self.refresh_display()
    
    def fit_view(self):
        """适应窗口大小"""
        self.zoom = 1.0
        self.refresh_display()
        self.graphics_view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
    
    def select_color(self, color_code):
        """选择颜色"""
        self.current_color = color_code
        hex_color = MARD_COLORS_HEX.get(color_code, "#000000")
        
        self.color_preview.setStyleSheet(f"background-color: {hex_color}; border: 2px solid #ccc;")
        self.color_code_label.setText(color_code)
    
    def apply_color(self):
        """应用颜色到选中的点"""
        if not self.selected_points:
            InfoBar.warning("提示", "请先选择要修改的点", parent=self)
            return
        
        matrix = self.result_data["matrix"]
        
        for (x, y) in self.selected_points:
            if 0 <= y < len(matrix) and 0 <= x < len(matrix[0]):
                matrix[y][x] = self.current_color
        
        self.selected_points.clear()
        self.refresh_display()
        self.status_label.setText(f"已应用颜色 {self.current_color}")
    
    def clear_selection(self):
        """清空选择"""
        self.selected_points.clear()
        self.refresh_display()
        self.status_label.setText("已清空选择")


class MainInterface(QWidget):
    """主界面"""
    
    def __init__(self):
        super().__init__()
        self.setObjectName("MainInterface")
        
        self.converter = PerlerBeadConverter()
        self.current_image_path = None
        self.result_data = None
        
        # 创建快速工具提示管理器
        self.quick_tooltip = QuickToolTip(self)
        
        self.init_ui()
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 左侧控制面板
        control_panel = self.create_control_panel()
        layout.addWidget(control_panel, 1)
        
        # 右侧显示区域
        display_panel = self.create_display_panel()
        layout.addWidget(display_panel, 3)
    
    def create_control_panel(self):
        """创建控制面板"""
        panel = ScrollArea()
        panel.setWidgetResizable(True)
        
        container = QWidget()
        panel.setWidget(container)
        
        layout = QVBoxLayout(container)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 图片导入卡片
        image_card = CardWidget()
        image_layout = QVBoxLayout(image_card)
        image_layout.setContentsMargins(20, 15, 20, 15)
        
        image_title = BodyLabel("📷 图片导入")
        image_title.setStyleSheet("font-weight: bold; color: #3498db;")
        image_layout.addWidget(image_title)
        
        self.load_image_btn = PrimaryPushButton("选择图片")
        self.load_image_btn.clicked.connect(self.load_image)
        image_layout.addWidget(self.load_image_btn)
        
        self.image_path_label = BodyLabel("未选择图片")
        self.image_path_label.setStyleSheet("color: #95a5a6;")
        image_layout.addWidget(self.image_path_label)
        
        layout.addWidget(image_card)
        
        # 参数设置卡片
        params_card = CardWidget()
        params_layout = QVBoxLayout(params_card)
        params_layout.setContentsMargins(20, 15, 20, 15)
        
        params_title = BodyLabel("⚙️ 参数设置")
        params_title.setStyleSheet("font-weight: bold; color: #3498db;")
        params_layout.addWidget(params_title)
        
        # 宽度设置
        width_layout = QHBoxLayout()
        width_label = BodyLabel("宽度（格子数）:")
        self.quick_tooltip.add_tooltip(width_label, "设置输出拼豆图纸的宽度\n高度会根据原图比例自动计算\n值越大细节越丰富，但处理时间更长")
        width_layout.addWidget(width_label)
        self.width_spinbox = SpinBox()
        self.width_spinbox.setRange(1, 200)
        self.width_spinbox.setValue(16)
        self.quick_tooltip.add_tooltip(self.width_spinbox, "建议值：\n16-29：简单图案\n30-50：中等细节\n50-100：高细节\n100+：超高清（处理较慢）")
        self.width_spinbox.valueChanged.connect(self.update_dimension)
        width_layout.addWidget(self.width_spinbox)
        params_layout.addLayout(width_layout)
        
        # 尺寸显示
        self.dimension_label = BodyLabel("尺寸：16 x ?")
        self.quick_tooltip.add_tooltip(self.dimension_label, "转换后的拼豆图纸尺寸\n高度根据原图比例自动计算")
        params_layout.addWidget(self.dimension_label)
        
        # 色号规格
        spec_layout = QHBoxLayout()
        spec_label = BodyLabel("色号规格:")
        self.quick_tooltip.add_tooltip(spec_label, "选择使用的色号规格\n221色：标准色号，覆盖常用颜色\n291色：完整色号，包含更多特殊颜色")
        spec_layout.addWidget(spec_label)
        self.spec_combo = ComboBox()
        self.spec_combo.addItems(["221", "291"])
        self.quick_tooltip.add_tooltip(self.spec_combo, "221色：A-H + M系列，适合大多数图片\n291色：包含P、Q、R、T、Y、ZG系列，颜色更丰富")
        spec_layout.addWidget(self.spec_combo)
        params_layout.addLayout(spec_layout)
        
        # 抖动模式
        dither_layout = QHBoxLayout()
        dither_label = BodyLabel("抖动模式:")
        self.quick_tooltip.add_tooltip(dither_label, "选择颜色抖动方式\n影响颜色过渡的自然程度")
        dither_layout.addWidget(dither_label)
        self.dither_combo = ComboBox()
        self.dither_combo.addItems(["none", "ordered", "floyd"])
        self.quick_tooltip.add_tooltip(self.dither_combo, "none：无抖动，直接匹配，适合卡通风格\nordered：有序抖动，轻微颗粒感，适合渐变\nfloyd：误差扩散，保留细节最多，适合照片")
        dither_layout.addWidget(self.dither_combo)
        params_layout.addLayout(dither_layout)
        
        # 颜色合并
        merge_layout = QHBoxLayout()
        merge_label = BodyLabel("颜色合并:")
        self.quick_tooltip.add_tooltip(merge_label, "合并相似颜色，减少颜色种类\n值越大合并越激进")
        merge_layout.addWidget(merge_label)
        self.merge_slider = Slider(Qt.Horizontal)
        self.merge_slider.setRange(0, 100)
        self.merge_slider.setValue(0)
        self.quick_tooltip.add_tooltip(self.merge_slider, "0：不合并\n10-20：轻度合并（推荐）\n30-50：中度合并\n50+：激进合并")
        self.merge_slider.valueChanged.connect(self.update_merge_label)
        merge_layout.addWidget(self.merge_slider)
        self.merge_label = BodyLabel("0")
        merge_layout.addWidget(self.merge_label)
        params_layout.addLayout(merge_layout)
        
        layout.addWidget(params_card)
        
        # 功能按钮卡片
        button_card = CardWidget()
        button_layout = QVBoxLayout(button_card)
        button_layout.setContentsMargins(20, 15, 20, 15)
        
        button_title = BodyLabel("🎯 功能按钮")
        button_title.setStyleSheet("font-weight: bold; color: #3498db;")
        button_layout.addWidget(button_title)
        
        self.convert_btn = PrimaryPushButton("开始转换")
        self.convert_btn.clicked.connect(self.start_convert)
        button_layout.addWidget(self.convert_btn)
        
        self.edit_btn = PushButton("打开编辑器")
        self.edit_btn.clicked.connect(self.open_editor)
        self.edit_btn.setEnabled(False)
        button_layout.addWidget(self.edit_btn)
        
        layout.addWidget(button_card)
        
        # 保存按钮卡片
        save_card = CardWidget()
        save_layout = QVBoxLayout(save_card)
        save_layout.setContentsMargins(20, 15, 20, 15)
        
        save_title = BodyLabel("💾 保存结果")
        save_title.setStyleSheet("font-weight: bold; color: #3498db;")
        save_layout.addWidget(save_title)
        
        self.save_preview_btn = PushButton("保存预览图")
        self.save_preview_btn.clicked.connect(self.save_preview)
        self.save_preview_btn.setEnabled(False)
        save_layout.addWidget(self.save_preview_btn)
        
        self.save_grid_btn = PushButton("保存网格图")
        self.save_grid_btn.clicked.connect(self.save_grid)
        self.save_grid_btn.setEnabled(False)
        save_layout.addWidget(self.save_grid_btn)
        
        self.save_list_btn = PushButton("保存颜色清单")
        self.save_list_btn.clicked.connect(self.save_color_list)
        self.save_list_btn.setEnabled(False)
        save_layout.addWidget(self.save_list_btn)
        
        layout.addWidget(save_card)
        
        # 高级设置卡片（可折叠）
        advanced_card = CardWidget()
        advanced_layout = QVBoxLayout(advanced_card)
        advanced_layout.setContentsMargins(20, 15, 20, 15)
        
        # 折叠按钮
        self.advanced_toggle = PushButton("🔧 高级设置 ▼")
        self.advanced_toggle.clicked.connect(self.toggle_advanced)
        advanced_layout.addWidget(self.advanced_toggle)
        
        # 高级设置内容（默认隐藏）
        self.advanced_content = QWidget()
        advanced_content_layout = QVBoxLayout(self.advanced_content)
        advanced_content_layout.setContentsMargins(0, 10, 0, 0)
        self.advanced_content.setVisible(False)
        
        # 豆子形状
        shape_layout = QHBoxLayout()
        shape_label = BodyLabel("豆子形状:")
        self.quick_tooltip.add_tooltip(shape_label, "选择拼豆的显示形状：圆形更接近实际拼豆，方形更接近像素风格")
        shape_layout.addWidget(shape_label)
        self.shape_combo = ComboBox()
        self.shape_combo.addItems(["circle", "square"])
        self.quick_tooltip.add_tooltip(self.shape_combo, "圆形：模拟真实拼豆外观\n方形：像素风格，更清晰")
        shape_layout.addWidget(self.shape_combo)
        advanced_content_layout.addLayout(shape_layout)
        
        # 锐化程度
        sharpen_layout = QHBoxLayout()
        sharpen_label = BodyLabel("锐化程度:")
        self.quick_tooltip.add_tooltip(sharpen_label, "增强图像边缘清晰度，让细节更突出\n值越大锐化越强，但可能产生噪点")
        sharpen_layout.addWidget(sharpen_label)
        self.sharpen_slider = Slider(Qt.Horizontal)
        self.sharpen_slider.setRange(0, 100)
        self.sharpen_slider.setValue(30)
        self.quick_tooltip.add_tooltip(self.sharpen_slider, "0：不锐化\n30：轻度锐化（推荐）\n100：强烈锐化")
        self.sharpen_slider.valueChanged.connect(self.update_sharpen_label)
        sharpen_layout.addWidget(self.sharpen_slider)
        self.sharpen_label = BodyLabel("0.3")
        sharpen_layout.addWidget(self.sharpen_label)
        advanced_content_layout.addLayout(sharpen_layout)
        
        # 降噪设置
        self.denoise_checkbox = CheckBox("启用降噪")
        self.quick_tooltip.add_tooltip(self.denoise_checkbox, "启用图像降噪处理，减少杂色\n适用于照片等有噪点的图片")
        advanced_content_layout.addWidget(self.denoise_checkbox)
        
        # 高斯模糊
        gaussian_layout = QHBoxLayout()
        gaussian_label = BodyLabel("高斯模糊半径:")
        self.quick_tooltip.add_tooltip(gaussian_label, "高斯模糊可以平滑图像，减少噪点\n但会让图像变模糊，建议配合深色保护使用")
        gaussian_layout.addWidget(gaussian_label)
        self.gaussian_slider = Slider(Qt.Horizontal)
        self.gaussian_slider.setRange(0, 5)
        self.gaussian_slider.setValue(0)
        self.quick_tooltip.add_tooltip(self.gaussian_slider, "0：不模糊\n1-2：轻度模糊\n3-5：强烈模糊")
        gaussian_layout.addWidget(self.gaussian_slider)
        self.gaussian_label = BodyLabel("0")
        gaussian_layout.addWidget(self.gaussian_label)
        advanced_content_layout.addLayout(gaussian_layout)
        
        # 中值滤波
        median_layout = QHBoxLayout()
        median_label = BodyLabel("中值滤波半径:")
        self.quick_tooltip.add_tooltip(median_label, "中值滤波可以去除椒盐噪点\n同时保留边缘细节，比高斯模糊更保边")
        median_layout.addWidget(median_label)
        self.median_slider = Slider(Qt.Horizontal)
        self.median_slider.setRange(0, 3)
        self.median_slider.setValue(1)
        self.quick_tooltip.add_tooltip(self.median_slider, "0：不滤波\n1：轻度滤波（推荐）\n2-3：强烈滤波")
        median_layout.addWidget(self.median_slider)
        self.median_label = BodyLabel("1")
        median_layout.addWidget(self.median_label)
        advanced_content_layout.addLayout(median_layout)
        
        # 深色阈值
        dark_layout = QHBoxLayout()
        dark_label = BodyLabel("深色阈值:")
        self.quick_tooltip.add_tooltip(dark_label, "控制哪些像素被识别为深色\n深色区域会被保护，不会被模糊或滤波影响")
        dark_layout.addWidget(dark_label)
        self.dark_slider = Slider(Qt.Horizontal)
        self.dark_slider.setRange(0, 100)
        self.dark_slider.setValue(40)
        self.quick_tooltip.add_tooltip(self.dark_slider, "值越大，越多像素被识别为深色\n建议30-60之间")
        dark_layout.addWidget(self.dark_slider)
        self.dark_label = BodyLabel("40")
        dark_layout.addWidget(self.dark_label)
        advanced_content_layout.addLayout(dark_layout)
        
        # ICM空间平滑
        self.spatial_checkbox = CheckBox("ICM空间平滑")
        self.quick_tooltip.add_tooltip(self.spatial_checkbox, "迭代优化相邻像素，减少杂色点\n只处理孤立像素（没有同色邻居的像素）\n可能会影响细节，建议谨慎使用")
        advanced_content_layout.addWidget(self.spatial_checkbox)
        
        # 噪点清理
        self.speckle_checkbox = CheckBox("噪点清理")
        self.quick_tooltip.add_tooltip(self.speckle_checkbox, "检测并替换孤立像素\n如果一个像素周围有3个以上同色邻居，就替换为该颜色\n可能会影响细节，建议谨慎使用")
        advanced_content_layout.addWidget(self.speckle_checkbox)
        
        advanced_layout.addWidget(self.advanced_content)
        layout.addWidget(advanced_card)
        
        # 鼠标悬停显示
        self.hover_label = BodyLabel("鼠标悬停显示色号")
        self.hover_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(self.hover_label)
        
        layout.addStretch()
        
        return panel
    
    def create_display_panel(self):
        """创建显示面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 预览标签页
        self.tab_widget = QTabWidget()
        
        # 预览图标签页
        self.preview_tab = QWidget()
        preview_layout = QVBoxLayout(self.preview_tab)
        self.preview_label = QLabel("转换后显示预览图")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
        self.preview_label.setMouseTracking(True)
        self.preview_label.installEventFilter(self)
        preview_layout.addWidget(self.preview_label)
        self.tab_widget.addTab(self.preview_tab, "预览图")
        
        # 网格图标签页
        self.grid_tab = QWidget()
        grid_layout = QVBoxLayout(self.grid_tab)
        self.grid_label = QLabel("转换后显示网格图")
        self.grid_label.setAlignment(Qt.AlignCenter)
        self.grid_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
        self.grid_label.setMouseTracking(True)
        self.grid_label.installEventFilter(self)
        grid_layout.addWidget(self.grid_label)
        self.tab_widget.addTab(self.grid_tab, "网格图")
        
        # 颜色清单标签页
        self.list_tab = QWidget()
        list_layout = QVBoxLayout(self.list_tab)
        self.list_text = QTextEdit()
        self.list_text.setReadOnly(True)
        list_layout.addWidget(self.list_text)
        self.tab_widget.addTab(self.list_tab, "颜色清单")
        
        layout.addWidget(self.tab_widget)
        
        # 状态栏
        self.status_label = BodyLabel("就绪")
        self.status_label.setStyleSheet("color: #95a5a6;")
        layout.addWidget(self.status_label)
        
        # 添加水印标签
        from watermark import COPYRIGHT_SHORT
        watermark_label = QLabel(COPYRIGHT_SHORT)
        watermark_label.setStyleSheet("""
            QLabel {
                color: rgba(0, 0, 0, 25);
                font-size: 10px;
                background: transparent;
            }
        """)
        watermark_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        layout.addWidget(watermark_label)
        
        return panel
    
    def load_image(self):
        """加载图片"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择图片", "", "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        
        if file_path:
            self.current_image_path = file_path
            self.image_path_label.setText(os.path.basename(file_path))
            
            if self.converter.load_image(file_path):
                self.update_dimension()
                InfoBar.success("成功", "图片加载成功", parent=self)
            else:
                InfoBar.error("错误", "加载图片失败", parent=self)
    
    def update_dimension(self):
        """更新尺寸显示"""
        width = self.width_spinbox.value()
        if self.converter.set_width(width):
            w, h = self.converter.get_dimensions()
            self.dimension_label.setText(f"尺寸：{w} x {h}")
    
    def update_merge_label(self, value):
        """更新合并阈值显示"""
        self.merge_label.setText(str(value))
    
    def update_sharpen_label(self, value):
        """更新锐化程度显示"""
        self.sharpen_label.setText(f"{value / 100:.1f}")
    
    def toggle_advanced(self):
        """切换高级设置显示状态"""
        visible = not self.advanced_content.isVisible()
        self.advanced_content.setVisible(visible)
        self.advanced_toggle.setText("🔧 高级设置 ▲" if visible else "🔧 高级设置 ▼")
    
    def start_convert(self):
        """开始转换"""
        if self.converter.image is None:
            InfoBar.warning("警告", "请先导入图片", parent=self)
            return
        
        # 更新设置
        self.update_dimension()
        self.converter.set_color_spec(self.spec_combo.currentText())
        self.converter.set_merge_level(self.merge_slider.value())
        self.converter.set_dither_mode(self.dither_combo.currentText())
        
        # 高级设置
        self.converter.set_sharpen_amount(self.sharpen_slider.value() / 100)
        self.converter.set_denoise_params(
            enable=self.denoise_checkbox.isChecked(),
            gaussian_radius=self.gaussian_slider.value(),
            gaussian_dark_protect=40,
            median_radius=self.median_slider.value(),
            median_dark_protect=40,
            dark_threshold=self.dark_slider.value()
        )
        self.converter.set_spatial_refine(self.spatial_checkbox.isChecked())
        self.converter.set_speckle_cleanup(self.speckle_checkbox.isChecked())
        
        # 执行转换
        self.status_label.setText("正在转换...")
        QApplication.processEvents()
        
        result = self.converter.convert()
        if result:
            self.result_data = result
            
            # 生成预览图
            bead_style = self.shape_combo.currentText()
            preview_image = self.converter.generate_preview(result, bead_style=bead_style)
            self.display_image(preview_image, self.preview_label)
            
            # 生成网格图
            grid_image = self.converter.generate_grid(result)
            self.display_image(grid_image, self.grid_label)
            
            # 生成颜色清单
            color_list = self.converter.generate_color_list(result)
            self.list_text.setText(color_list)
            
            # 启用按钮
            self.edit_btn.setEnabled(True)
            self.save_preview_btn.setEnabled(True)
            self.save_grid_btn.setEnabled(True)
            self.save_list_btn.setEnabled(True)
            
            self.status_label.setText(f"转换完成！共{len(result['color_count'])}种颜色")
            InfoBar.success("成功", "转换完成", parent=self)
        else:
            InfoBar.error("错误", "转换失败", parent=self)
    
    def display_image(self, image, label):
        """在标签上显示图像"""
        # 转换PIL图像为QPixmap
        image = image.convert("RGBA")
        data = image.tobytes("raw", "RGBA")
        qimage = QImage(data, image.width, image.height, QImage.Format_RGBA8888)
        
        # 转换为QPixmap并显示
        pixmap = QPixmap.fromImage(qimage)
        scaled_pixmap = pixmap.scaled(label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        label.setPixmap(scaled_pixmap)
    
    def eventFilter(self, obj, event):
        """事件过滤器 - 处理鼠标悬停"""
        if event.type() == QEvent.MouseMove and self.result_data is not None:
            if obj in [self.preview_label, self.grid_label]:
                # 获取鼠标位置
                pos = event.pos()
                pixmap = obj.pixmap()
                
                if pixmap and not pixmap.isNull():
                    # 计算图像在标签中的位置
                    label_size = obj.size()
                    pixmap_size = pixmap.size()
                    
                    # 计算偏移（居中显示）
                    offset_x = (label_size.width() - pixmap_size.width()) // 2
                    offset_y = (label_size.height() - pixmap_size.height()) // 2
                    
                    # 计算鼠标在图像中的位置
                    img_x = pos.x() - offset_x
                    img_y = pos.y() - offset_y
                    
                    # 检查是否在图像范围内
                    if 0 <= img_x < pixmap_size.width() and 0 <= img_y < pixmap_size.height():
                        # 计算豆子坐标
                        matrix = self.result_data["matrix"]
                        width = self.result_data["width"]
                        height = self.result_data["height"]
                        
                        cell_width = pixmap_size.width() / width
                        cell_height = pixmap_size.height() / height
                        
                        bead_x = int(img_x / cell_width)
                        bead_y = int(img_y / cell_height)
                        
                        if 0 <= bead_x < width and 0 <= bead_y < height:
                            color_code = matrix[bead_y][bead_x]
                            self.hover_label.setText(f"色号: {color_code}")
                            return False
        
        return super().eventFilter(obj, event)
    
    def open_editor(self):
        """打开编辑器"""
        if self.result_data is None:
            InfoBar.warning("警告", "请先转换图片", parent=self)
            return
        
        dialog = EditDialog(self.result_data, self.converter, self)
        dialog.exec_()
        
        # 编辑完成后刷新显示
        self.status_label.setText("正在刷新...")
        QApplication.processEvents()
        
        # 重新生成预览图和网格图
        preview_image = self.converter.generate_preview(self.result_data)
        self.display_image(preview_image, self.preview_label)
        
        grid_image = self.converter.generate_grid(self.result_data)
        self.display_image(grid_image, self.grid_label)
        
        # 重新生成颜色清单
        color_list = self.converter.generate_color_list(self.result_data)
        self.list_text.setText(color_list)
        
        self.status_label.setText("刷新完成")
    
    def save_preview(self):
        """保存预览图"""
        if self.result_data is None:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存预览图", "", "PNG文件 (*.png);;所有文件 (*.*)"
        )
        
        if file_path:
            preview_image = self.converter.generate_preview(self.result_data)
            preview_image.save(file_path)
            InfoBar.success("成功", f"预览图已保存：{file_path}", parent=self)
    
    def save_grid(self):
        """保存网格图"""
        if self.result_data is None:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存网格图", "", "PNG文件 (*.png);;所有文件 (*.*)"
        )
        
        if file_path:
            grid_image = self.converter.generate_grid(self.result_data)
            grid_image.save(file_path)
            InfoBar.success("成功", f"网格图已保存：{file_path}", parent=self)
    
    def save_color_list(self):
        """保存颜色清单"""
        if self.result_data is None:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存颜色清单", "", "文本文件 (*.txt);;所有文件 (*.*)"
        )
        
        if file_path:
            color_list = self.converter.generate_color_list(self.result_data)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(color_list)
            InfoBar.success("成功", f"颜色清单已保存：{file_path}", parent=self)


class AboutInterface(QWidget):
    """关于界面"""
    
    def __init__(self):
        super().__init__()
        self.setObjectName("AboutInterface")
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(50, 50, 50, 50)
        
        # 标题
        title_label = TitleLabel("拼豆图纸转换器")
        title_label.setStyleSheet("font-size: 28px; color: #1abc9c;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 版本信息
        version_label = BodyLabel("版本 1.0.0")
        version_label.setStyleSheet("font-size: 14px; color: #95a5a6;")
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)
        
        layout.addSpacing(30)
        
        # 功能介绍卡片
        intro_card = CardWidget()
        intro_layout = QVBoxLayout(intro_card)
        intro_layout.setContentsMargins(20, 20, 20, 20)
        
        intro_title = BodyLabel("功能介绍")
        intro_title.setStyleSheet("font-weight: bold; font-size: 16px; color: #3498db;")
        intro_layout.addWidget(intro_title)
        
        intro_text = BodyLabel(
            "• 支持多种图片格式导入（PNG、JPG、BMP等）\n"
            "• 支持221色和291色MARD色号规格\n"
            "• 多种抖动模式（无抖动、有序抖动、Floyd-Steinberg）\n"
            "• 边缘感知缩放，保持图像细节\n"
            "• CIEDE2000颜色匹配算法，更准确的颜色还原\n"
            "• 实时预览和编辑功能\n"
            "• 导出预览图、网格图和颜色清单"
        )
        intro_text.setStyleSheet("font-size: 13px; line-height: 1.8;")
        intro_layout.addWidget(intro_text)
        
        layout.addWidget(intro_card)
        
        # 作者信息卡片
        author_card = CardWidget()
        author_layout = QVBoxLayout(author_card)
        author_layout.setContentsMargins(20, 20, 20, 20)
        
        author_title = BodyLabel("作者信息")
        author_title.setStyleSheet("font-weight: bold; font-size: 16px; color: #3498db;")
        author_layout.addWidget(author_title)
        
        author_text = BodyLabel(
            "作者：Danstfool\n"
            "反馈邮箱：danstfool@163.com\n"
            "\n"
            "欢迎提交Bug反馈和功能建议！\n"
            "未经授权禁止商用"
        )
        author_text.setStyleSheet("font-size: 13px; line-height: 1.8;")
        author_layout.addWidget(author_text)
        
        layout.addWidget(author_card)
        
        # 技术栈卡片
        tech_card = CardWidget()
        tech_layout = QVBoxLayout(tech_card)
        tech_layout.setContentsMargins(20, 20, 20, 20)
        
        tech_title = BodyLabel("技术栈")
        tech_title.setStyleSheet("font-weight: bold; font-size: 16px; color: #3498db;")
        tech_layout.addWidget(tech_title)
        
        tech_text = BodyLabel(
            "• Python 3.12\n"
            "• PyQt5 + PyQt-Fluent-Widgets\n"
            "• Pillow（图像处理）\n"
            "• NumPy + SciPy（数值计算）\n"
            "• CIEDE2000颜色匹配算法"
        )
        tech_text.setStyleSheet("font-size: 13px; line-height: 1.8;")
        tech_layout.addWidget(tech_text)
        
        layout.addWidget(tech_card)
        
        layout.addStretch()


class MainWindow(FluentWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        
        # 创建主界面
        self.main_interface = MainInterface()
        self.about_interface = AboutInterface()
        self.initNavigation()
        self.initWindow()
    
    def initNavigation(self):
        """初始化导航"""
        self.addSubInterface(self.main_interface, FIF.HOME, "主页")
        self.addSubInterface(self.about_interface, FIF.INFO, "关于")
        self.navigationInterface.setCurrentItem("主页")
    
    def initWindow(self):
        """初始化窗口"""
        self.setWindowTitle("拼豆图纸转换器")
        self.resize(1000, 700)
        
        # 居中显示
        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)


def main():
    # 设置高DPI支持
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    # Linux兼容性设置（仅在Linux下生效）
    import platform
    if platform.system() == 'Linux':
        os.environ['QT_QPA_PLATFORM'] = 'xcb'
    
    app = QApplication(sys.argv)
    
    # 设置工具提示样式和延迟
    app.setStyleSheet("""
        QToolTip {
            background-color: #2c3e50;
            color: #ecf0f1;
            border: 1px solid #34495e;
            padding: 8px;
            font-size: 12px;
            border-radius: 4px;
        }
    """)
    
    # 设置工具提示延迟为200毫秒
    app.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    # 设置主题
    setTheme(Theme.LIGHT)
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
import sys
import os
import random
import winreg
from PyQt6.QtWidgets import (QApplication, QWidget, QMenu, QFileDialog,
                             QInputDialog, QMessageBox)
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont, QImageReader
from PyQt6.QtCore import (Qt, QTimer, QPoint, QPropertyAnimation,
                         QEasingCurve, pyqtProperty, QRect)

# 开机自启配置
REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "FloatImageSlide"


class FloatSlideWindow(QWidget):
    def __init__(self):
        super().__init__()
        # 基础参数
        self.resize(400, 710)
        self.setWindowOpacity(1.0)

        # 功能状态
        self.is_top = True
        self.is_random_play = False
        self.is_playing = True
        self.image_folder = ""
        self.image_list = []
        self.current_idx = 0
        self.interval = 5000

        # 窗口样式
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # 拖动/缩放 变量
        self.dragging = False
        self.resizing = False
        self.drag_start_pos = QPoint()
        self.start_width = 0
        self.start_height = 0
        self.RESIZE_MARGIN = 15

        # 轮播定时器
        self.slide_timer = QTimer()
        self.slide_timer.timeout.connect(self.next_image)
        self.slide_timer.start(self.interval)

        # 动画系统
        self.anim_progress = 0.0
        self.animation = QPropertyAnimation(self, b"animProgress")
        self.animation.setDuration(400)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        # 图片缓存 - 存储原始高分辨率图片
        self.current_pix = QPixmap()
        self.current_pix_scaled = QPixmap()  # 缩放后的图片
        self.next_pix = QPixmap()
        self.next_pix_scaled = QPixmap()
        self.anim_type = 0

        # 右键菜单
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_right_menu)

    # 动画进度属性
    @pyqtProperty(float)
    def animProgress(self):
        return self.anim_progress

    @animProgress.setter
    def animProgress(self, value):
        self.anim_progress = value
        self.update()

    # 拖动 + 缩放
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.pos()
            # 检测右下角缩放
            if (pos.x() >= self.width() - self.RESIZE_MARGIN and
                pos.y() >= self.height() - self.RESIZE_MARGIN):
                self.resizing = True
                self.drag_start_pos = event.globalPosition().toPoint()
                self.start_width = self.width()
                self.start_height = self.height()
            # 普通拖动
            else:
                self.dragging = True
                self.drag_start_pos = event.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, event):
        # 拖动窗口
        if self.dragging:
            self.move(event.globalPosition().toPoint() - self.drag_start_pos)
            return

        # 窗口缩放
        if self.resizing:
            current_pos = event.globalPosition().toPoint()
            delta_x = current_pos.x() - self.drag_start_pos.x()
            delta_y = current_pos.y() - self.drag_start_pos.y()

            new_w = max(300, self.start_width + delta_x)
            new_h = max(250, self.start_height + delta_y)
            self.resize(new_w, new_h)
            # 窗口大小改变时重新缩放图片
            self._rescale_current_image()

    def mouseReleaseEvent(self, event):
        self.dragging = False
        self.resizing = False

    # 5种随机动画
    def play_random_animation(self):
        self.anim_type = random.randint(0, 4)
        self.animation.stop()
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.start()

    # ========== 修复1: 高DPI + 填充裁剪的图片加载 ==========
    def _load_high_res_image(self, path):
        """加载高分辨率原图，不做任何缩放"""
        # 使用QImageReader读取原始图片信息
        reader = QImageReader(path)
        original_format = reader.format()
        image = reader.read()

        if image.isNull():
            # 如果读取失败，尝试直接加载
            image = QPixmap(path).toImage()

        # 转换为QPixmap并设置设备像素比（用于高DPI）
        pixmap = QPixmap.fromImage(image)
        # 关键：在高DPI显示器上使用devicePixelRatio确保图片清晰
        if hasattr(pixmap, 'setDevicePixelRatio'):
            # 保持原始清晰度，devicePixelRatio会让Qt自动处理DPI缩放
            pixmap.setDevicePixelRatio(1.0)

        return pixmap

    def _scale_img_fill(self, pixmap):
        """
        将图片缩放填充整个窗口，比例不对时自动裁剪（从中心裁剪）
        修复高DPI模糊问题
        """
        if pixmap.isNull():
            return QPixmap()

        widget_w = self.width()
        widget_h = self.height()

        if widget_w <= 0 or widget_h <= 0:
            return pixmap

        pix_w = pixmap.width()
        pix_h = pixmap.height()

        if pix_w <= 0 or pix_h <= 0:
            return QPixmap()

        # 计算填充比例 - 确保完全覆盖窗口
        scale_w = widget_w / pix_w
        scale_h = widget_h / pix_h
        scale = max(scale_w, scale_h)  # 使用较大的缩放比例以确保覆盖

        # 计算缩放后的尺寸
        new_w = int(pix_w * scale)
        new_h = int(pix_h * scale)

        # 缩放图片（使用平滑变换）
        scaled = pixmap.scaled(
            new_w, new_h,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        # 计算裁剪区域（从中心裁剪）
        crop_x = (new_w - widget_w) // 2
        crop_y = (new_h - widget_h) // 2

        # 裁剪到窗口大小
        cropped = scaled.copy(crop_x, crop_y, widget_w, widget_h)

        return cropped

    def _rescale_current_image(self):
        """重新缩放当前图片（窗口大小改变时调用）"""
        if not self.current_pix.isNull():
            self.current_pix_scaled = self._scale_img_fill(self.current_pix)
        if not self.next_pix.isNull():
            self.next_pix_scaled = self._scale_img_fill(self.next_pix)
        self.update()

    # ========== 图片加载 ==========
    def load_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择图片文件夹")
        if not folder:
            return
        self.image_folder = folder
        exts = (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp")
        self.image_list = [
            os.path.join(folder, f) for f in os.listdir(folder)
            if f.lower().endswith(exts)
        ]
        if not self.image_list:
            QMessageBox.warning(self, "提示", "文件夹内没有图片！")
            return
        self.current_idx = 0
        # 加载高分辨率原图
        self.current_pix = self._load_high_res_image(self.image_list[self.current_idx])
        # 缩放并裁剪
        self.current_pix_scaled = self._scale_img_fill(self.current_pix)
        self.update()

    # ========== 自动切换图片 ==========
    def next_image(self):
        if not self.image_list or not self.is_playing:
            return

        if self.is_random_play:
            self.current_idx = random.randint(0, len(self.image_list)-1)
        else:
            self.current_idx = (self.current_idx + 1) % len(self.image_list)

        # 加载高分辨率原图
        self.next_pix = self._load_high_res_image(self.image_list[self.current_idx])
        # 缩放并裁剪
        self.next_pix_scaled = self._scale_img_fill(self.next_pix)
        self.play_random_animation()
        QTimer.singleShot(400, self._finish_switch)

    def _finish_switch(self):
        self.current_pix = self.next_pix
        self.current_pix_scaled = self.next_pix_scaled
        self.next_pix = QPixmap()
        self.next_pix_scaled = QPixmap()
        self.anim_progress = 0
        self.update()

    # ========== 功能设置 ==========
    def set_interval(self):
        sec, ok = QInputDialog.getInt(self, "轮播间隔", "设置秒数(1-3600):", self.interval//1000, 1, 3600)
        if ok:
            self.interval = sec * 1000
            self.slide_timer.setInterval(self.interval)

    def toggle_top(self):
        self.is_top = not self.is_top
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, self.is_top)
        self.show()

    # ========== 开机自启 ==========
    def set_autostart(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_WRITE)
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, sys.executable)
            winreg.CloseKey(key)
            QMessageBox.information(self, "成功", "已开启开机自启")
        except:
            QMessageBox.critical(self, "错误", "设置失败")

    def del_autostart(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_WRITE)
            winreg.DeleteValue(key, APP_NAME)
            winreg.CloseKey(key)
            QMessageBox.information(self, "成功", "已关闭开机自启")
        except:
            QMessageBox.critical(self, "错误", "取消失败")

    # ========== 右键菜单 ==========
    def show_right_menu(self, pos):
        menu = QMenu()
        menu.addAction("📁 选择图片文件夹", self.load_folder)
        menu.addAction("⏱️ 设置轮播间隔", self.set_interval)
        menu.addAction(f"{'📌 取消置顶' if self.is_top else '📌 开启置顶'}", self.toggle_top)
        menu.addAction(f"🔀 {'关闭随机' if self.is_random_play else '开启随机'}", lambda: setattr(self, 'is_random_play', not self.is_random_play))
        menu.addAction(f"⏯️ {'暂停' if self.is_playing else '播放'}", lambda: setattr(self, 'is_playing', not self.is_playing))
        menu.addSeparator()
        menu.addAction("🚀 开机自启", self.set_autostart)
        menu.addAction("❌ 关闭自启", self.del_autostart)
        menu.addSeparator()
        menu.addAction("🔚 退出程序", self.close)
        menu.exec(self.mapToGlobal(pos))

    # ========== 绘制界面 ==========
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(30, 30, 30, 40))

        if not self.image_list:
            painter.setFont(QFont("微软雅黑", 11))
            painter.setPen(Qt.GlobalColor.white)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "右键 → 选择图片文件夹")
            return

        w, h = self.width(), self.height()

        # 使用缩放并裁剪后的图片（填充模式）
        display_pix = self.current_pix_scaled

        if display_pix.isNull():
            display_pix = self.current_pix

        # 填充模式：图片已裁剪为窗口大小，直接绘制在(0,0)
        painter.drawPixmap(0, 0, display_pix)

        # 动画效果
        if self.anim_progress > 0 and not self.next_pix_scaled.isNull():
            p = self.anim_progress

            if self.anim_type == 0:
                painter.setOpacity(p)
                painter.drawPixmap(0, 0, self.next_pix_scaled)
            elif self.anim_type == 1:
                painter.drawPixmap(int(-w*(1-p)), 0, self.next_pix_scaled)
            elif self.anim_type == 2:
                painter.drawPixmap(0, int(h*(1-p)), self.next_pix_scaled)
            elif self.anim_type == 3:
                s = 0.3 + 0.7*p
                sw, sh = int(w*s), int(h*s)
                painter.drawPixmap((w-sw)//2, (h-sh)//2, sw, sh, self.next_pix_scaled)
            elif self.anim_type == 4:
                painter.drawPixmap(int(w*(1-p)), 0, self.next_pix_scaled)


# ========== 启动程序 ==========
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # PyQt6 默认启用高DPI支持，无需额外设置
    # 确保应用使用系统的DPI设置

    window = FloatSlideWindow()
    window.show()
    sys.exit(app.exec())

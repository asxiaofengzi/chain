from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, QMutex
from PyQt5.QtGui import QImage, QPixmap, QPainter, QColor, QFont
import cv2
import numpy as np

class CameraWidget(QWidget):
    def __init__(self, camera_id=0, parent=None):
        super().__init__(parent)
        self.camera_id = camera_id
        self.capture = None
        self.frame = None
        self.mutex = QMutex()
        self.paused = False
        self.title = f"Camera {camera_id + 1}"
        self.show_title = False  # 添加标志控制是否显示标题
        self.video_file_mode = False  # 标记是否为视频文件模式
        
        # 设置标签用于显示视频
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(4, 4, 4, 4)  # 减少边距
        self.camera_label = QLabel()
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.camera_label)
        
        # 设置样式
        self.setStyleSheet("""
            QWidget {
                background-color: #2D2D30;
                border-radius: 6px;
            }
            QLabel {
                border: 1px solid #3E3E42;
                border-radius: 4px;
                background-color: #252525;
                color: white;
            }
        """)
        
        # 显示初始提示
        self.show_placeholder()
    
    def show_placeholder(self):
        """显示占位提示"""
        # 创建一个空白图像
        blank_image = np.zeros((480, 640, 3), dtype=np.uint8)
        blank_image.fill(40)  # 深灰色背景
        
        # 在图像中心添加文字
        font = cv2.FONT_HERSHEY_SIMPLEX
        text = self.title
        font_scale = 1.5  # 增大字体比例
        text_size = cv2.getTextSize(text, font, font_scale, 2)[0]
        text_x = (blank_image.shape[1] - text_size[0]) // 2
        text_y = (blank_image.shape[0] + text_size[1]) // 2
        cv2.putText(blank_image, text, (text_x, text_y), font, font_scale, (200, 200, 200), 2, cv2.LINE_AA)
        
        # 将占位图显示在组件上
        self.update_image(blank_image)
    
    def start(self):
        """启动摄像头"""
        try:
            # 如果已经有打开的摄像头，先关闭
            if self.capture is not None:
                self.capture.release()
                self.capture = None
            
            # 启动摄像头后显示标题
            self.show_title = True
            
            # 方法1: 直接使用索引打开
            self.capture = cv2.VideoCapture(self.camera_id)
            
            if not self.capture.isOpened():
                print(f"方法1失败: 无法打开摄像头 {self.camera_id}")
                
                # 方法2: 使用DirectShow尝试打开
                self.capture = cv2.VideoCapture(self.camera_id, cv2.CAP_DSHOW)
                
                if not self.capture.isOpened():
                    print(f"方法2失败: 无法使用DirectShow打开摄像头 {self.camera_id}")
                    
                    # 方法3: 使用默认的摄像头
                    self.capture = cv2.VideoCapture(0)
                    
                    if not self.capture.isOpened():
                        print("方法3失败: 无法打开默认摄像头")
                        return False
            
            # 设置摄像头参数 (可选)
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 1024)
            
            # 读取一帧测试是否正常
            ret, frame = self.capture.read()
            if not ret:
                print(f"无法从摄像头读取图像")
                self.capture.release()
                self.capture = None
                return False
            
            print(f"成功打开摄像头 ID: {self.camera_id}")
            print(f"摄像头信息:")
            print(f"- 宽度: {int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))}")
            print(f"- 高度: {int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))}")
            print(f"- FPS: {self.capture.get(cv2.CAP_PROP_FPS)}")
            
            self.paused = False
            return True
        except Exception as e:
            print(f"启动摄像头时出错: {e}")
            if self.capture is not None:
                self.capture.release()
                self.capture = None
            return False
    
    def set_video_file(self, video_path):
        """从视频文件加载视频"""
        try:
            # 如果已经有打开的摄像头或视频，先关闭
            if self.capture is not None:
                self.capture.release()
                self.capture = None
            
            # 使用视频文件
            self.capture = cv2.VideoCapture(video_path)
            
            if not self.capture.isOpened():
                print(f"无法打开视频文件: {video_path}")
                return False
            
            # 标记为视频文件模式
            self.video_file_mode = True
            self.title = f"Video {self.camera_id + 1}"
            self.show_title = True
            
            # 获取并输出视频信息
            width = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = self.capture.get(cv2.CAP_PROP_FPS)
            print(f"成功打开视频文件: {video_path}")
            print(f"视频信息: 分辨率 {width}x{height}, FPS: {fps}")
            
            self.paused = False
            return True
        except Exception as e:
            print(f"设置视频文件时出错: {e}")
            if self.capture is not None:
                self.capture.release()
                self.capture = None
            return False

    def stop(self):
        """停止摄像头或视频"""
        if self.capture is not None:
            self.capture.release()
            self.capture = None
        # 重置视频文件模式
        self.video_file_mode = False
        # 停止显示标题
        self.show_title = False
        # 恢复到占位图
        self.show_placeholder()
    
    def pause(self):
        """暂停摄像头"""
        self.paused = True
    
    def resume(self):
        """恢复摄像头"""
        self.paused = False
    
    def get_frame(self):
        """获取当前帧"""
        if self.capture is None:
            return None
            
        if self.paused and self.frame is not None:
            return self.frame
        
        try:
            ret, frame = self.capture.read()
            if ret:
                self.mutex.lock()
                self.frame = frame
                self.mutex.unlock()
                return frame
            elif self.video_file_mode:
                # 视频文件播放结束，重新开始播放
                print(f"视频 {self.camera_id + 1} 播放结束，重新开始")
                self.capture.set(cv2.CAP_PROP_POS_FRAMES, 0)  # 重置到第一帧
                ret, frame = self.capture.read()
                if ret:
                    self.mutex.lock()
                    self.frame = frame
                    self.mutex.unlock()
                    return frame
        except Exception as e:
            print(f"获取帧时出错: {e}")
            
        return None
    
    def update_image(self, frame):
        """更新显示的图像"""
        if frame is None:
            return
        
        try:
            # 将OpenCV的BGR图像转换为RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # 获取图像尺寸
            height, width, channels = rgb_frame.shape
            
            # 创建QImage
            bytesPerLine = channels * width
            image = QImage(rgb_frame.data, width, height, bytesPerLine, QImage.Format_RGB888)
            
            # 根据窗口大小缩放图像
            pixmap = QPixmap.fromImage(image)
            pixmap = pixmap.scaled(self.camera_label.width(), self.camera_label.height(),
                                  Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            
            # 在图像上添加标题
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # 只在需要显示标题时绘制
            if self.show_title:
                # 绘制半透明背景
                painter.fillRect(0, 0, pixmap.width(), 35, QColor(0, 0, 0, 150))
                
                # 设置字体
                font = QFont("Arial", 14, QFont.Bold)
                painter.setFont(font)
                
                # 绘制文本
                painter.setPen(Qt.white)
                painter.drawText(12, 24, self.title)
            
            painter.end()
            
            # 设置图像
            self.camera_label.setPixmap(pixmap)
        except Exception as e:
            print(f"更新图像时出错: {e}")
    
    def resizeEvent(self, event):
        """窗口大小改变时重新缩放图像"""
        super().resizeEvent(event)
        if self.frame is not None:
            self.update_image(self.frame)
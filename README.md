# 铁链缺陷检测系统

基于PyQt5和YOLOv8的实时多摄像头铁链缺陷检测系统。

## 功能特点

- 同时支持4个摄像头实时视频流显示和检测
- 使用YOLOv8模型进行实时缺陷检测
- 检测到缺陷时自动暂停视频流并发送信号
- 支持缺陷图像标记和保存
- 简洁易用的用户界面

## 系统要求

- Python 3.8+
- CUDA支持的NVIDIA显卡(推荐，但不强制)
- 连接的摄像头设备

## 安装步骤

1. 克隆或下载项目代码

2. 安装依赖
   ```
   pip install -r requirements.txt
   ```

3. 安装自定义YOLOv8模型(可选)
   - 将训练好的YOLOv8模型(.pt文件)放入项目根目录
   - 或修改`app/detector/YoloDetector.py`文件中的模型路径

## 使用说明

1. 启动程序
   ```
   python main.py
   ```

2. 操作流程
   - 点击"开始检测"按钮开始实时检测
   - 检测到缺陷后，系统会自动暂停视频流并显示提示
   - 使用"标记缺陷"按钮标记检测到的缺陷
   - 使用"保存图像"按钮保存当前缺陷图像
   - 点击"停止检测"按钮停止检测过程

## 硬件连接

- 系统支持通过GPIO(树莓派)或串口发送低电平信号
- 默认GPIO引脚为GPIO17，串口为COM3(Windows)
- 可在`app/utils/io_control.py`中修改相关配置

## 自定义开发

- 修改`app/detector/YoloDetector.py`以使用自定义模型
- 调整`app/MainWindow.py`中的UI布局
- 根据硬件情况配置`app/utils/io_control.py` 
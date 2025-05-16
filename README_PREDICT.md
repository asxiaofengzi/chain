# 铁链缺陷批量检测工具

此工具用于批量处理图片并使用YOLOv8模型检测铁链缺陷。

## 功能特点

- 支持批量处理指定文件夹中的所有图片
- 检测所有支持的图片格式（jpg、jpeg、png、bmp、tif）
- 自动生成检测结果CSV报告
- 保存标注后的图片以便可视化
- 可选保存缺陷区域的裁剪图片
- 支持Windows和Linux系统

## 使用方法

### Windows系统

直接通过批处理文件执行：

```
predict_batch.bat [图片目录] [可选:输出目录] [可选:模型路径]
```

例如：

```
predict_batch.bat D:\images D:\results best.pt
```

### Linux系统

确保脚本有执行权限：

```
chmod +x predict_batch.sh
```

然后执行：

```
./predict_batch.sh [图片目录] [可选:输出目录] [可选:模型路径]
```

例如：

```
./predict_batch.sh /home/user/images /home/user/results best.pt
```

### 直接使用Python脚本

也可以直接调用Python脚本，获得更多控制选项：

```
python predict_images.py --input [图片目录] --output [输出目录] --model [模型路径] --conf [置信度阈值] [--no-save] [--crops]
```

参数说明：
- `--input`, `-i`: 输入图片目录（必选）
- `--output`, `-o`: 输出结果目录（默认：results）
- `--model`, `-m`: YOLOv8模型路径（默认：best.pt）
- `--conf`, `-c`: 置信度阈值（默认：0.25）
- `--no-save`: 不保存标注后的图片
- `--crops`: 保存裁剪的缺陷区域

## 输出结果

程序运行后会在指定的输出目录生成以下内容：

1. **results.csv** - 包含所有检测结果的CSV文件，字段包括：
   - 文件名
   - 检测时间(ms)
   - 检测到的缺陷数
   - 类别
   - 置信度
   - 坐标

2. **annotated_xxx.jpg** - 标注了检测框的图片

3. **crops/** - 如果启用了裁剪选项，将包含按原图片名组织的子文件夹，内含每个缺陷的裁剪图像

## 注意事项

1. 确保已安装必要的Python库：
   ```
   pip install ultralytics opencv-python numpy
   ```

2. 对于自定义模型，确保模型文件(.pt)位于正确路径

3. 处理大量图片时可能需要较长时间，请耐心等待 
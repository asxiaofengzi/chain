@echo off
echo 铁链缺陷检测批处理工具
echo =========================

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到Python，请安装Python 3.8或更高版本。
    pause
    exit /b 1
)

REM 检查输入参数
if "%~1"=="" (
    echo 用法: predict_batch.bat [图片目录] [可选:输出目录] [可选:模型路径]
    echo 例如: predict_batch.bat D:\images D:\results best.pt
    pause
    exit /b 1
)

REM 设置参数
set INPUT_DIR=%~1
set OUTPUT_DIR=%~2
set MODEL_PATH=%~3

REM 如果没有指定输出目录，使用默认目录
if "%OUTPUT_DIR%"=="" set OUTPUT_DIR=results

REM 如果没有指定模型路径，使用默认模型
if "%MODEL_PATH%"=="" set MODEL_PATH=best.pt

echo 输入目录: %INPUT_DIR%
echo 输出目录: %OUTPUT_DIR%
echo 模型路径: %MODEL_PATH%
echo.

REM 运行预测脚本
python predict_images.py --input "%INPUT_DIR%" --output "%OUTPUT_DIR%" --model "%MODEL_PATH%" --crops

echo.
echo 处理完成，按任意键退出...
pause 
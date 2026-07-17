# 拼豆图纸转换器/Fuse-bead-generator
一款将图片转换为拼豆图纸的桌面应用程序。

A desktop application that converts ordinary images into fuse bead pattern charts.
## 功能特点/Features
- 支持多种图片格式导入（PNG、JPG、BMP等）
- 支持221色和291色MARD色号规格
- 多种抖动模式（无抖动、有序抖动、Floyd-Steinberg）
- 边缘感知缩放，保持图像细节
- CIEDE2000颜色匹配算法，更准确的颜色还原
- 实时预览和编辑功能
- 导出预览图、网格图和颜色清单

-Supports importing multiple image formats: PNG, JPG, BMP, etc.
-Compatible with two standard MARD bead palettes: 221-color & 291-color sets
-CIEDE2000 color difference algorithm for high-precision color matching & restoration
-Real-time canvas preview and interactive pattern editing
-Multi-file export options: render preview, grid bead graph, color material list

## 下载/Download

从 Releases 页面下载对应平台的版本：
Download the build for your OS from the Releases page.
- **Windows**: `拼豆图纸转换器-Windows.exe`
- **macOS**: `拼豆图纸转换器-macOS`
- **Linux**: `拼豆图纸转换器-Linux`

## 使用方法

1. 下载对应平台的可执行文件
2. 双击运行
3. 导入图片
4. 调整参数（宽度、色号规格、抖动模式等）
5. 点击"开始转换"
6. 保存预览图、网格图或颜色清单

## 功能说明

### 基本设置
- **宽度**：设置输出图纸的宽度（格子数），高度自动计算
- **色号规格**：221色（标准）或291色（完整）
- **抖动模式**：无抖动、有序抖动、Floyd-Steinberg误差扩散
- **颜色合并**：合并相似颜色，减少颜色种类

### 高级设置
- **豆子形状**：圆形或方形
- **锐化程度**：增强图像边缘清晰度
- **降噪设置**：高斯模糊、中值滤波、深色阈值
- **ICM空间平滑**：减少杂色点
- **噪点清理**：清除孤立像素

### 编辑功能
- 左键点击选择/取消选择点
- 左键拖动连续选择
- 右键拖动移动图像
- 滚轮缩放
- 应用颜色到选中点

## 技术栈

- Python
- Python 3.11
- PyQt5 + PyQt-Fluent-Widgets
- Pillow
- NumPy + SciPy
- CIEDE2000颜色匹配算法

## 作者
- 作者：Danstfool
## 版权
版权所有 © 2026 Danstfool
未经许可禁止商用

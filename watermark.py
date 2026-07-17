"""
水印模块 - 实现图像水印和LSB隐写
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont


# 版权信息
COPYRIGHT_TEXT = "拼豆图纸转换器 v1.0.0 | 作者:Danstfool | 邮箱:danstfool@163.com | 版权所有©2026王凯文 | 未经许可禁止商用"
COPYRIGHT_SHORT = "©2026 Danstfool | 未经许可禁止商用"


def text_to_binary(text):
    """将文本转换为二进制字符串（使用UTF-8编码）"""
    # 将文本编码为UTF-8字节
    utf8_bytes = text.encode('utf-8')
    # 转换为二进制字符串
    binary = ''.join(format(byte, '08b') for byte in utf8_bytes)
    # 添加结束标记（8位全0）
    binary += '00000000'
    return binary


def binary_to_text(binary):
    """将二进制字符串转换为文本（使用UTF-8解码）"""
    # 提取字节
    bytes_list = []
    for i in range(0, len(binary), 8):
        if i + 8 > len(binary):
            break
        byte = binary[i:i+8]
        if byte == '00000000':
            break
        bytes_list.append(int(byte, 2))
    
    # 将字节解码为UTF-8文本
    try:
        return bytes(bytes_list).decode('utf-8')
    except:
        return None


def embed_lsb(image, text):
    """
    使用LSB隐写术在图像中嵌入文本
    
    Args:
        image: PIL Image对象
        text: 要嵌入的文本
    
    Returns:
        嵌入水印后的PIL Image对象
    """
    # 转换为numpy数组
    img_array = np.array(image)
    
    # 获取图像尺寸
    height, width, channels = img_array.shape
    
    # 将文本转换为二进制
    binary_text = text_to_binary(text)
    text_length = len(binary_text)
    
    # 检查图像是否足够大
    max_bits = height * width * channels
    if text_length > max_bits:
        print(f"警告：文本太长（{text_length}位），图像最多容纳{max_bits}位")
        return image
    
    # 展平图像数组
    flat_array = img_array.flatten()
    
    # 嵌入文本长度（32位）
    length_binary = format(text_length, '032b')
    for i in range(32):
        # 清除最低位，然后设置新值
        flat_array[i] = (flat_array[i] & 0xFE) | int(length_binary[i])
    
    # 嵌入文本内容
    for i in range(text_length):
        # 清除最低位，然后设置新值
        flat_array[i + 32] = (flat_array[i + 32] & 0xFE) | int(binary_text[i])
    
    # 恢复图像形状
    result_array = flat_array.reshape(img_array.shape)
    
    # 转换回PIL Image
    result_image = Image.fromarray(result_array.astype(np.uint8))
    
    return result_image


def extract_lsb(image):
    """
    从图像中提取LSB隐写的文本
    
    Args:
        image: PIL Image对象
    
    Returns:
        提取的文本，如果失败返回None
    """
    # 转换为numpy数组
    img_array = np.array(image)
    
    # 展平图像数组
    flat_array = img_array.flatten()
    
    # 提取文本长度（32位）
    length_binary = ''
    for i in range(32):
        length_binary += str(flat_array[i] & 1)
    text_length = int(length_binary, 2)
    
    # 检查长度是否合理
    if text_length <= 0 or text_length > len(flat_array) - 32:
        return None
    
    # 提取文本内容
    binary_text = ''
    for i in range(text_length):
        binary_text += str(flat_array[i + 32] & 1)
    
    # 转换为文本
    text = binary_to_text(binary_text)
    
    return text


def add_visible_watermark(image, text=None, opacity=30):
    """
    在图像上添加半透明可见水印
    
    Args:
        image: PIL Image对象
        text: 水印文本，默认为版权信息
        opacity: 水印透明度（0-255）
    
    Returns:
        添加水印后的PIL Image对象
    """
    if text is None:
        text = COPYRIGHT_SHORT
    
    # 转换为RGBA模式
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    # 创建水印层
    watermark = Image.new('RGBA', image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(watermark)
    
    # 尝试加载字体
    try:
        font = ImageFont.truetype("arial.ttf", 12)
    except:
        font = ImageFont.load_default()
    
    # 计算文字大小
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # 在多个位置添加水印（对角线排列）
    width, height = image.size
    spacing = max(text_width + 50, 200)
    
    for y in range(0, height, spacing):
        for x in range(0, width, spacing):
            draw.text((x, y), text, fill=(255, 255, 255, opacity), font=font)
    
    # 合并图层
    result = Image.alpha_composite(image, watermark)
    
    # 转换回RGB模式
    if result.mode == 'RGBA':
        result = result.convert('RGB')
    
    return result


def add_gui_watermark(widget):
    """
    在GUI界面上添加水印标签
    
    Args:
        widget: 父控件
    """
    from PyQt5.QtWidgets import QLabel
    from PyQt5.QtCore import Qt
    
    watermark_label = QLabel(COPYRIGHT_SHORT, widget)
    watermark_label.setStyleSheet("""
        QLabel {
            color: rgba(0, 0, 0, 30);
            font-size: 10px;
            background: transparent;
        }
    """)
    watermark_label.setAlignment(Qt.AlignBottom | Qt.AlignRight)
    watermark_label.setGeometry(widget.width() - 200, widget.height() - 20, 200, 20)
    
    return watermark_label


if __name__ == "__main__":
    # 测试LSB隐写
    print("测试LSB隐写功能...")
    
    # 创建测试图像
    test_image = Image.new("RGB", (100, 100), (128, 128, 128))
    
    # 嵌入文本
    test_text = "Test Watermark"
    embedded_image = embed_lsb(test_image, test_text)
    
    # 提取文本
    extracted_text = extract_lsb(embedded_image)
    
    print(f"Original: {test_text}")
    print(f"Extracted: {extracted_text}")
    print(f"Match: {test_text == extracted_text}")
    
    # 测试可见水印
    print("\n测试可见水印功能...")
    watermarked_image = add_visible_watermark(test_image)
    watermarked_image.save("test_watermark.png")
    print("水印图像已保存：test_watermark.png")
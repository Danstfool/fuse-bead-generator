"""
拼豆图纸转换器 - 核心转换模块
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
from scipy import ndimage
from mard_colors import (
    MARD_COLORS_HEX, MARD_221_COLORS, MARD_291_COLORS,
    hex_to_rgb, rgb_to_hex, get_color_rgb, find_nearest_color, color_distance
)
from image_processor import process_image
from color_lookup import build_lookup_table, get_lookup_table
from watermark import embed_lsb, COPYRIGHT_TEXT

class PerlerBeadConverter:
    def __init__(self):
        self.image = None
        self.width = 0
        self.height = 0
        self.bead_width = 0
        self.bead_height = 0
        self.color_spec = "221"
        self.merge_level = 0
        
        # 降噪参数
        self.gaussian_radius = 0
        self.gaussian_dark_protect = 40
        self.median_radius = 1
        self.median_dark_protect = 40
        self.dark_threshold = 40
        self.enable_denoise = False
        
        # 新处理参数
        self.dither_mode = "none"  # "none", "ordered", "floyd"
        self.sharpen_amount = 0.3  # 0-1，锐化程度
        self.enable_spatial_refine = False  # ICM空间平滑
        self.enable_speckle_cleanup = False  # 噪点清理
        
    def load_image(self, image_path):
        """加载图片"""
        try:
            self.image = Image.open(image_path).convert("RGB")
            return True
        except Exception as e:
            print(f"加载图片失败: {e}")
            return False
    
    def set_width(self, width):
        """设置宽度，自动计算高度"""
        if self.image is None:
            return False
        
        self.bead_width = width
        img_width, img_height = self.image.size
        ratio = img_height / img_width
        self.bead_height = int(width * ratio)
        
        return True
    
    def get_dimensions(self):
        """获取转换后的尺寸"""
        return self.bead_width, self.bead_height
    
    def set_color_spec(self, spec):
        """设置色号规格 (221 或 291)"""
        if spec in ["221", "291"]:
            self.color_spec = spec
            return True
        return False
    
    def set_merge_level(self, level):
        """设置颜色合并级别（0-100的整数值）"""
        if isinstance(level, int) and 0 <= level <= 100:
            self.merge_level = level
            return True
        return False
    
    def set_denoise_params(self, enable=False, gaussian_radius=0, gaussian_dark_protect=40,
                           median_radius=1, median_dark_protect=40, dark_threshold=40):
        """设置降噪参数
        
        Args:
            enable: 是否启用降噪
            gaussian_radius: 高斯模糊半径（0表示不模糊）
            gaussian_dark_protect: 高斯模糊深色保护（0-100）
            median_radius: 中值滤波半径
            median_dark_protect: 中值滤波深色保护（0-100）
            dark_threshold: 深色阈值（0-100）
        """
        self.enable_denoise = enable
        self.gaussian_radius = gaussian_radius
        self.gaussian_dark_protect = gaussian_dark_protect
    
    def set_dither_mode(self, mode):
        """设置抖动模式
        
        Args:
            mode: "none", "ordered", "floyd"
        """
        if mode in ["none", "ordered", "floyd"]:
            self.dither_mode = mode
    
    def set_sharpen_amount(self, amount):
        """设置锐化程度
        
        Args:
            amount: 0-1，锐化程度
        """
        self.sharpen_amount = max(0, min(1, amount))
    
    def set_spatial_refine(self, enable):
        """设置是否启用ICM空间平滑"""
        self.enable_spatial_refine = enable
    
    def set_speckle_cleanup(self, enable):
        """设置是否启用噪点清理"""
        self.enable_speckle_cleanup = enable
    
    def _get_color_list(self):
        """获取当前色号列表"""
        if self.color_spec == "221":
            return MARD_221_COLORS
        else:
            return MARD_291_COLORS
    
    def _merge_similar_colors(self, colors, threshold):
        """合并相似颜色"""
        if len(colors) == 0:
            return colors
        
        merged = [colors[0]]
        for color in colors[1:]:
            is_similar = False
            for existing in merged:
                distance = color_distance(color, existing)
                if distance < threshold:
                    is_similar = True
                    break
            if not is_similar:
                merged.append(color)
        
        return merged
    
    def _get_merge_threshold(self):
        """获取合并阈值"""
        # 直接返回用户设置的值（0-100映射到实际阈值）
        return self.merge_level
    
    def _is_dark_pixel(self, rgb):
        """判断是否为深色像素"""
        # 将RGB转换为亮度
        r, g, b = int(rgb[0]), int(rgb[1]), int(rgb[2])
        brightness = (r * 0.299 + g * 0.587 + b * 0.114)
        # 阈值越小，识别为深色的条件越严格
        return brightness < self.dark_threshold * 2.55
    
    def _apply_gaussian_blur(self, image):
        """应用高斯模糊（带深色保护）"""
        if self.gaussian_radius <= 0:
            return image
        
        # 创建深色掩码
        pixels = np.array(image)
        height, width = pixels.shape[:2]
        dark_mask = np.zeros((height, width), dtype=bool)
        
        for y in range(height):
            for x in range(width):
                if self._is_dark_pixel(pixels[y, x]):
                    dark_mask[y, x] = True
        
        # 扩展深色保护区域
        if self.gaussian_dark_protect > 0:
            protect_radius = int(self.gaussian_dark_protect / 20)
            if protect_radius > 0:
                dark_mask = ndimage.binary_dilation(dark_mask, iterations=protect_radius)
        
        # 应用高斯模糊
        blurred = image.filter(ImageFilter.GaussianBlur(radius=self.gaussian_radius))
        blurred_pixels = np.array(blurred)
        
        # 深色区域保留原始像素
        result = pixels.copy()
        result[~dark_mask] = blurred_pixels[~dark_mask]
        
        return Image.fromarray(result)
    
    def _apply_median_filter(self, image):
        """应用中值滤波（带深色保护）"""
        if self.median_radius <= 0:
            return image
        
        # 创建深色掩码
        pixels = np.array(image)
        height, width = pixels.shape[:2]
        dark_mask = np.zeros((height, width), dtype=bool)
        
        for y in range(height):
            for x in range(width):
                if self._is_dark_pixel(pixels[y, x]):
                    dark_mask[y, x] = True
        
        # 扩展深色保护区域
        if self.median_dark_protect > 0:
            protect_radius = int(self.median_dark_protect / 20)
            if protect_radius > 0:
                dark_mask = ndimage.binary_dilation(dark_mask, iterations=protect_radius)
        
        # 应用中值滤波
        size = self.median_radius * 2 + 1
        filtered = image.filter(ImageFilter.MedianFilter(size=size))
        filtered_pixels = np.array(filtered)
        
        # 深色区域保留原始像素
        result = pixels.copy()
        result[~dark_mask] = filtered_pixels[~dark_mask]
        
        return Image.fromarray(result)
    
    def _apply_denoise(self, image):
        """应用降噪处理"""
        if not self.enable_denoise:
            return image
        
        # 先应用高斯模糊
        result = self._apply_gaussian_blur(image)
        
        # 再应用中值滤波
        result = self._apply_median_filter(result)
        
        return result
    
    def _merge_pixel_colors(self, pixels, threshold):
        """合并相似的像素颜色"""
        if threshold == 0:
            return pixels
        
        height, width, _ = pixels.shape
        merged = np.copy(pixels)
        
        # 创建颜色映射表
        color_map = {}
        
        for y in range(height):
            for x in range(width):
                pixel = tuple(pixels[y, x])
                
                if pixel not in color_map:
                    # 查找是否有相似的已处理颜色
                    found_similar = False
                    for existing_color in color_map:
                        if color_distance(pixel, existing_color) < threshold:
                            color_map[pixel] = color_map[existing_color]
                            found_similar = True
                            break
                    
                    if not found_similar:
                        color_map[pixel] = pixel
                
                merged[y, x] = color_map[pixel]
        
        return merged
    
    def _build_color_lookup(self, color_list):
        """构建颜色查找表（预计算所有颜色的RGB值）"""
        colors = []
        codes = []
        for code in color_list:
            rgb = get_color_rgb(code)
            if rgb:
                colors.append(rgb)
                codes.append(code)
        return np.array(colors), codes
    
    def _fast_color_match(self, pixels, color_array, color_codes):
        """使用numpy向量化快速匹配颜色"""
        height, width, _ = pixels.shape
        result_matrix = []
        color_count = {}
        color_sq = color_array.astype(np.int32) ** 2
        for y in range(height):
            row = []
            for x in range(width):
                pixel = pixels[y, x].astype(np.int32)
                diff = color_array - pixel
                dist_sq = 4 * diff[:, 0]**2 + 2 * diff[:, 1]**2 + 3 * diff[:, 2]**2
                min_idx = np.argmin(dist_sq)
                nearest = color_codes[min_idx]
                row.append(nearest)
                color_count[nearest] = color_count.get(nearest, 0) + 1
            result_matrix.append(row)
        return result_matrix, color_count
    
    def convert(self):
        """执行转换（使用查找表加速）"""
        if self.image is None or self.bead_width == 0:
            return None
        
        # 获取可用色号列表
        color_list = self._get_color_list()
        
        # 使用边缘感知缩放
        from image_processor import edge_aware_resize, floyd_steinberg_dither, ordered_dither
        resized = edge_aware_resize(self.image, self.bead_width, self.bead_height)
        
        # 根据抖动模式选择处理方式
        if self.dither_mode == "floyd":
            # Floyd-Steinberg抖动
            def nearest_func(rgb, cl, hex_dict):
                return find_nearest_color(rgb, cl)
            result_matrix = floyd_steinberg_dither(
                resized, color_list, MARD_COLORS_HEX, nearest_func
            )
            # 统计颜色
            color_count = {}
            for row in result_matrix:
                for code in row:
                    color_count[code] = color_count.get(code, 0) + 1
        elif self.dither_mode == "ordered":
            # 有序抖动
            def nearest_func(rgb, cl):
                return find_nearest_color(rgb, cl)
            result_matrix = ordered_dither(
                resized, color_list, MARD_COLORS_HEX, nearest_func
            )
            # 统计颜色
            color_count = {}
            for row in result_matrix:
                for code in row:
                    color_count[code] = color_count.get(code, 0) + 1
        else:
            # 无抖动 - 使用查找表加速
            pixels = np.array(resized)
            result_matrix, color_count = self._lookup_color_match(pixels, color_list)
        
        # 颜色合并后处理
        threshold = self._get_merge_threshold()
        if threshold > 0:
            result_matrix, color_count = self._merge_result_colors(result_matrix, color_count, threshold)
        
        return {
            "matrix": result_matrix,
            "color_count": color_count,
            "width": self.bead_width,
            "height": self.bead_height
        }
    
    def _lookup_color_match(self, pixels, color_list):
        """使用查找表进行颜色匹配"""
        # 获取或构建查找表
        table = get_lookup_table()
        if not table.is_built:
            # 首次使用，构建查找表
            build_lookup_table(color_list, MARD_COLORS_HEX)
        
        # 使用查找表批量匹配
        result_matrix = table.get_color_batch(pixels)
        
        # 统计颜色
        color_count = {}
        for row in result_matrix:
            for code in row:
                color_count[code] = color_count.get(code, 0) + 1
        
        return result_matrix, color_count
    
    def _merge_result_colors(self, matrix, color_count, threshold):
        """对匹配结果进行颜色合并（合并颜色表中相近的色号）"""
        color_set = list(color_count.keys())
        
        # 计算哪些色号对应该合并
        merge_map = {}
        color_rgbs = {}
        for code in color_set:
            rgb = get_color_rgb(code)
            if rgb:
                color_rgbs[code] = rgb
        
        # CIEDE2000阈值映射：滑动条0-100 -> CIEDE2000距离 0-10
        # 滑动条10 ≈ DeltaE 1（仅合并几乎相同的颜色）
        # 滑动条30 ≈ DeltaE 3（合并相似颜色）
        # 滑动条50 ≈ DeltaE 5（合并明显不同的颜色）
        cie_threshold = threshold / 10.0
        
        # 找出相近的色号对
        used = set()
        for i, c1 in enumerate(color_set):
            if c1 in used:
                continue
            if c1 not in color_rgbs:
                continue
            merge_map[c1] = c1
            for j, c2 in enumerate(color_set):
                if j <= i or c2 in used:
                    continue
                if c2 not in color_rgbs:
                    continue
                dist = color_distance(color_rgbs[c1], color_rgbs[c2])
                if dist < cie_threshold:
                    merge_map[c2] = c1
                    used.add(c2)
        
        # 应用合并
        new_matrix = []
        new_count = {}
        for y in range(len(matrix)):
            row = []
            for x in range(len(matrix[0])):
                code = matrix[y][x]
                merged = merge_map.get(code, code)
                row.append(merged)
                new_count[merged] = new_count.get(merged, 0) + 1
            new_matrix.append(row)
        
        return new_matrix, new_count
    
    def generate_preview(self, result, cell_size=10, bead_style="circle"):
        """生成预览图（无色号标注）
        
        Args:
            bead_style: "circle" 为圆形豆子, "square" 为方形豆子
        """
        width = result["width"]
        height = result["height"]
        matrix = result["matrix"]
        
        img_width = width * cell_size
        img_height = height * cell_size
        
        # 创建浅灰色背景（模拟豆板）
        img = Image.new("RGB", (img_width, img_height), (240, 240, 240))
        draw = ImageDraw.Draw(img)
        
        # 绘制豆板网格线
        for x in range(width + 1):
            draw.line([(x * cell_size, 0), (x * cell_size, img_height)], fill=(200, 200, 200), width=1)
        for y in range(height + 1):
            draw.line([(0, y * cell_size), (img_width, y * cell_size)], fill=(200, 200, 200), width=1)
        
        # 绘制豆子
        padding = max(1, cell_size // 10)
        for y in range(height):
            for x in range(width):
                color_code = matrix[y][x]
                hex_color = get_color_rgb(color_code)
                if hex_color:
                    x1 = x * cell_size + padding
                    y1 = y * cell_size + padding
                    x2 = (x + 1) * cell_size - padding
                    y2 = (y + 1) * cell_size - padding
                    
                    if bead_style == "circle":
                        # 绘制圆形豆子（中空效果）
                        # 外圆
                        draw.ellipse([x1, y1, x2, y2], fill=hex_color)
                        # 内圆（中空效果，颜色稍浅）
                        inner_padding = max(2, cell_size // 4)
                        inner_x1 = x1 + inner_padding
                        inner_y1 = y1 + inner_padding
                        inner_x2 = x2 - inner_padding
                        inner_y2 = y2 - inner_padding
                        # 让内圆颜色变浅（模拟中空效果）
                        lighter_color = tuple(min(255, c + 40) for c in hex_color)
                        draw.ellipse([inner_x1, inner_y1, inner_x2, inner_y2], fill=lighter_color)
                    else:
                        # 方形豆子
                        draw.rectangle([x1, y1, x2, y2], fill=hex_color)
        
        # 添加LSB水印
        img = embed_lsb(img, COPYRIGHT_TEXT)
        
        return img
    
    def generate_grid(self, result, cell_size=30):
        """生成网格图纸（带色号标注）- 优化版"""
        width = result["width"]
        height = result["height"]
        matrix = result["matrix"]
        
        img_width = width * cell_size
        img_height = height * cell_size
        
        img = Image.new("RGB", (img_width, img_height), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        # 尝试加载字体
        try:
            font_size = max(10, cell_size // 2)
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()
        
        # 批量绘制
        for y in range(height):
            for x in range(width):
                color_code = matrix[y][x]
                hex_color = get_color_rgb(color_code)
                if hex_color:
                    x1 = x * cell_size
                    y1 = y * cell_size
                    x2 = x1 + cell_size
                    y2 = y1 + cell_size
                    
                    # 绘制背景色和边框
                    draw.rectangle([x1, y1, x2, y2], fill=hex_color, outline=(100, 100, 100))
                    
                    # 绘制色号文字（2次绘制：描边+文字）
                    text_x = x1 + cell_size // 2
                    text_y = y1 + cell_size // 2
                    
                    # 根据背景色选择文字颜色
                    rgb = hex_color
                    brightness = rgb[0] * 0.299 + rgb[1] * 0.587 + rgb[2] * 0.114
                    
                    if brightness < 128:
                        # 暗背景：白色文字+黑色描边
                        draw.text((text_x, text_y), color_code, fill=(0, 0, 0), font=font, anchor="mm")
                        draw.text((text_x, text_y), color_code, fill=(255, 255, 255), font=font, anchor="mm")
                    else:
                        # 亮背景：黑色文字+白色描边
                        draw.text((text_x, text_y), color_code, fill=(255, 255, 255), font=font, anchor="mm")
                        draw.text((text_x, text_y), color_code, fill=(0, 0, 0), font=font, anchor="mm")
        
        # 添加LSB水印
        img = embed_lsb(img, COPYRIGHT_TEXT)
        
        return img
    
    def generate_color_list(self, result):
        """生成颜色清单"""
        color_count = result["color_count"]
        
        # 按色号排序
        sorted_colors = sorted(color_count.items(), key=lambda x: x[0])
        
        lines = ["色号清单："]
        lines.append("=" * 30)
        lines.append(f"{'色号':<10} {'数量':<10} {'颜色':<10}")
        lines.append("-" * 30)
        
        total = 0
        for color_code, count in sorted_colors:
            hex_color = get_color_rgb(color_code)
            hex_str = rgb_to_hex(hex_color) if hex_color else "N/A"
            lines.append(f"{color_code:<10} {count:<10} {hex_str:<10}")
            total += count
        
        lines.append("=" * 30)
        lines.append(f"总计：{total}颗豆子")
        
        return "\n".join(lines)

def main():
    """测试函数"""
    converter = PerlerBeadConverter()
    
    # 测试图片路径
    test_image = "test.png"
    
    if not os.path.exists(test_image):
        print(f"测试图片 {test_image} 不存在")
        return
    
    # 加载图片
    if not converter.load_image(test_image):
        return
    
    # 设置宽度
    converter.set_width(16)
    width, height = converter.get_dimensions()
    print(f"转换尺寸：{width} x {height}")
    
    # 设置色号规格
    converter.set_color_spec("221")
    
    # 执行转换
    result = converter.convert()
    if result:
        print(f"转换完成！共{len(result['color_count'])}种颜色")
        
        # 生成预览图
        preview = converter.generate_preview(result)
        preview.save("preview.png")
        print("预览图已保存：preview.png")
        
        # 生成网格图纸
        grid = converter.generate_grid(result)
        grid.save("grid.png")
        print("网格图纸已保存：grid.png")
        
        # 生成颜色清单
        color_list = converter.generate_color_list(result)
        with open("color_list.txt", "w", encoding="utf-8") as f:
            f.write(color_list)
        print("颜色清单已保存：color_list.txt")

if __name__ == "__main__":
    main()
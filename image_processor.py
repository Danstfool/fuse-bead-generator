"""
图像处理模块 - 实现边缘感知缩放、抖动、空间平滑等
参考pixelbead.art的实现
"""
import numpy as np
from PIL import Image
from color_utils import rgb_to_lab, delta_e_cie76, delta_e_cie2000

# 方差阈值
VAR_LOW = 50
VAR_HIGH = 240

def compute_edge_area_color(pixels, x1, y1, x2, y2):
    """
    边缘感知区域采样 - 计算一个区域的代表颜色
    对于高方差区域（边缘），使用2-means聚类选择主导颜色
    """
    # 提取区域像素
    h, w, _ = pixels.shape
    x1, y1 = max(0, int(x1)), max(0, int(y1))
    x2, y2 = min(w, int(x2)), min(h, int(y2))
    
    if x2 <= x1 or y2 <= y1:
        return None
    
    region = pixels[y1:y2, x1:x2].reshape(-1, 3)
    
    if len(region) == 0:
        return None
    
    # 计算平均颜色和方差
    avg_color = np.mean(region, axis=0)
    
    # 计算线性RGB空间的方差
    region_linear = np.array([[srgb_to_linear(p[0]), srgb_to_linear(p[1]), srgb_to_linear(p[2])] for p in region])
    variance = np.mean(np.var(region_linear, axis=0))
    
    # 低方差区域：直接返回平均颜色
    if variance < 0.008:
        return tuple(int(x) for x in avg_color)
    
    # 高方差区域（边缘）：使用2-means聚类
    # 找到离平均最远的像素作为第一个聚类中心
    avg_lab = rgb_to_lab(tuple(int(x) for x in avg_color))
    max_dist = 0
    center1_idx = 0
    
    for i, pixel in enumerate(region[:min(100, len(region))]):  # 采样前100个
        lab = rgb_to_lab(tuple(int(x) for x in pixel))
        dist = delta_e_cie76(avg_lab, lab)
        if dist > max_dist:
            max_dist = dist
            center1_idx = i
    
    center1 = region[center1_idx].astype(float)
    center2 = avg_color.astype(float)
    
    # 3次迭代的2-means
    for _ in range(3):
        cluster1 = []
        cluster2 = []
        
        for pixel in region:
            d1 = np.sum((pixel - center1) ** 2)
            d2 = np.sum((pixel - center2) ** 2)
            if d1 < d2:
                cluster1.append(pixel)
            else:
                cluster2.append(pixel)
        
        if cluster1:
            center1 = np.mean(cluster1, axis=0)
        if cluster2:
            center2 = np.mean(cluster2, axis=0)
    
    # 选择更大的聚类的中心
    if len(cluster1) >= len(cluster2):
        return tuple(int(x) for x in center1)
    else:
        return tuple(int(x) for x in center2)

def edge_aware_resize(image, target_width, target_height):
    """
    边缘感知缩放 - 保持边缘清晰
    """
    img_array = np.array(image)
    src_h, src_w, _ = img_array.shape
    
    # 计算每个输出像素对应的源区域大小
    cell_w = src_w / target_width
    cell_h = src_h / target_height
    
    # 创建输出数组
    result = np.zeros((target_height, target_width, 3), dtype=np.uint8)
    
    for y in range(target_height):
        for x in range(target_width):
            # 计算源区域
            x1 = int(x * cell_w)
            y1 = int(y * cell_h)
            x2 = int((x + 1) * cell_w)
            y2 = int((y + 1) * cell_h)
            
            # 边界检查
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(src_w, x2), min(src_h, y2)
            
            if x2 <= x1 or y2 <= y1:
                continue
            
            # 提取区域
            region = img_array[y1:y2, x1:x2].reshape(-1, 3)
            
            if len(region) == 0:
                continue
            
            # 计算平均颜色
            avg_color = np.mean(region, axis=0)
            
            # 计算方差
            region_float = region.astype(np.float32) / 255.0
            variance = np.mean(np.var(region_float, axis=0))
            
            # 低方差区域：直接使用平均颜色
            if variance < 0.008:
                result[y, x] = avg_color.astype(np.uint8)
            else:
                # 高方差区域（边缘）：使用2-means聚类
                # 找到离平均最远的像素作为第一个聚类中心
                avg_lab = rgb_to_lab(tuple(int(c) for c in avg_color))
                max_dist = 0
                center1_idx = 0
                
                for i in range(min(50, len(region))):
                    lab = rgb_to_lab(tuple(int(c) for c in region[i]))
                    dist = delta_e_cie76(avg_lab, lab)
                    if dist > max_dist:
                        max_dist = dist
                        center1_idx = i
                
                center1 = region[center1_idx].astype(float)
                center2 = avg_color.astype(float)
                
                # 3次迭代的2-means
                for _ in range(3):
                    cluster1 = []
                    cluster2 = []
                    
                    for pixel in region:
                        d1 = np.sum((pixel - center1) ** 2)
                        d2 = np.sum((pixel - center2) ** 2)
                        if d1 < d2:
                            cluster1.append(pixel)
                        else:
                            cluster2.append(pixel)
                    
                    if cluster1:
                        center1 = np.mean(cluster1, axis=0)
                    if cluster2:
                        center2 = np.mean(cluster2, axis=0)
                
                # 选择更大的聚类的中心
                if len(cluster1) >= len(cluster2):
                    result[y, x] = center1.astype(np.uint8)
                else:
                    result[y, x] = center2.astype(np.uint8)
    
    return Image.fromarray(result)

def srgb_to_linear(c):
    """sRGB到线性RGB"""
    c = c / 255.0
    if c <= 0.04045:
        return c / 12.92
    else:
        return ((c + 0.055) / 1.055) ** 2.4

def apply_unsharp_mask(image, amount=0.3, radius=1):
    """
    反锐化掩膜 - 增强边缘
    """
    img_array = np.array(image, dtype=np.float64)
    
    # 简单的3x3高斯模糊
    kernel = np.array([[1, 2, 1], [2, 4, 2], [1, 2, 1]]) / 16.0
    
    # 对每个通道应用
    blurred = np.zeros_like(img_array)
    for c in range(3):
        # 简单的卷积
        padded = np.pad(img_array[:, :, c], 1, mode='edge')
        for y in range(img_array.shape[0]):
            for x in range(img_array.shape[1]):
                blurred[y, x, c] = np.sum(padded[y:y+3, x:x+3] * kernel)
    
    # 反锐化 = 原图 + amount * (原图 - 模糊图)
    sharpened = img_array + amount * (img_array - blurred)
    sharpened = np.clip(sharpened, 0, 255).astype(np.uint8)
    
    return Image.fromarray(sharpened)

def ordered_dither(image, color_list, mard_colors_hex, find_nearest_func):
    """
    有序抖动（4x4 Bayer矩阵）
    在亮度通道上添加抖动，让渐变更自然
    """
    img_array = np.array(image, dtype=np.float64)
    h, w, _ = img_array.shape
    
    # 4x4 Bayer矩阵
    bayer_matrix = np.array([
        [0, 8, 2, 10],
        [12, 4, 14, 6],
        [3, 11, 1, 9],
        [15, 7, 13, 5]
    ]) / 16.0 - 0.5  # 归一化到 -0.5 到 0.5
    
    result_matrix = []
    
    for y in range(h):
        row = []
        for x in range(w):
            # 获取原始像素
            r, g, b = img_array[y, x]
            
            # 计算亮度
            brightness = r * 0.299 + g * 0.587 + b * 0.114
            
            # 添加Bayer抖动（只影响亮度）
            threshold = bayer_matrix[y % 4][x % 4]
            dither_amount = 12  # 抖动强度
            
            # 调整亮度
            new_brightness = brightness + threshold * dither_amount
            scale = new_brightness / max(brightness, 0.001)
            
            new_r = int(min(255, max(0, r * scale)))
            new_g = int(min(255, max(0, g * scale)))
            new_b = int(min(255, max(0, b * scale)))
            
            # 匹配颜色
            nearest = find_nearest_func((new_r, new_g, new_b), color_list)
            row.append(nearest)
        result_matrix.append(row)
    
    return result_matrix

def floyd_steinberg_dither(image, color_list, mard_colors_hex, find_nearest_func):
    """
    Floyd-Steinberg误差扩散抖动（蛇形扫描）
    在Lab空间进行误差扩散
    """
    img_array = np.array(image, dtype=np.float64)
    h, w, _ = img_array.shape
    
    # 转换为Lab空间
    lab_array = np.zeros((h, w, 3))
    for y in range(h):
        for x in range(w):
            lab_array[y, x] = rgb_to_lab(tuple(int(c) for c in img_array[y, x]))
    
    result = np.zeros((h, w), dtype=object)  # 存储色号
    
    for y in range(h):
        # 蛇形扫描：偶数行左到右，奇数行右到左
        if y % 2 == 0:
            x_range = range(w)
        else:
            x_range = range(w - 1, -1, -1)
        
        for x in x_range:
            # 获取当前像素的Lab值
            L, a, b = lab_array[y, x]
            
            # 找到最接近的颜色
            current_rgb = (int(img_array[y, x, 0]), int(img_array[y, x, 1]), int(img_array[y, x, 2]))
            nearest = find_nearest_func(current_rgb, color_list, mard_colors_hex)
            result[y, x] = nearest
            
            # 获取最近颜色的Lab值
            from mard_colors import hex_to_rgb, MARD_COLORS_HEX
            nearest_rgb = hex_to_rgb(MARD_COLORS_HEX[nearest])
            nearest_lab = rgb_to_lab(nearest_rgb)
            
            # 计算误差
            error_L = L - nearest_lab[0]
            error_a = a - nearest_lab[1]
            error_b = b - nearest_lab[2]
            
            # 扩散误差（7/16, 5/16, 3/16, 1/16）
            if y % 2 == 0:  # 左到右
                if x + 1 < w:
                    lab_array[y, x + 1] += [error_L * 7/16, error_a * 7/16, error_b * 7/16]
                if y + 1 < h:
                    if x - 1 >= 0:
                        lab_array[y + 1, x - 1] += [error_L * 3/16, error_a * 3/16, error_b * 3/16]
                    lab_array[y + 1, x] += [error_L * 5/16, error_a * 5/16, error_b * 5/16]
                    if x + 1 < w:
                        lab_array[y + 1, x + 1] += [error_L * 1/16, error_a * 1/16, error_b * 1/16]
            else:  # 右到左
                if x - 1 >= 0:
                    lab_array[y, x - 1] += [error_L * 7/16, error_a * 7/16, error_b * 7/16]
                if y + 1 < h:
                    if x + 1 < w:
                        lab_array[y + 1, x + 1] += [error_L * 3/16, error_a * 3/16, error_b * 3/16]
                    lab_array[y + 1, x] += [error_L * 5/16, error_a * 5/16, error_b * 5/16]
                    if x - 1 >= 0:
                        lab_array[y + 1, x - 1] += [error_L * 1/16, error_a * 1/16, error_b * 1/16]
    
    return result

def spatial_refinement(result_matrix, color_list, mard_colors_hex, iterations=3):
    """
    ICM空间平滑 - 迭代优化减少杂色
    只处理孤立像素（没有同色邻居的像素）
    """
    h = len(result_matrix)
    w = len(result_matrix[0])
    
    from mard_colors import hex_to_rgb, MARD_COLORS_HEX
    
    # 预计算所有颜色的Lab值
    color_labs = {}
    for code in set(sum(result_matrix, [])):
        if code in MARD_COLORS_HEX:
            rgb = hex_to_rgb(MARD_COLORS_HEX[code])
            color_labs[code] = rgb_to_lab(rgb)
    
    for iteration in range(iterations):
        changed = 0
        
        for y in range(h):
            for x in range(w):
                current = result_matrix[y][x]
                if current not in color_labs:
                    continue
                
                # 统计邻居颜色
                neighbor_counts = {}
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        if dy == 0 and dx == 0:
                            continue
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < h and 0 <= nx < w:
                            neighbor = result_matrix[ny][nx]
                            neighbor_counts[neighbor] = neighbor_counts.get(neighbor, 0) + 1
                
                # 只处理孤立像素（没有同色邻居）
                same_count = neighbor_counts.get(current, 0)
                if same_count > 0:
                    continue  # 有同色邻居，跳过
                
                # 找到最多的邻居颜色
                if not neighbor_counts:
                    continue
                
                dominant = max(neighbor_counts, key=neighbor_counts.get)
                dominant_count = neighbor_counts[dominant]
                
                # 只有当主导颜色>= 4个邻居时才替换（超过一半）
                if dominant_count >= 4:
                    current_lab = color_labs[current]
                    dominant_lab = color_labs.get(dominant)
                    if dominant_lab:
                        cost = delta_e_cie2000(current_lab, dominant_lab)
                        # 只有当颜色差异不太大时才替换
                        if cost <= 10:
                            result_matrix[y][x] = dominant
                            changed += 1
        
        # 如果没有变化，提前退出
        if changed == 0:
            break
    
    return result_matrix

def clean_speckles(result_matrix, color_list, mard_colors_hex, tolerance=5.0):
    """
    噪点清理 - 检测并替换孤立像素
    如果一个像素没有同色邻居，且邻居中有主导颜色>=3个，则替换
    """
    h = len(result_matrix)
    w = len(result_matrix[0])
    
    from mard_colors import hex_to_rgb, MARD_COLORS_HEX
    
    # 预计算颜色Lab值
    color_labs = {}
    for code in set(sum(result_matrix, [])):
        if code in MARD_COLORS_HEX:
            rgb = hex_to_rgb(MARD_COLORS_HEX[code])
            color_labs[code] = rgb_to_lab(rgb)
    
    # 需要两遍处理，避免顺序影响
    changes = []
    
    for y in range(h):
        for x in range(w):
            current = result_matrix[y][x]
            if current not in color_labs:
                continue
            
            # 统计邻居颜色
            neighbor_counts = {}
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    if dy == 0 and dx == 0:
                        continue
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < h and 0 <= nx < w:
                        neighbor = result_matrix[ny][nx]
                        neighbor_counts[neighbor] = neighbor_counts.get(neighbor, 0) + 1
            
            # 如果有同色邻居，跳过
            same_count = neighbor_counts.get(current, 0)
            if same_count > 0:
                continue
            
            # 找到最多的邻居颜色
            if not neighbor_counts:
                continue
            
            dominant = max(neighbor_counts, key=neighbor_counts.get)
            dominant_count = neighbor_counts[dominant]
            
            # 只有当主导颜色>= 3个邻居时才替换
            if dominant_count >= 3:
                current_lab = color_labs[current]
                dominant_lab = color_labs.get(dominant)
                if dominant_lab:
                    cost = delta_e_cie2000(current_lab, dominant_lab)
                    if cost <= tolerance:
                        changes.append((x, y, dominant))
    
    # 应用更改
    for x, y, new_color in changes:
        result_matrix[y][x] = new_color
    
    return result_matrix

def process_image(image, target_width, target_height, color_list, mard_colors_hex, 
                  dither_mode="none", sharpen_amount=0.3, enable_cleanup=True):
    """
    完整的图像处理流程
    """
    from color_utils import precompute_mard_lab, find_nearest_color_cie2000
    
    # 预计算Lab值
    precompute_mard_lab(mard_colors_hex)
    
    # Step 1: 反锐化（如果需要）
    if sharpen_amount > 0:
        # 计算缩放比例
        scale_ratio = max(image.width / target_width, image.height / target_height)
        if scale_ratio > 3:
            # 自适应锐化量
            adaptive_amount = 0.15 + (scale_ratio - 5) * 0.03
            adaptive_amount = max(0.1, min(0.62, adaptive_amount))
            image = apply_unsharp_mask(image, adaptive_amount)
    
    # Step 2: 边缘感知缩放
    resized = edge_aware_resize(image, target_width, target_height)
    
    # Step 3: 颜色匹配（根据抖动模式）
    if dither_mode == "floyd":
        # Floyd-Steinberg抖动
        result_matrix = floyd_steinberg_dither(
            resized, color_list, mard_colors_hex, find_nearest_color_cie2000
        )
    else:
        # 无抖动或有序抖动
        img_array = np.array(resized)
        h, w, _ = img_array.shape
        result_matrix = []
        
        for y in range(h):
            row = []
            for x in range(w):
                pixel = tuple(int(c) for c in img_array[y, x])
                nearest = find_nearest_color_cie2000(pixel, color_list, mard_colors_hex)
                row.append(nearest)
            result_matrix.append(row)
    
    # Step 4: 空间平滑
    result_matrix = spatial_refinement(result_matrix, color_list, mard_colors_hex)
    
    # Step 5: 噪点清理
    if enable_cleanup:
        result_matrix = clean_speckles(result_matrix, color_list, mard_colors_hex)
    
    # 统计颜色数量
    color_count = {}
    for row in result_matrix:
        for code in row:
            color_count[code] = color_count.get(code, 0) + 1
    
    return {
        "matrix": result_matrix,
        "color_count": color_count,
        "width": target_width,
        "height": target_height
    }
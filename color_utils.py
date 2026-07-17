"""
颜色工具模块 - 实现CIEDE2000和Lab色彩空间
参考pixelbead.art的实现
"""
import math
import numpy as np

# sRGB到线性RGB的转换
def srgb_to_linear(c):
    """sRGB到线性RGB（正确的gamma解码）"""
    c = c / 255.0
    if c <= 0.04045:
        return c / 12.92
    else:
        return ((c + 0.055) / 1.055) ** 2.4

def linear_to_srgb(c):
    """线性RGB到sRGB"""
    if c <= 0.0031308:
        return int(round(c * 12.92 * 255))
    else:
        return int(round((1.055 * (c ** (1.0 / 2.4)) - 0.055) * 255))

# 线性RGB到XYZ（D65光源）
RGB_TO_XYZ = np.array([
    [0.4124, 0.3576, 0.1805],
    [0.2126, 0.7152, 0.0722],
    [0.0193, 0.1192, 0.9505]
])

XYZ_TO_RGB = np.linalg.inv(RGB_TO_XYZ)

# D65白点
XN, YN, ZN = 0.95047, 1.00000, 1.08883

# Lab转换阈值
LAB_DELTA = 6.0 / 29.0
LAB_DELTA_SQ = LAB_DELTA ** 2
LAB_DELTA_CU = LAB_DELTA ** 3

def lab_f(t):
    """Lab转换的f函数"""
    if t > LAB_DELTA_CU:
        return t ** (1.0 / 3.0)
    else:
        return t / (3.0 * LAB_DELTA_SQ) + 4.0 / 29.0

def lab_f_inv(t):
    """Lab转换的f逆函数"""
    if t > LAB_DELTA:
        return t ** 3
    else:
        return 3.0 * LAB_DELTA_SQ * (t - 4.0 / 29.0)

# 预计算Lab值的缓存
_lab_cache = {}

def rgb_to_lab(rgb):
    """将RGB转换为Lab色彩空间"""
    rgb_tuple = tuple(int(x) for x in rgb)
    if rgb_tuple not in _lab_cache:
        r, g, b = rgb_tuple
        
        # sRGB到线性RGB
        r_lin = srgb_to_linear(r)
        g_lin = srgb_to_linear(g)
        b_lin = srgb_to_linear(b)
        
        # 线性RGB到XYZ
        x = r_lin * 0.4124 + g_lin * 0.3576 + b_lin * 0.1805
        y = r_lin * 0.2126 + g_lin * 0.7152 + b_lin * 0.0722
        z = r_lin * 0.0193 + g_lin * 0.1192 + b_lin * 0.9505
        
        # XYZ到Lab
        fx = lab_f(x / XN)
        fy = lab_f(y / YN)
        fz = lab_f(z / ZN)
        
        L = 116.0 * fy - 16.0
        a = 500.0 * (fx - fy)
        b_lab = 200.0 * (fy - fz)
        
        _lab_cache[rgb_tuple] = (L, a, b_lab)
    
    return _lab_cache[rgb_tuple]

def lab_to_rgb(L, a, b_lab):
    """将Lab转换为RGB"""
    fy = (L + 16.0) / 116.0
    fx = a / 500.0 + fy
    fz = fy - b_lab / 200.0
    
    x = XN * lab_f_inv(fx)
    y = YN * lab_f_inv(fy)
    z = ZN * lab_f_inv(fz)
    
    # XYZ到线性RGB
    r_lin = x * 3.2406 + y * -1.5372 + z * -0.4986
    g_lin = x * -0.9689 + y * 1.8758 + z * 0.0415
    b_lin = x * 0.0557 + y * -0.2040 + z * 1.0570
    
    # 线性RGB到sRGB
    r = linear_to_srgb(max(0, min(1, r_lin)))
    g = linear_to_srgb(max(0, min(1, g_lin)))
    b = linear_to_srgb(max(0, min(1, b_lin)))
    
    return (r, g, b)

def delta_e_cie76(lab1, lab2):
    """CIEDE76 - 快速欧氏距离（用于内循环）"""
    dL = lab1[0] - lab2[0]
    da = lab1[1] - lab2[1]
    db = lab1[2] - lab2[2]
    return math.sqrt(dL * dL + da * da + db * db)

def delta_e_cie2000(lab1, lab2, kL=1, kC=1, kH=1):
    """CIEDE2000 - 完整实现（用于最终匹配）"""
    L1, a1, b1 = lab1
    L2, a2, b2 = lab2
    
    # Step 1: Calculate C'ab and h'ab
    C1 = math.sqrt(a1 * a1 + b1 * b1)
    C2 = math.sqrt(a2 * a2 + b2 * b2)
    C_avg = (C1 + C2) / 2.0
    C_avg_7 = C_avg ** 7
    G = 0.5 * (1 - math.sqrt(C_avg_7 / (C_avg_7 + 25 ** 7)))
    
    a1p = a1 * (1 + G)
    a2p = a2 * (1 + G)
    
    C1p = math.sqrt(a1p * a1p + b1 * b1)
    C2p = math.sqrt(a2p * a2p + b2 * b2)
    
    h1p = math.atan2(b1, a1p)
    if h1p < 0:
        h1p += 2 * math.pi
    
    h2p = math.atan2(b2, a2p)
    if h2p < 0:
        h2p += 2 * math.pi
    
    # Step 2: Calculate delta L', delta C', delta H'
    dLp = L2 - L1
    dCp = C2p - C1p
    
    if C1p * C2p == 0:
        dhp = 0
    elif abs(h2p - h1p) <= math.pi:
        dhp = h2p - h1p
    elif h2p - h1p > math.pi:
        dhp = h2p - h1p - 2 * math.pi
    else:
        dhp = h2p - h1p + 2 * math.pi
    
    dHp = 2 * math.sqrt(C1p * C2p) * math.sin(dhp / 2)
    
    # Step 3: Calculate CIEDE2000
    Lp_avg = (L1 + L2) / 2
    Cp_avg = (C1p + C2p) / 2
    
    if C1p * C2p == 0:
        hp_avg = h1p + h2p
    elif abs(h1p - h2p) <= math.pi:
        hp_avg = (h1p + h2p) / 2
    elif h1p + h2p < 2 * math.pi:
        hp_avg = (h1p + h2p + 2 * math.pi) / 2
    else:
        hp_avg = (h1p + h2p - 2 * math.pi) / 2
    
    T = (1 
         - 0.17 * math.cos(hp_avg - math.pi / 6)
         + 0.24 * math.cos(2 * hp_avg)
         + 0.32 * math.cos(3 * hp_avg + math.pi / 30)
         - 0.20 * math.cos(4 * hp_avg - 7 * math.pi / 20))
    
    SL = 1 + 0.015 * (Lp_avg - 50) ** 2 / math.sqrt(20 + (Lp_avg - 50) ** 2)
    SC = 1 + 0.045 * Cp_avg
    SH = 1 + 0.015 * Cp_avg * T
    
    Cp_avg_7 = Cp_avg ** 7
    RC = 2 * math.sqrt(Cp_avg_7 / (Cp_avg_7 + 25 ** 7))
    
    dtheta = 30 * math.exp(-((hp_avg * 180 / math.pi - 275) / 25) ** 2)
    
    RT = -math.sin(2 * dtheta * math.pi / 180) * RC
    
    dE = math.sqrt(
        (dLp / (kL * SL)) ** 2
        + (dCp / (kC * SC)) ** 2
        + (dHp / (kH * SH)) ** 2
        + RT * (dCp / (kC * SC)) * (dHp / (kH * SH))
    )
    
    return dE

# 预计算所有MARD颜色的Lab值
_mard_lab_cache = {}

def precompute_mard_lab(mard_colors_hex):
    """预计算所有MARD颜色的Lab值"""
    from mard_colors import hex_to_rgb
    for color_code, hex_color in mard_colors_hex.items():
        rgb = hex_to_rgb(hex_color)
        _mard_lab_cache[color_code] = rgb_to_lab(rgb)

def find_nearest_color_cie2000(rgb, color_list, mard_colors_hex):
    """使用CIEDE2000查找最接近的色号"""
    input_lab = rgb_to_lab(rgb)
    
    min_distance = float('inf')
    nearest_color = None
    
    for color_code in color_list:
        if color_code in _mard_lab_cache:
            color_lab = _mard_lab_cache[color_code]
            delta_e = delta_e_cie2000(input_lab, color_lab)
            if delta_e < min_distance:
                min_distance = delta_e
                nearest_color = color_code
    
    return nearest_color

def find_nearest_color_cie76(rgb, color_list, mard_colors_hex):
    """使用CIEDE76查找最接近的色号（快速版本）"""
    input_lab = rgb_to_lab(rgb)
    
    min_distance = float('inf')
    nearest_color = None
    
    for color_code in color_list:
        if color_code in _mard_lab_cache:
            color_lab = _mard_lab_cache[color_code]
            delta_e = delta_e_cie76(input_lab, color_lab)
            if delta_e < min_distance:
                min_distance = delta_e
                nearest_color = color_code
    
    return nearest_color
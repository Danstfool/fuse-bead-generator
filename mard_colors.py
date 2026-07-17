# MARD拼豆色号表 - 291色完整版
# 格式: {色号: 十六进制颜色码}
# 数据来源：MARD官方色号表

import math

MARD_COLORS_HEX = {
    # A系列
    "A1": "#FAF4C8",
    "A2": "#FFFFD5",
    "A3": "#FEFF8B",
    "A4": "#FBED56",
    "A5": "#F4D738",
    "A6": "#FEAC4C",
    "A7": "#FE8B4C",
    "A8": "#FFDA45",
    "A9": "#FF995B",
    "A10": "#F77C31",
    "A11": "#FFDD99",
    "A12": "#FE9F72",
    "A13": "#FFC365",
    "A14": "#FD543D",
    "A15": "#FFF365",
    "A16": "#FFFF9F",
    "A17": "#FFE36E",
    "A18": "#FEBE7D",
    "A19": "#FD7C72",
    "A20": "#FFD568",
    "A21": "#FFE395",
    "A22": "#F4F57D",
    "A23": "#E6C9B7",
    "A24": "#F7F8A2",
    "A25": "#FFD67D",
    "A26": "#FFC830",
    
    # B系列
    "B1": "#E6EE31",
    "B2": "#63F347",
    "B3": "#9EFF80",
    "B4": "#5DE035",
    "B5": "#35E352",
    "B6": "#65E2A6",
    "B7": "#3DAF80",
    "B8": "#1C9C4F",
    "B9": "#27523A",
    "B10": "#95D3C2",
    "B11": "#5D722A",
    "B12": "#166F41",
    "B13": "#CAEB7B",
    "B14": "#ADE946",
    "B15": "#2E5132",
    "B16": "#C5ED9C",
    "B17": "#9BB13A",
    "B18": "#E6EE49",
    "B19": "#24B88C",
    "B20": "#C2F0CC",
    "B21": "#156A6B",
    "B22": "#0B3C43",
    "B23": "#303A21",
    "B24": "#EEFCA5",
    "B25": "#4E846D",
    "B26": "#8D7A35",
    "B27": "#CCE1AF",
    "B28": "#9EE5B9",
    "B29": "#C5E254",
    "B30": "#E2FCB1",
    "B31": "#B0E792",
    "B32": "#9CAB5A",
    
    # C系列
    "C1": "#E8FFE7",
    "C2": "#A9F9FC",
    "C3": "#A0E2FB",
    "C4": "#41CCFF",
    "C5": "#01ACEB",
    "C6": "#50AAF0",
    "C7": "#3677D2",
    "C8": "#0F54C0",
    "C9": "#324BCA",
    "C10": "#3EBCE2",
    "C11": "#28DDDE",
    "C12": "#1C334D",
    "C13": "#CDE8FF",
    "C14": "#D5FDFF",
    "C15": "#22C4C6",
    "C16": "#1557A8",
    "C17": "#04D1F6",
    "C18": "#1D3344",
    "C19": "#1887A2",
    "C20": "#176DAF",
    "C21": "#BEDDFF",
    "C22": "#67B4BE",
    "C23": "#C8E2FF",
    "C24": "#7CC4FF",
    "C25": "#A9E5E5",
    "C26": "#3CAED8",
    "C27": "#D3DFFA",
    "C28": "#BBCFED",
    "C29": "#34488E",
    
    # D系列
    "D1": "#AEB4F2",
    "D2": "#858EDD",
    "D3": "#2F54AF",
    "D4": "#182A84",
    "D5": "#B843C5",
    "D6": "#AC7BDE",
    "D7": "#8854B3",
    "D8": "#E2D3FF",
    "D9": "#D5B9F8",
    "D10": "#361851",
    "D11": "#B9BAE1",
    "D12": "#DE9AD4",
    "D13": "#B90095",
    "D14": "#8B279B",
    "D15": "#2F1F90",
    "D16": "#E3E1EE",
    "D17": "#C4D4F6",
    "D18": "#A45EC7",
    "D19": "#D8C3D7",
    "D20": "#9C32B2",
    "D21": "#9A009B",
    "D22": "#333A95",
    "D23": "#EBDAFC",
    "D24": "#7786E5",
    "D25": "#494FC7",
    "D26": "#DFC2F8",
    
    # E系列
    "E1": "#FDD3CC",
    "E2": "#FEC0DF",
    "E3": "#FFB7E7",
    "E4": "#E8649E",
    "E5": "#F551A2",
    "E6": "#F13D74",
    "E7": "#C63478",
    "E8": "#FFDBE9",
    "E9": "#E970CC",
    "E10": "#D33793",
    "E11": "#FCDDD2",
    "E12": "#F78FC3",
    "E13": "#B5006D",
    "E14": "#FFD1BA",
    "E15": "#F8C7C9",
    "E16": "#FFF3EB",
    "E17": "#FFE2EA",
    "E18": "#FFC7DB",
    "E19": "#FEBAD5",
    "E20": "#D8C7D1",
    "E21": "#BD9DA1",
    "E22": "#B785A1",
    "E23": "#937A8D",
    "E24": "#E1BCE8",
    
    # F系列
    "F1": "#FD957B",
    "F2": "#FC3D46",
    "F3": "#F74941",
    "F4": "#FC283C",
    "F5": "#E7002F",
    "F6": "#943630",
    "F7": "#971937",
    "F8": "#BC0028",
    "F9": "#E2677A",
    "F10": "#8A4526",
    "F11": "#5A2121",
    "F12": "#FD4E6A",
    "F13": "#F35744",
    "F14": "#FFA9AD",
    "F15": "#D30022",
    "F16": "#FEC2A6",
    "F17": "#E69C79",
    "F18": "#D37C46",
    "F19": "#C1444A",
    "F20": "#CD9391",
    "F21": "#F7B4C6",
    "F22": "#FDC0D0",
    "F23": "#F67E66",
    "F24": "#E698AA",
    "F25": "#E54B4F",
    
    # G系列
    "G1": "#FFE2CE",
    "G2": "#FFC4AA",
    "G3": "#F4C3A5",
    "G4": "#E1B383",
    "G5": "#EDB045",
    "G6": "#E99C17",
    "G7": "#9D5B3E",
    "G8": "#753832",
    "G9": "#E6B483",
    "G10": "#D98C39",
    "G11": "#E0C593",
    "G12": "#FFC890",
    "G13": "#B7714A",
    "G14": "#8D614C",
    "G15": "#FCF9E0",
    "G16": "#F2D9BA",
    "G17": "#78524B",
    "G18": "#FFE4CC",
    "G19": "#E07935",
    "G20": "#A94023",
    "G21": "#B88558",
    
    # H系列
    "H1": "#FDFBFF",
    "H2": "#FEFFFF",
    "H3": "#B6B1BA",
    "H4": "#89858C",
    "H5": "#48464E",
    "H6": "#2F2B2F",
    "H7": "#000000",
    "H8": "#E7D6DB",
    "H9": "#EDEDED",
    "H10": "#EEE9EA",
    "H11": "#CECDD5",
    "H12": "#FFF5ED",
    "H13": "#F5ECD2",
    "H14": "#CFD7D3",
    "H15": "#98A6A8",
    "H16": "#1D1414",
    "H17": "#F1EDED",
    "H18": "#FFFDF0",
    "H19": "#F6EFE2",
    "H20": "#949FA3",
    "H21": "#FFFBE1",
    "H22": "#CACAD4",
    "H23": "#9A9D94",
    
    # M系列
    "M1": "#BCC6B8",
    "M2": "#8AA386",
    "M3": "#697D80",
    "M4": "#E3D2BC",
    "M5": "#D0CCAA",
    "M6": "#B0A782",
    "M7": "#B4A497",
    "M8": "#B38281",
    "M9": "#A58767",
    "M10": "#C5B2BC",
    "M11": "#9F7594",
    "M12": "#644749",
    "M13": "#D19066",
    "M14": "#C77362",
    "M15": "#757D78",
    
    # P系列
    "P1": "#FCF7F8",
    "P2": "#B0A9AC",
    "P3": "#AFDCAB",
    "P4": "#FEA49F",
    "P5": "#EE8C3E",
    "P6": "#5FD0A7",
    "P7": "#EB9270",
    "P8": "#F0D958",
    "P9": "#D9D9D9",
    "P10": "#D9C7EA",
    "P11": "#F3ECC9",
    "P12": "#E6EEF2",
    "P13": "#AACBEF",
    "P14": "#337680",
    "P15": "#668575",
    "P16": "#FEBF45",
    "P17": "#FEA324",
    "P18": "#FEB89F",
    "P19": "#FFFEEC",
    "P20": "#FEBECF",
    "P21": "#ECBEBF",
    "P22": "#E4A89F",
    "P23": "#A56268",
    
    # Q系列
    "Q1": "#F2A5E8",
    "Q2": "#E9EC91",
    "Q3": "#FFFF00",
    "Q4": "#FFEBFA",
    "Q5": "#76CEDE",
    
    # R系列
    "R1": "#D50D21",
    "R2": "#F92F83",
    "R3": "#FD8324",
    "R4": "#F8EC31",
    "R5": "#35C75B",
    "R6": "#238891",
    "R7": "#19779D",
    "R8": "#1A60C3",
    "R9": "#9A56B4",
    "R10": "#FFDB4C",
    "R11": "#FFEBFA",
    "R12": "#D8D5CE",
    "R13": "#55514C",
    "R14": "#9FE4DF",
    "R15": "#77CEE9",
    "R16": "#3ECFCA",
    "R17": "#4A867A",
    "R18": "#7FCD9D",
    "R19": "#CDE55D",
    "R20": "#E8C7B4",
    "R21": "#AD6F3C",
    "R22": "#6C372F",
    "R23": "#FEB872",
    "R24": "#F3C1C0",
    "R25": "#C9675E",
    "R26": "#D293BE",
    "R27": "#EA8CB1",
    "R28": "#9C87D6",
    
    # T系列
    "T1": "#FFFFFF",
    
    # Y系列
    "Y1": "#FD6FB4",
    "Y2": "#FEB481",
    "Y3": "#D7FAA0",
    "Y4": "#8BDBFA",
    "Y5": "#E987EA",
    
    # ZG系列
    "ZG1": "#DAABB3",
    "ZG2": "#D6AA87",
    "ZG3": "#C1BD8D",
    "ZG4": "#96869F",
    "ZG5": "#8490A6",
    "ZG6": "#94BFE2",
    "ZG7": "#E2A9D2",
    "ZG8": "#AB91C0",
}

def hex_to_rgb(hex_color):
    """将十六进制颜色转换为RGB元组"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb):
    """将RGB元组转换为十六进制颜色"""
    return '#{:02x}{:02x}{:02x}'.format(*rgb)

def get_color_rgb(color_code):
    """获取色号对应的RGB值"""
    hex_color = MARD_COLORS_HEX.get(color_code)
    if hex_color:
        return hex_to_rgb(hex_color)
    return None

def get_color_hex(color_code):
    """获取色号对应的十六进制值"""
    return MARD_COLORS_HEX.get(color_code)

def get_all_colors():
    """获取所有色号"""
    return list(MARD_COLORS_HEX.keys())

# 预计算所有颜色的Lab值（缓存）
_lab_cache = {}

def _srgb_to_linear(c):
    """sRGB到线性RGB"""
    c = c / 255.0
    if c <= 0.04045:
        return c / 12.92
    else:
        return ((c + 0.055) / 1.055) ** 2.4

def _linear_to_xyz(r, g, b):
    """线性RGB到XYZ"""
    x = r * 0.4124564 + g * 0.3575761 + b * 0.1804375
    y = r * 0.2126729 + g * 0.7151522 + b * 0.0721750
    z = r * 0.0193339 + g * 0.1191920 + b * 0.9503041
    return x, y, z

def _xyz_to_lab(x, y, z):
    """XYZ到Lab"""
    xn, yn, zn = 0.95047, 1.00000, 1.08883
    x = x / xn
    y = y / yn
    z = z / zn
    delta = 6/29
    def f(t):
        if t > delta ** 3:
            return t ** (1/3)
        else:
            return t / (3 * delta ** 2) + 4/29
    fx = f(x)
    fy = f(y)
    fz = f(z)
    L = 116 * fy - 16
    a = 500 * (fx - fy)
    b = 200 * (fy - fz)
    return L, a, b

def rgb_to_lab(rgb):
    """将RGB转换为Lab色彩空间"""
    rgb_tuple = tuple(int(x) for x in rgb)
    if rgb_tuple not in _lab_cache:
        r, g, b = rgb_tuple
        r_lin = _srgb_to_linear(r)
        g_lin = _srgb_to_linear(g)
        b_lin = _srgb_to_linear(b)
        x, y, z = _linear_to_xyz(r_lin, g_lin, b_lin)
        L, a, b_lab = _xyz_to_lab(x, y, z)
        _lab_cache[rgb_tuple] = (L, a, b_lab)
    return _lab_cache[rgb_tuple]

def _delta_e_cie2000(lab1, lab2):
    """计算CIEDE2000色差"""
    import math
    L1, a1, b1 = lab1
    L2, a2, b2 = lab2
    kL = 1
    kC = 1
    kH = 1
    C1 = math.sqrt(a1**2 + b1**2)
    C2 = math.sqrt(a2**2 + b2**2)
    C_avg = (C1 + C2) / 2
    G = 0.5 * (1 - math.sqrt(C_avg**7 / (C_avg**7 + 25**7)))
    a1p = a1 * (1 + G)
    a2p = a2 * (1 + G)
    C1p = math.sqrt(a1p**2 + b1**2)
    C2p = math.sqrt(a2p**2 + b2**2)
    h1p = math.atan2(b1, a1p)
    if h1p < 0:
        h1p += 2 * math.pi
    h2p = math.atan2(b2, a2p)
    if h2p < 0:
        h2p += 2 * math.pi
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
    T = (1 - 0.17 * math.cos(hp_avg - math.pi/6) + 0.24 * math.cos(2 * hp_avg) + 0.32 * math.cos(3 * hp_avg + math.pi/30) - 0.20 * math.cos(4 * hp_avg - 7*math.pi/20))
    SL = 1 + 0.015 * (Lp_avg - 50)**2 / math.sqrt(20 + (Lp_avg - 50)**2)
    SC = 1 + 0.045 * Cp_avg
    SH = 1 + 0.015 * Cp_avg * T
    Cp_avg_7 = Cp_avg**7
    RC = 2 * math.sqrt(Cp_avg_7 / (Cp_avg_7 + 25**7))
    dtheta = 30 * math.exp(-((hp_avg * 180/math.pi - 275) / 25)**2)
    RT = -math.sin(2 * dtheta * math.pi/180) * RC
    dE = math.sqrt((dLp / (kL * SL))**2 + (dCp / (kC * SC))**2 + (dHp / (kH * SH))**2 + RT * (dCp / (kC * SC)) * (dHp / (kH * SH)))
    return dE

def color_distance(rgb1, rgb2):
    """计算两个颜色之间的距离（使用CIEDE2000算法）"""
    lab1 = rgb_to_lab(rgb1)
    lab2 = rgb_to_lab(rgb2)
    return _delta_e_cie2000(lab1, lab2)

# 预计算所有MARD颜色的Lab值
_mard_lab_cache = {}

def _precompute_mard_lab():
    """预计算所有MARD颜色的Lab值"""
    for color_code, hex_color in MARD_COLORS_HEX.items():
        rgb = hex_to_rgb(hex_color)
        _mard_lab_cache[color_code] = rgb_to_lab(rgb)

# 初始化时预计算
_precompute_mard_lab()

def find_nearest_color(rgb, color_list=None):
    """查找最接近的色号（使用CIEDE2000算法）"""
    if color_list is None:
        color_list = list(MARD_COLORS_HEX.keys())
    input_lab = rgb_to_lab(rgb)
    min_distance = float('inf')
    nearest_color = None
    for color_code in color_list:
        if color_code in _mard_lab_cache:
            color_lab = _mard_lab_cache[color_code]
            delta_e = _delta_e_cie2000(input_lab, color_lab)
            if delta_e < min_distance:
                min_distance = delta_e
                nearest_color = color_code
    return nearest_color

# 221色标准色号（A-H + M系列）
MARD_221_COLORS = []
for prefix, count in [("A", 26), ("B", 32), ("C", 29), ("D", 26), ("E", 24), ("F", 25), ("G", 21), ("H", 23), ("M", 15)]:
    for i in range(1, count + 1):
        MARD_221_COLORS.append(f"{prefix}{i}")

# 291色完整色号（所有色号）
MARD_291_COLORS = list(MARD_COLORS_HEX.keys())

if __name__ == "__main__":
    print(f"MARD色号表 - 共{len(MARD_COLORS_HEX)}个色号")
    print(f"\n221色规格包含{len(MARD_221_COLORS)}个色号")
    print(f"291色规格包含{len(MARD_291_COLORS)}个色号")
    
    print("\n221色色号列表：")
    print(", ".join(MARD_221_COLORS))
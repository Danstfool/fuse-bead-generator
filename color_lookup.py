"""
颜色查找表 - 预计算RGB到色号的映射
全精度：256^3 = 16,777,216个条目
"""
import os
import sys
import numpy as np
from color_utils import rgb_to_lab, delta_e_cie76

def get_resource_path(relative_path):
    """获取资源文件路径（支持打包后的exe）"""
    if getattr(sys, 'frozen', False):
        # 打包后的路径
        base_path = sys._MEIPASS
    else:
        # 开发环境路径
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

class ColorLookupTable:
    def __init__(self):
        # 256^3的查找表，每个条目存储色号索引
        self.table = None
        self.color_codes = None
        self.color_labs = None
        self.is_built = False
        self.cache_file = "color_lookup_cache.npz"
    
    def build(self, color_list, mard_colors_hex):
        """构建查找表（一次性计算）"""
        print("正在构建颜色查找表...")
        
        # 存储色号列表
        self.color_codes = color_list
        
        # 预计算所有颜色的Lab值
        from mard_colors import hex_to_rgb
        self.color_labs = []
        for code in color_list:
            rgb = hex_to_rgb(mard_colors_hex[code])
            self.color_labs.append(rgb_to_lab(rgb))
        self.color_labs = np.array(self.color_labs)
        
        # 创建查找表（256^3 = 16.7M条目）
        self.table = np.zeros(256**3, dtype=np.uint16)
        
        # 计算每个RGB值对应的最近颜色
        total = 256**3
        for i in range(total):
            if i % 1000000 == 0:
                print(f"进度：{i/total*100:.1f}%")
            
            # 将索引转换为RGB
            r = i >> 16
            g = (i >> 8) & 0xFF
            b = i & 0xFF
            
            # 计算Lab值
            lab = rgb_to_lab((r, g, b))
            
            # 找到最近的颜色（使用CIEDE76，快速）
            min_dist = float('inf')
            min_idx = 0
            for j, color_lab in enumerate(self.color_labs):
                dist = delta_e_cie76(lab, color_lab)
                if dist < min_dist:
                    min_dist = dist
                    min_idx = j
            
            self.table[i] = min_idx
        
        self.is_built = True
        
        # 保存到文件
        self.save_to_file()
        print("查找表构建完成并已保存！")
    
    def save_to_file(self):
        """保存查找表到文件"""
        # 保存到用户目录（可写）
        user_dir = os.path.expanduser("~")
        save_path = os.path.join(user_dir, ".perler_bead_converter")
        os.makedirs(save_path, exist_ok=True)
        
        cache_path = os.path.join(save_path, self.cache_file)
        np.savez_compressed(
            cache_path,
            table=self.table,
            color_codes=np.array(self.color_codes),
            color_labs=self.color_labs
        )
        print(f"查找表已保存到 {cache_path}")
    
    def load_from_file(self):
        """从文件加载查找表"""
        # 先尝试从打包资源中加载
        resource_path = get_resource_path(self.cache_file)
        if os.path.exists(resource_path):
            try:
                data = np.load(resource_path, allow_pickle=True)
                self.table = data['table']
                self.color_codes = data['color_codes'].tolist()
                self.color_labs = data['color_labs']
                self.is_built = True
                print(f"查找表已从打包资源加载")
                return True
            except Exception as e:
                print(f"从打包资源加载失败：{e}")
        
        # 再尝试从用户目录加载
        user_dir = os.path.expanduser("~")
        cache_path = os.path.join(user_dir, ".perler_bead_converter", self.cache_file)
        if os.path.exists(cache_path):
            try:
                data = np.load(cache_path, allow_pickle=True)
                self.table = data['table']
                self.color_codes = data['color_codes'].tolist()
                self.color_labs = data['color_labs']
                self.is_built = True
                print(f"查找表已从用户目录加载")
                return True
            except Exception as e:
                print(f"加载查找表失败：{e}")
        
        return False
    
    def get_color(self, r, g, b):
        """查找RGB对应的色号"""
        if not self.is_built:
            return None
        
        # 将RGB转换为索引
        idx = (r << 16) | (g << 8) | b
        
        # 查找色号
        color_idx = self.table[idx]
        return self.color_codes[color_idx]
    
    def get_color_batch(self, pixels):
        """批量查找RGB对应的色号"""
        if not self.is_built:
            return None
        
        h, w, _ = pixels.shape
        result = []
        
        for y in range(h):
            row = []
            for x in range(w):
                r, g, b = pixels[y, x]
                idx = (int(r) << 16) | (int(g) << 8) | int(b)
                color_idx = self.table[idx]
                row.append(self.color_codes[color_idx])
            result.append(row)
        
        return result

# 全局查找表实例
_lookup_table = None

def get_lookup_table():
    """获取全局查找表"""
    global _lookup_table
    if _lookup_table is None:
        _lookup_table = ColorLookupTable()
    return _lookup_table

def build_lookup_table(color_list, mard_colors_hex):
    """构建全局查找表（优先从文件加载）"""
    table = get_lookup_table()
    
    # 先尝试从文件加载
    if table.load_from_file():
        return table
    
    # 文件不存在，构建新表
    table.build(color_list, mard_colors_hex)
    return table
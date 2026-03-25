"""
cat_function.py - Stellarium .cat 星表文件解析模块

该模块提供解析 Stellarium .cat 格式星表文件的功能，
提取天体物理数据（坐标、星等、光谱类型等），并提供
批量文件处理和数据验证接口。
"""

import struct
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple


class CatParseError(Exception):
    """星表解析错误异常类"""
    pass


class StellariumCatParser:
    """Stellarium .cat 格式星表解析器"""
    
    def __init__(self, cat_file_path: str):
        """
        初始化星表解析器
        
        Args:
            cat_file_path: .cat 文件路径
            
        Raises:
            FileNotFoundError: 如果文件不存在
        """
        self.cat_path = Path(cat_file_path)
        if not self.cat_path.exists():
            raise FileNotFoundError(f"星表文件不存在: {self.cat_path}")
        
        self.stars: List[Dict[str, Any]] = []
        self.header: Dict[str, Any] = {}
        self.zone_counts: List[int] = []
    
    def parse(self, verbose: bool = True) -> List[Dict[str, Any]]:
        """
        解析 .cat 二进制文件
        
        Args:
            verbose: 是否输出详细信息
            
        Returns:
            解析后的恒星数据列表
            
        Raises:
            CatParseError: 如果文件格式无效
        """
        try:
            with open(self.cat_path, "rb") as f:
                self._parse_header(f)
                if verbose:
                    self._print_header_info()
                
                self._parse_star_data(f)
                
                if verbose:
                    print(f"\n解析完成，共读取 {len(self.stars)} 颗恒星")
                
                return self.stars
        except (struct.error, EOFError) as e:
            raise CatParseError(f"文件格式解析错误: {e}")
    
    def _parse_header(self, f):
        """解析文件头"""
        magic = f.read(4)
        self.header["magic"] = magic
        
        self.header["datatype"] = struct.unpack("<I", f.read(4))[0]
        self.header["majver"] = struct.unpack("<I", f.read(4))[0]
        self.header["minver"] = struct.unpack("<I", f.read(4))[0]
        self.header["level"] = struct.unpack("<I", f.read(4))[0]
        self.header["min_mag"] = struct.unpack("<i", f.read(4))[0] / 1000.0
        self.header["epoch_jd"] = struct.unpack("<f", f.read(4))[0]
        
        n_zones = 20 * (4 ** self.header["level"]) + 1
        self.zone_counts = []
        for _ in range(n_zones):
            self.zone_counts.append(struct.unpack("<I", f.read(4))[0])
    
    def _print_header_info(self):
        """打印文件头信息"""
        print("=== 文件头信息 ===")
        print(f"Magic: 0x{self.header['magic'].hex()}")
        print(f"数据类型: {self.header['datatype']}")
        print(f"版本: {self.header['majver']}.{self.header['minver']}")
        print(f"级别: {self.header['level']}")
        print(f"星等范围: {self.header['min_mag']} ~ ...")
        print(f"历元JD: {self.header['epoch_jd']}")
        print(f"区域数: {len(self.zone_counts)}")
        print(f"总星数: {sum(self.zone_counts)}")
    
    def _parse_star_data(self, f):
        """解析恒星数据"""
        total_stars = sum(self.zone_counts)
        
        if self.header["datatype"] == 0:
            self._parse_datatype_0(f, total_stars)
        elif self.header["datatype"] == 1:
            self._parse_datatype_1(f, total_stars)
        else:
            raise CatParseError(f"未知数据类型: {self.header['datatype']}")
    
    def _parse_datatype_0(self, f, total_stars: int):
        """解析数据类型 0 (48字节/记录)"""
        STAR_FORMAT = "<qiiiiiihhHHhHB3s"
        STAR_SIZE = struct.calcsize(STAR_FORMAT)
        
        for i in range(total_stars):
            star_data = f.read(STAR_SIZE)
            if len(star_data) < STAR_SIZE:
                break
            
            unpacked = struct.unpack(STAR_FORMAT, star_data)
            
            x0, x1, x2 = unpacked[1], unpacked[2], unpacked[3]
            r = np.sqrt(x0**2 + x1**2 + x2**2)
            dec = np.degrees(np.arcsin(x2 / r))
            ra = np.degrees(np.arctan2(x1, x0))
            if ra < 0:
                ra += 360
            
            star = {
                "source_id": unpacked[0],
                "x0": x0,
                "x1": x1,
                "x2": x2,
                "ra_deg": ra,
                "dec_deg": dec,
                "dx0": unpacked[4],
                "dx1": unpacked[5],
                "dx2": unpacked[6],
                "b_v": unpacked[7] / 1000.0,
                "vmag": unpacked[8] / 1000.0,
                "parallax": unpacked[9] / 50.0,
                "parallax_err": unpacked[10] / 100.0,
                "radial_velocity": unpacked[11] / 10.0,
                "sp_type_idx": unpacked[12],
                "otype_idx": unpacked[13],
                "hip_component": unpacked[14]
            }
            self.stars.append(star)
    
    def _parse_datatype_1(self, f, total_stars: int):
        """解析数据类型 1 (32字节/记录)"""
        STAR_FORMAT = "<qiiiihhHH"
        STAR_SIZE = struct.calcsize(STAR_FORMAT)
        
        for i in range(total_stars):
            star_data = f.read(STAR_SIZE)
            if len(star_data) < STAR_SIZE:
                break
            
            unpacked = struct.unpack(STAR_FORMAT, star_data)
            
            star = {
                "source_id": unpacked[0],
                "ra_deg": unpacked[1] / 3600000.0,
                "dec_deg": unpacked[2] / 3600000.0,
                "pmra": unpacked[3] / 1000.0,
                "pmdec": unpacked[4] / 1000.0,
                "b_v": unpacked[5] / 1000.0,
                "vmag": unpacked[6] / 1000.0,
                "parallax": unpacked[7] / 100.0,
                "parallax_err": unpacked[8] / 100.0
            }
            self.stars.append(star)
    
    def get_basic_stats(self) -> Dict[str, Any]:
        """
        获取基础统计信息
        
        Returns:
            统计信息字典
        """
        if not self.stars:
            return {}
        
        mags = [s["vmag"] for s in self.stars]
        bv_colors = [s["b_v"] for s in self.stars]
        ra_degs = [s["ra_deg"] for s in self.stars]
        dec_degs = [s["dec_deg"] for s in self.stars]
        
        return {
            "star_count": len(self.stars),
            "ra_range": (np.min(ra_degs), np.max(ra_degs)),
            "dec_range": (np.min(dec_degs), np.max(dec_degs)),
            "vmag_range": (np.min(mags), np.max(mags)),
            "vmag_mean": np.mean(mags),
            "bv_range": (np.min(bv_colors), np.max(bv_colors)),
            "bv_mean": np.mean(bv_colors)
        }
    
    def validate_data(self) -> Tuple[bool, List[str]]:
        """
        验证解析数据的有效性
        
        Returns:
            (是否有效, 错误列表)
        """
        errors = []
        
        if not self.stars:
            errors.append("没有解析到任何恒星数据")
            return False, errors
        
        for i, star in enumerate(self.stars[:100]):  # 仅验证前100颗星
            if not (0 <= star["ra_deg"] <= 360):
                errors.append(f"星{i}: RA超出范围 {star['ra_deg']}")
            if not (-90 <= star["dec_deg"] <= 90):
                errors.append(f"星{i}: Dec超出范围 {star['dec_deg']}")
        
        return len(errors) == 0, errors


def batch_parse_cat_files(directory: str, pattern: str = "*.cat") -> Dict[str, List[Dict[str, Any]]]:
    """
    批量解析目录下的所有 .cat 文件
    
    Args:
        directory: 目录路径
        pattern: 文件匹配模式
        
    Returns:
        文件名 -> 恒星数据列表 的字典
    """
    results = {}
    dir_path = Path(directory)
    
    for cat_file in dir_path.glob(pattern):
        try:
            print(f"正在解析: {cat_file.name}")
            parser = StellariumCatParser(str(cat_file))
            stars = parser.parse(verbose=False)
            results[cat_file.name] = stars
            print(f"  解析完成: {len(stars)} 颗星")
        except Exception as e:
            print(f"  解析失败: {e}")
    
    return results


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        cat_file = sys.argv[1]
    else:
        cat_file = "./stars_0_0v0_20.cat"
    
    try:
        parser = StellariumCatParser(cat_file)
        stars = parser.parse()
        
        stats = parser.get_basic_stats()
        print("\n=== 基础统计 ===")
        for key, value in stats.items():
            print(f"{key}: {value}")
        
        is_valid, errors = parser.validate_data()
        if not is_valid:
            print("\n=== 数据验证警告 ===")
            for error in errors:
                print(f"  {error}")
        else:
            print("\n数据验证通过")
        
        print("\n=== 前5颗星详情 ===")
        for i, star in enumerate(stars[:5]):
            print(f"星{i+1} - RA:{star['ra_deg']:.4f}°, Dec:{star['dec_deg']:.4f}°, Vmag:{star['vmag']:.2f}")
    
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

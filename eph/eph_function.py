"""
eph_function.py - Stellarium Web Engine .eph 文件写入模块

该模块提供符合 Stellarium-Web-Engine 规范的 .eph 文件写入功能，
支持 HEALPix 分区架构的文件组织逻辑 (Norder{a}/Dir{b}/Npix{c}.eph)，
并实现数据写入效率优化和文件完整性校验。
"""

import struct
import zlib
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple


class EPHWriteError(Exception):
    """EPH 文件写入错误异常类"""
    pass


FILE_VERSION = 2


def shuffle_bytes(data: bytes, n_row: int, row_size: int) -> bytes:
    """
    字节重排函数 - 按列重排以提高压缩率
    
    Args:
        data: 原始按行排列的数据
        n_row: 行数
        row_size: 每行字节数
        
    Returns:
        按列重排后的数据
    """
    buf = bytearray(data)
    result = bytearray(len(data))
    for j in range(row_size):
        for i in range(n_row):
            result[j * n_row + i] = buf[i * row_size + j]
    return bytes(result)


class EPHFileWriter:
    """EPH 文件写入器"""
    
    def __init__(self, file_path: str):
        """
        初始化 EPH 文件写入器
        
        Args:
            file_path: 输出文件路径
        """
        self.file_path = Path(file_path)
        self.fp: Optional[Any] = None
        self.star_count = 0
    
    def open_file(self, overwrite: bool = True) -> None:
        """
        打开文件并写入文件头
        
        Args:
            overwrite: 是否覆盖已存在的文件
            
        Raises:
            EPHWriteError: 如果无法删除现有文件
        """
        if self.file_path.exists():
            if not overwrite:
                raise EPHWriteError(f"文件已存在且不允许覆盖: {self.file_path}")
            try:
                os.remove(self.file_path)
            except OSError as e:
                raise EPHWriteError(f"无法删除现有文件: {e}")
        
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.fp = open(self.file_path, "wb")
        self.fp.write(b"EPHE")
        self.fp.write(struct.pack("<I", FILE_VERSION))
        self.star_count = 0
    
    def write_chunk(self, chunk_type: str, data: bytes) -> None:
        """
        写入一个 Chunk
        
        Args:
            chunk_type: Chunk 类型（最大4字符）
            data: Chunk 数据
            
        Raises:
            EPHWriteError: 如果 Chunk 类型过长
        """
        if len(chunk_type) > 4:
            raise EPHWriteError("Chunk type too long (max 4 chars)")
        
        chunk_type_bytes = chunk_type.ljust(4).encode("ascii")
        chunk_len = len(data)
        
        self.fp.write(chunk_type_bytes)
        self.fp.write(struct.pack("<I", chunk_len))
        self.fp.write(data)
        self.fp.write(struct.pack("<I", 0))
    
    def write_json_chunk(self, json_str: str) -> None:
        """
        写入 JSON 元数据 Chunk
        
        Args:
            json_str: JSON 字符串
        """
        self.write_chunk("JSON", json_str.encode("utf-8"))
    
    def write_star_chunk(self, stars: List[Dict[str, Any]], order: int = 0, pix: int = 0) -> None:
        """
        写入恒星数据 Chunk
        
        Args:
            stars: 恒星数据列表
            order: HEALPix 层级
            pix: HEALPix 像素编号
        """
        nuniq = 4 * (1 << (2 * order)) + pix
        tile_data = struct.pack("<IQ", 3, nuniq)
        
        # 单位常量（与参考文件一致）
        EPH_RAD          = 1 << 16
        EPH_VMAG         = 3 << 16
        EPH_ARCSEC       = (1 << 16) | 1 | 2 | 4   # 0x10007
        EPH_RAD_PER_YEAR = 6 << 16
        
        columns = [
            {"name": "hip", "type": "i", "unit": 0, "start": 0, "size": 4},
            {"name": "hd", "type": "i", "unit": 0, "start": 4, "size": 4},
            {"name": "vmag", "type": "f", "unit": EPH_VMAG, "start": 8, "size": 4},
            {"name": "ra", "type": "f", "unit": EPH_RAD, "start": 12, "size": 4},
            {"name": "de", "type": "f", "unit": EPH_RAD, "start": 16, "size": 4},
            {"name": "plx", "type": "f", "unit": EPH_ARCSEC, "start": 20, "size": 4},
            {"name": "pra", "type": "f", "unit": EPH_RAD_PER_YEAR, "start": 24, "size": 4},
            {"name": "pde", "type": "f", "unit": EPH_RAD_PER_YEAR, "start": 28, "size": 4},
            {"name": "bv", "type": "f", "unit": 0, "start": 32, "size": 4},
            {"name": "ids", "type": "s", "unit": 0, "start": 36, "size": 256},
        ]
        
        row_size = 292
        n_col = 10
        n_row = len(stars)
        flags = 1
        
        table_header = struct.pack("<IIII", flags, row_size, n_col, n_row)
        table_data = table_header
        
        for col in columns:
            name_bytes = col["name"].ljust(4).encode("ascii")
            typ_byte = col["type"].encode("ascii") + b"\x00\x00\x00"
            col_data = name_bytes + typ_byte + struct.pack("<III", col["unit"], col["start"], col["size"])
            table_data += col_data
        
        row_data = b""
        for star in stars:
            row = bytearray(row_size)
            
            struct.pack_into("<I", row, 0, star.get("hip", 0))
            struct.pack_into("<I", row, 4, star.get("hd", 0))
            struct.pack_into("<f", row, 8, star.get("vmag", 0.0))
            struct.pack_into("<f", row, 12, star.get("ra", 0.0))
            struct.pack_into("<f", row, 16, star.get("de", 0.0))
            struct.pack_into("<f", row, 20, star.get("plx", 0.0))
            struct.pack_into("<f", row, 24, star.get("pra", 0.0))
            struct.pack_into("<f", row, 28, star.get("pde", 0.0))
            struct.pack_into("<f", row, 32, star.get("bv", 0.0))
            
            ids_bytes = star.get("ids", "").encode("ascii", errors="replace")[:255]
            ids_bytes = ids_bytes.ljust(256, b"\x00")
            row[36:36+256] = ids_bytes
            
            row_data += bytes(row)
        
        shuffled_data = shuffle_bytes(row_data, n_row, row_size)
        compressed_data = zlib.compress(shuffled_data, level=9)
        
        comp_header = struct.pack("<II", len(row_data), len(compressed_data))
        table_data += comp_header + compressed_data
        
        self.write_chunk("STAR", tile_data + table_data)
        self.star_count += len(stars)
    
    def close(self) -> None:
        """关闭文件"""
        if self.fp:
            self.fp.flush()
            self.fp.close()
            self.fp = None
    
    def verify_file(self) -> Tuple[bool, str]:
        """
        验证文件完整性
        
        Returns:
            (是否有效, 错误信息)
        """
        if not self.file_path.exists():
            return False, "文件不存在"
        
        try:
            with open(self.file_path, "rb") as f:
                magic = f.read(4)
                if magic != b"EPHE":
                    return False, f"无效的文件标识: {magic}"
                
                version = struct.unpack("<I", f.read(4))[0]
                if version != FILE_VERSION:
                    return False, f"版本不匹配: 期望 {FILE_VERSION}, 实际 {version}"
            
            return True, "文件验证通过"
        except Exception as e:
            return False, f"验证失败: {e}"
    
    def __enter__(self):
        self.open_file()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def cat_star_to_eph_star(cat_star: Dict[str, Any]) -> Dict[str, Any]:
    """
    将 .cat 格式的恒星数据转换为 .eph 格式
    
    Args:
        cat_star: .cat 格式的恒星数据
        
    Returns:
        .eph 格式的恒星数据
    """
    ra_rad = cat_star["ra_deg"] * (3.141592653589793 / 180.0)
    dec_rad = cat_star["dec_deg"] * (3.141592653589793 / 180.0)
    
    pmra = cat_star.get("pmra", 0.0) or cat_star.get("dx0", 0.0) * 1e-3
    pmdec = cat_star.get("pmdec", 0.0) or cat_star.get("dx1", 0.0) * 1e-3
    
    source_id_str = str(cat_star.get("source_id", ""))
    
    return {
        "hip": int(cat_star.get("source_id", 0) % 4294967295),
        "hd": 0,
        "vmag": cat_star.get("vmag", 0.0),
        "ra": ra_rad,
        "de": dec_rad,
        "plx": cat_star.get("parallax", 0.0) / 1000.0,  # 转换为arcsec单位
        "pra": pmra,
        "pde": pmdec,
        "bv": cat_star.get("b_v", 0.0),
        "ids": source_id_str
    }


def write_eph_for_healpix(output_dir: str, order: int, pix: int, stars: List[Dict[str, Any]]) -> Tuple[bool, str]:
    """
    为指定的 HEALPix 分区写入 .eph 文件
    
    Args:
        output_dir: 输出根目录
        order: HEALPix 层级 (Norder)
        pix: HEALPix 像素编号 (Npix)
        stars: 该分区内的恒星数据列表
        
    Returns:
        (是否成功, 消息)
    """
    if not stars:
        return True, "无数据，跳过写入"
    
    norder_dir = f"Norder{order}"
    dir_name = "Dir0"
    npix_file = f"Npix{pix}.eph"
    
    output_path = Path(output_dir) / norder_dir / dir_name / npix_file
    
    try:
        eph_stars = [cat_star_to_eph_star(s) for s in stars]
        
        # 按 vmag 排序（亮星在前，与参考文件一致）
        eph_stars.sort(key=lambda s: s["vmag"])
        
        with EPHFileWriter(str(output_path)) as writer:
            writer.write_json_chunk('{"children_mask": 15}')
            writer.write_star_chunk(eph_stars, order=order, pix=pix)
        
        is_valid, msg = writer.verify_file()
        if is_valid:
            return True, f"成功写入 {len(stars)} 颗恒星到 {output_path}"
        else:
            return False, f"文件验证失败: {msg}"
    
    except Exception as e:
        return False, f"写入失败: {str(e)}"


if __name__ == "__main__":
    import sys
    
    print("eph_function.py - EPH 文件写入模块")
    print("\n该模块提供以下功能:")
    print("- EPHFileWriter: .eph 文件写入器")
    print("- cat_star_to_eph_star: .cat 到 .eph 数据格式转换")
    print("- write_eph_for_healpix: HEALPix 分区写入")

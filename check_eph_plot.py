"""
check_eph_plot.py - 检查并绘制 .eph 文件中的天体信息

该脚本读取 Norder0 路径下的所有 .eph 文件，
提取天体坐标并绘制在天球坐标图上。

基于 eph/read_eph.py 的正确实现进行文件解析。
"""

import struct
import zlib
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams
from typing import List, Dict, Any

rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
rcParams['axes.unicode_minus'] = False

FILE_VERSION = 2


class EPHFileReader:
    """.eph 文件读取器，用于提取恒星数据
    
    基于 eph/read_eph.py 的正确实现。
    """
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.stars: List[Dict[str, Any]] = []
    
    def _unshuffle_bytes(self, data: bytes, n_row: int, row_size: int) -> bytes:
        """反转字节重排"""
        buf = bytearray(data)
        result = bytearray(len(data))
        for j in range(row_size):
            for i in range(n_row):
                result[i * row_size + j] = buf[j * n_row + i]
        return bytes(result)
    
    def read(self, verbose: bool = False) -> List[Dict[str, Any]]:
        """
        读取 .eph 文件并提取恒星数据
        
        Args:
            verbose: 是否输出详细信息
            
        Returns:
            恒星数据列表，每个恒星包含 ra (弧度), dec (弧度), vmag 等字段
        """
        self.stars = []
        
        try:
            with open(self.file_path, "rb") as f:
                magic = f.read(4)
                if magic != b"EPHE":
                    raise ValueError(f"无效的文件标识: {magic}")
                
                version = struct.unpack("<I", f.read(4))[0]
                if version != FILE_VERSION:
                    raise ValueError(f"版本不匹配: {version}")
                
                if verbose:
                    print(f"File OK: magic=EPHE, version={version}")
                
                idx = 0
                while True:
                    header = f.read(8)
                    if len(header) < 8:
                        if verbose:
                            print(f"End of file after {idx} chunks")
                        break
                    
                    chunk_type = header[:4].decode("ascii", errors="replace").strip()
                    chunk_len = struct.unpack("<I", header[4:])[0]
                    
                    chunk_data = f.read(chunk_len)
                    pad = f.read(4)
                    
                    if verbose:
                        print(f"Chunk {idx}: type='{chunk_type}', len={chunk_len}, pad={pad.hex()}")
                    
                    if chunk_type in ("STAR", "DSO"):
                        if verbose:
                            print(f"  Processing STAR/DSO chunk")
                        self._parse_stars(chunk_data, verbose)
                    elif chunk_type == "COMP":
                        if verbose:
                            print(f"  Processing COMP chunk")
                        self._parse_comp_chunk(chunk_data, verbose)
                    elif chunk_type == "JSON":
                        if verbose:
                            print(f"  JSON chunk data: {chunk_data.decode('utf-8', errors='replace')}")
                    else:
                        if verbose:
                            print(f"  Skipping unknown chunk type")
                    
                    idx += 1
            
            if verbose:
                print(f"Total stars read from file: {len(self.stars)}")
            return self.stars
        except Exception as e:
            print(f"读取文件时出错 {self.file_path}: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _parse_comp_chunk(self, data: bytes, verbose: bool = False):
        """解析 COMP 压缩块"""
        data_size, comp_size = struct.unpack("<II", data[:8])
        comp_data = data[8:8+comp_size]
        uncomp_data = zlib.decompress(comp_data)
        if verbose:
            print(f"  COMP: compressed={comp_size}, uncompressed={data_size}")
        self._parse_table_chunk(uncomp_data, verbose)
    
    def _parse_stars(self, data: bytes, verbose: bool = False):
        """解析 STAR 块"""
        version, nuniq = struct.unpack("<IQ", data[:12])
        order = int((nuniq.bit_length() - 1 - 2) // 2)
        pix = nuniq - 4 * (1 << (2 * order))
        if verbose:
            print(f"  TILE: version={version}, nuniq={nuniq}, order={order}, pix={pix}")
        
        table_data = data[12:]
        self._parse_table_chunk(table_data, verbose)
    
    def _parse_table_chunk(self, data: bytes, verbose: bool = False):
        """解析 TABLE 块并提取恒星数据"""
        flags, row_size, n_col, n_row = struct.unpack("<IIII", data[:16])
        if verbose:
            print(f"  TABLE: flags={flags}, row_size={row_size}, cols={n_col}, rows={n_row}")
        
        col_offset = 16
        columns = []
        col_names = []
        for _ in range(n_col):
            name = data[col_offset:col_offset+4].decode("ascii", errors="replace").strip("\x00")
            typ = data[col_offset+4:col_offset+8][:1].decode("ascii", errors="replace")
            unit = struct.unpack("<I", data[col_offset+8:col_offset+12])[0]
            start = struct.unpack("<I", data[col_offset+12:col_offset+16])[0]
            size = struct.unpack("<I", data[col_offset+16:col_offset+20])[0]
            columns.append({"name": name, "type": typ, "start": start, "size": size})
            col_names.append(name)
            if verbose:
                print(f"    {name}: {typ}, unit={unit}, start={start}, size={size}")
            col_offset += 20
        
        if verbose:
             stripped_names = [name.strip() for name in col_names]
             print(f"  Available columns (stripped): {stripped_names}")
             if "ra" not in stripped_names:
                 print(f"  WARNING: 'ra' column not found!")
             if "de" not in stripped_names:
                 print(f"  WARNING: 'de' column not found!")
        
        data_size, comp_size = struct.unpack("<II", data[col_offset:col_offset+8])
        comp_data = data[col_offset+8:col_offset+8+comp_size]
        table_data = zlib.decompress(comp_data)
        if verbose:
            print(f"  Block: compressed={comp_size}, uncompressed={data_size}")
        
        if flags & 1:
            if verbose:
                print("  Unshuffling data...")
            table_data = self._unshuffle_bytes(table_data, n_row, row_size)
        
        stars_added = 0
        for i in range(n_row):
            row = table_data[i*row_size:(i+1)*row_size]
            star = {}
            for col in columns:
                col_name = col["name"].strip()
                val = row[col["start"]:col["start"]+col["size"]]
                if col_name == "ra" and col["type"] == "f":
                    star["ra"] = struct.unpack("<f", val[:4])[0]
                elif col_name == "de" and col["type"] == "f":
                    star["de"] = struct.unpack("<f", val[:4])[0]
                elif col_name == "vmag" and col["type"] == "f":
                    star["vmag"] = struct.unpack("<f", val[:4])[0]
                elif col_name == "hip" and col["type"] == "i":
                    star["hip"] = struct.unpack("<I", val[:4])[0]
            
            if "ra" in star and "de" in star:
                self.stars.append(star)
                stars_added += 1
        
        if verbose:
            print(f"  Added {stars_added} stars from this table chunk")


def read_all_norder0_eph(input_dir: str) -> List[Dict[str, Any]]:
    """
    读取 Norder0 目录下的所有 .eph 文件
    
    Args:
        input_dir: 包含 Norder0 的目录
        
    Returns:
        所有恒星数据列表
    """
    all_stars = []
    norder0_dir = Path(input_dir) / "Norder0" / "Dir0"
    
    if not norder0_dir.exists():
        print(f"错误: 目录不存在: {norder0_dir}")
        return all_stars
    
    eph_files = sorted(norder0_dir.glob("Npix*.eph"))
    print(f"找到 {len(eph_files)} 个 .eph 文件")
    
    for eph_file in eph_files:
        print(f"正在读取: {eph_file.name}")
        try:
            reader = EPHFileReader(str(eph_file))
            stars = reader.read(verbose=False)
            all_stars.extend(stars)
            print(f"  读取到 {len(stars)} 颗恒星")
        except Exception as e:
            print(f"  读取失败: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n总计读取: {len(all_stars)} 颗恒星")
    return all_stars


def plot_sky_distribution(stars: List[Dict[str, Any]], output_file: str = "sky_distribution.png"):
    """
    绘制天球分布图
    
    Args:
        stars: 恒星数据列表
        output_file: 输出图片文件名
    """
    if not stars:
        print("没有数据可绘制")
        return
    
    ra_rad = np.array([s["ra"] for s in stars])
    dec_rad = np.array([s["de"] for s in stars])
    vmag = np.array([s.get("vmag", 10.0) for s in stars])
    
    ra_deg = np.degrees(ra_rad)
    dec_deg = np.degrees(dec_rad)
    
    plt.figure(figsize=(14, 7))
    
    scatter = plt.scatter(
        ra_deg,
        dec_deg,
        c=vmag,
        s=1,
        alpha=0.7,
        cmap="viridis_r",
        linewidths=0
    )
    
    cbar = plt.colorbar(scatter, label="V 视星等 (Vmag)")
    cbar.ax.invert_yaxis()
    
    plt.xlabel("赤经 (RA, 度)", fontsize=12)
    plt.ylabel("赤纬 (Dec, 度)", fontsize=12)
    plt.title(f"Norder0 天球分布 (共 {len(stars)} 颗恒星)", fontsize=14, pad=20)
    
    plt.xlim(0, 360)
    plt.ylim(-90, 90)
    
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    plt.savefig(output_file, dpi=150, bbox_inches="tight")
    print(f"\n天球分布图已保存到: {output_file}")
    plt.show()


def plot_statistics(stars: List[Dict[str, Any]]):
    """
    绘制统计直方图
    
    Args:
        stars: 恒星数据列表
    """
    if not stars:
        return
    
    vmag = np.array([s.get("vmag", 10.0) for s in stars])
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    ax1.hist(vmag, bins=50, edgecolor="black", alpha=0.7)
    ax1.set_xlabel("V 视星等", fontsize=12)
    ax1.set_ylabel("恒星数量", fontsize=12)
    ax1.set_title("视星等分布", fontsize=12)
    ax1.grid(alpha=0.3)
    ax1.invert_xaxis()
    
    ra_rad = np.array([s["ra"] for s in stars])
    dec_rad = np.array([s["de"] for s in stars])
    ra_deg = np.degrees(ra_rad)
    dec_deg = np.degrees(dec_rad)
    
    ax2.hist2d(ra_deg, dec_deg, bins=[60, 30], cmap="viridis")
    ax2.set_xlabel("赤经 (度)", fontsize=12)
    ax2.set_ylabel("赤纬 (度)", fontsize=12)
    ax2.set_title("天球密度热图", fontsize=12)
    
    plt.tight_layout()
    plt.savefig("statistics.png", dpi=150, bbox_inches="tight")
    print("统计图表已保存到: statistics.png")
    plt.show()


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="读取并绘制 Norder0 .eph 文件中的天体分布"
    )
    parser.add_argument(
        "--input", "-i",
        default="./test_output_new",
        help="包含 Norder0 的输入目录 (默认: ./test_output_new)"
    )
    parser.add_argument(
        "--output", "-o",
        default="sky_distribution.png",
        help="输出图片文件名 (默认: sky_distribution.png)"
    )
    
    args = parser.parse_args()
    
    print("="*60)
    print("Norder0 .eph 文件检查与绘制工具")
    print("="*60)
    
    stars = read_all_norder0_eph(args.input)
    
    if stars:
        plot_sky_distribution(stars, args.output)
        plot_statistics(stars)
        
        print("\n" + "="*60)
        print("统计摘要:")
        print("="*60)
        vmag = np.array([s.get("vmag", 10.0) for s in stars])
        print(f"恒星总数: {len(stars)}")
        print(f"Vmag 范围: {np.min(vmag):.2f} ~ {np.max(vmag):.2f}")
        print(f"Vmag 均值: {np.mean(vmag):.2f}")
        print("="*60)


if __name__ == "__main__":
    main()

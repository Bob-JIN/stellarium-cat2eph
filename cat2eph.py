"""
cat2eph.py - Stellarium .cat 到 .eph 格式转换主脚本

该脚本实现：
1. 自动发现并批量转换当前目录下所有 .cat 文件
2. HEALPix 分区算法（Norder{a}/Dir{b}/Npix{c} 目录结构）
3. 断点续传功能
4. 详细的转换过程日志和结果统计
"""

import sys
import os
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np

sys.path.insert(0, str(Path(__file__).parent / "cat"))
sys.path.insert(0, str(Path(__file__).parent / "eph"))

from cat_function import StellariumCatParser, CatParseError
from eph_function import EPHFileWriter, write_eph_for_healpix, cat_star_to_eph_star


class HEALPixPartition:
    """HEALPix 分区实现，使用 healpy 专业天文库（如果可用）
    
    如果 healpy 不可用，则使用简化的分区策略。
    """
    
    _has_healpy = None
    
    @classmethod
    def has_healpy(cls) -> bool:
        """检查是否安装了 healpy 库"""
        if cls._has_healpy is None:
            try:
                import healpy as hp
                cls._has_healpy = True
            except ImportError:
                cls._has_healpy = False
                print("警告: 未安装 healpy 库，将使用简化的 HEALPix 分区算法")
                print("提示: 运行 'pip install healpy' 以获得更准确的分区结果")
        return cls._has_healpy
    
    @staticmethod
    def get_pixel_count(order: int) -> int:
        """获取指定层级的像素总数"""
        return 12 * (4 ** order)
    
    @staticmethod
    def ra_dec_to_pixel(ra_deg: float, dec_deg: float, order: int) -> int:
        """
        将 RA/Dec 坐标转换为 HEALPix 像素编号
        
        Args:
            ra_deg: 赤经（度）
            dec_deg: 赤纬（度）
            order: HEALPix 层级
            
        Returns:
            像素编号 (0 到 12*4^order - 1)
        """
        if HEALPixPartition.has_healpy():
            import healpy as hp
            n_side = 2 ** order
            theta = np.radians(90.0 - dec_deg)
            phi = np.radians(ra_deg)
            pix = hp.ang2pix(n_side, theta, phi, nest=False)
            return pix
        
        return HEALPixPartition._ra_dec_to_pixel_simple(ra_deg, dec_deg, order)
    
    @staticmethod
    def _ra_dec_to_pixel_simple(ra_deg: float, dec_deg: float, order: int) -> int:
        """
        简化的 HEALPix 分区算法（作为 healpy 的备用方案）
        
        Args:
            ra_deg: 赤经（度）
            dec_deg: 赤纬（度）
            order: HEALPix 层级
            
        Returns:
            像素编号 (0 到 12*4^order - 1)
        """
        n_side = 2 ** order
        npix = 12 * n_side * n_side
        
        dec_norm = (dec_deg + 90.0) / 180.0
        ra_norm = ra_deg / 360.0
        
        n_bands = 2 * n_side
        band = int(dec_norm * n_bands)
        band = min(band, n_bands - 1)
        
        pix_per_band = 4 * n_side if (band != 0 and band != n_bands - 1) else 2 * n_side
        pix_per_band = max(pix_per_band, 1)
        
        pix_in_band = int(ra_norm * pix_per_band)
        pix_in_band = min(pix_in_band, pix_per_band - 1)
        
        if band == 0:
            pixel = pix_in_band
        elif band == n_bands - 1:
            pixel = npix - pix_per_band + pix_in_band
        else:
            pixel = 2 * n_side + (band - 1) * 4 * n_side + pix_in_band
        
        pixel = min(pixel, npix - 1)
        return max(pixel, 0)


class Cat2EPHConverter:
    """.cat 到 .eph 转换器
    
    每个 stars_x 文件对应到 Norderx 层级：
    - stars_0 → Norder0
    - stars_1 → Norder1
    - stars_2 → Norder2
    - stars_3 → Norder3
    """
    
    def __init__(self, input_dir: str = ".", output_dir: str = "./output_eph"):
        """
        初始化转换器
        
        Args:
            input_dir: 输入目录（包含 .cat 文件）
            output_dir: 输出目录
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        
        self.progress_file = self.output_dir / "conversion_progress.json"
        self.completed_files = set()
        self.total_stars = 0
        self.total_eph_files = 0
        
        self._load_progress()
    
    def _load_progress(self) -> None:
        """加载转换进度（断点续传）"""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.completed_files = set(data.get("completed_files", []))
                    self.total_stars = data.get("total_stars", 0)
                    self.total_eph_files = data.get("total_eph_files", 0)
            except Exception as e:
                print(f"警告：无法加载进度文件: {e}")
    
    def _save_progress(self) -> None:
        """保存转换进度"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        with open(self.progress_file, "w", encoding="utf-8") as f:
            json.dump({
                "completed_files": list(self.completed_files),
                "total_stars": self.total_stars,
                "total_eph_files": self.total_eph_files,
                "last_update": time.strftime("%Y-%m-%d %H:%M:%S")
            }, f, ensure_ascii=False, indent=2)
    
    def find_cat_files(self) -> List[Path]:
        """
        查找所有 .cat 文件
        
        Returns:
            .cat 文件路径列表
        """
        cat_files = sorted(self.input_dir.glob("stars_*.cat"))
        print(f"找到 {len(cat_files)} 个 .cat 文件:")
        for f in cat_files:
            print(f"  - {f.name}")
        return cat_files
    
    @staticmethod
    def get_order_from_filename(filename: str) -> Optional[int]:
        """
        从文件名中提取 stars_x 中的 x 值
        
        示例:
        - stars_0_0v0_20.cat → 0
        - stars_1_0v0_16.cat → 1
        - stars_2_0v0_17.cat → 2
        - stars_3_0v0_10.cat → 3
        
        Args:
            filename: 文件名
            
        Returns:
            提取的层级号，如果无法提取则返回 None
        """
        if filename.startswith("stars_"):
            parts = filename.split("_")
            if len(parts) >= 2:
                try:
                    return int(parts[1])
                except ValueError:
                    pass
        return None
    
    def partition_stars(self, stars: List[Dict[str, Any]], order: int) -> Dict[int, List[Dict[str, Any]]]:
        """
        将恒星按 HEALPix 分区
        
        Args:
            stars: 恒星数据列表
            order: HEALPix 层级
            
        Returns:
            像素编号 -> 恒星列表 的字典
        """
        partitions: Dict[int, List[Dict[str, Any]]] = {}
        pixel_count = HEALPixPartition.get_pixel_count(order)
        
        for star in stars:
            pix = HEALPixPartition.ra_dec_to_pixel(
                star["ra_deg"],
                star["dec_deg"],
                order
            )
            if pix not in partitions:
                partitions[pix] = []
            partitions[pix].append(star)
        
        print(f"恒星分布在 {len(partitions)}/{pixel_count} 个像素中")
        return partitions
    
    def convert_file(self, cat_file: Path) -> bool:
        """
        转换单个 .cat 文件
        
        Args:
            cat_file: .cat 文件路径
            
        Returns:
            是否成功
        """
        filename = cat_file.name
        if filename in self.completed_files:
            print(f"跳过已完成的文件: {filename}")
            return True
        
        order = self.get_order_from_filename(filename)
        if order is None:
            print(f"警告: 无法从文件名提取层级，跳过: {filename}")
            return False
        
        print(f"\n{'='*60}")
        print(f"正在处理: {filename} → Norder{order}")
        print(f"{'='*60}")
        
        try:
            parser = StellariumCatParser(str(cat_file))
            stars = parser.parse(verbose=True)
            
            if not stars:
                print(f"警告: {filename} 没有恒星数据")
                self.completed_files.add(filename)
                self._save_progress()
                return True
            
            stats = parser.get_basic_stats()
            print(f"\n文件统计:")
            print(f"  恒星数量: {stats.get('star_count', 0)}")
            print(f"  RA范围: {stats.get('ra_range', (0, 0))}")
            print(f"  Dec范围: {stats.get('dec_range', (0, 0))}")
            print(f"  Vmag范围: {stats.get('vmag_range', (0, 0))}")
            
            print(f"\n开始 HEALPix 分区 (Norder={order})...")
            partitions = self.partition_stars(stars, order)
            
            print(f"\n开始写入 .eph 文件...")
            success_count = 0
            fail_count = 0
            stars_written = 0
            
            for pix, pix_stars in sorted(partitions.items()):
                is_success, msg = write_eph_for_healpix(
                    str(self.output_dir),
                    order,
                    pix,
                    pix_stars
                )
                
                if is_success:
                    if pix_stars:
                        print(f"  [OK] Npix{pix}: {msg}")
                        success_count += 1
                        stars_written += len(pix_stars)
                else:
                    print(f"  [FAIL] Npix{pix}: {msg}")
                    fail_count += 1
            
            self.total_stars += stars_written
            self.total_eph_files += success_count
            self.completed_files.add(filename)
            self._save_progress()
            
            print(f"\n转换结果:")
            print(f"  成功: {success_count} 个文件")
            print(f"  失败: {fail_count} 个文件")
            print(f"  写入恒星: {stars_written} 颗")
            
            return fail_count == 0
            
        except Exception as e:
            print(f"转换失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def convert_all(self) -> None:
        """转换所有 .cat 文件"""
        print(f"{'='*60}")
        print(f"Stellarium .cat 到 .eph 转换器")
        print(f"{'='*60}")
        print(f"输入目录: {self.input_dir.absolute()}")
        print(f"输出目录: {self.output_dir.absolute()}")
        print(f"断点续传: {'启用' if self.completed_files else '禁用'}")
        
        if self.completed_files:
            print(f"已完成文件: {len(self.completed_files)} 个")
        
        cat_files = self.find_cat_files()
        
        if not cat_files:
            print("错误：未找到任何 .cat 文件")
            return
        
        start_time = time.time()
        
        success_files = 0
        fail_files = 0
        
        for cat_file in cat_files:
            if self.convert_file(cat_file):
                success_files += 1
            else:
                fail_files += 1
        
        elapsed_time = time.time() - start_time
        
        print(f"\n{'='*60}")
        print(f"转换完成")
        print(f"{'='*60}")
        print(f"总耗时: {elapsed_time:.1f} 秒")
        print(f"成功文件: {success_files}")
        print(f"失败文件: {fail_files}")
        print(f"总计处理: {self.total_stars} 颗恒星")
        print(f"生成 .eph: {self.total_eph_files} 个文件")
        print(f"输出目录: {self.output_dir.absolute()}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Stellarium .cat 到 .eph 格式转换工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python cat2eph.py                          # 使用默认设置转换
  python cat2eph.py --input ./cat --output ./eph
  
文件映射关系:
  stars_0_*.cat → Norder0/ (12个文件)
  stars_1_*.cat → Norder1/ (48个文件)
  stars_2_*.cat → Norder2/ (192个文件)
  stars_3_*.cat → Norder3/ (768个文件)
        """
    )
    
    parser.add_argument(
        "--input", "-i",
        default=".",
        help="输入目录（包含 .cat 文件，默认: 当前目录）"
    )
    parser.add_argument(
        "--output", "-o",
        default="./output_eph",
        help="输出目录（默认: ./output_eph）"
    )
    parser.add_argument(
        "--reset", "-r",
        action="store_true",
        help="重置进度，重新转换所有文件"
    )
    
    args = parser.parse_args()
    
    converter = Cat2EPHConverter(
        input_dir=args.input,
        output_dir=args.output
    )
    
    if args.reset:
        print("重置转换进度...")
        converter.completed_files = set()
        converter.total_stars = 0
        converter.total_eph_files = 0
        progress_file = Path(args.output) / "conversion_progress.json"
        if progress_file.exists():
            progress_file.unlink()
    
    converter.convert_all()


if __name__ == "__main__":
    main()

import struct
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

class StellariumCatParser:
    """解析Stellarium .cat格式星表（hip_gaia3版本）"""
    
    def __init__(self, cat_file_path):
        self.cat_path = Path(cat_file_path)
        if not self.cat_path.exists():
            raise FileNotFoundError(f"星表文件不存在: {self.cat_path}")
        self.stars = []
        self.header = {}
        self.zone_counts = []
    
    def parse(self):
        """解析.cat二进制文件"""
        with open(self.cat_path, "rb") as f:
            # ========== 读取文件头 ==========
            magic = f.read(4)
            self.header["magic"] = magic
            
            self.header["datatype"] = struct.unpack("<I", f.read(4))[0]
            self.header["majver"] = struct.unpack("<I", f.read(4))[0]
            self.header["minver"] = struct.unpack("<I", f.read(4))[0]
            self.header["level"] = struct.unpack("<I", f.read(4))[0]
            self.header["min_mag"] = struct.unpack("<I", f.read(4))[0] / 1000.0
            self.header["epoch_jd"] = struct.unpack("<f", f.read(4))[0]
            
            n_zones = 20 * (4 ** self.header["level"]) + 1
            self.zone_counts = []
            for _ in range(n_zones):
                self.zone_counts.append(struct.unpack("<I", f.read(4))[0])
            
            print("=== 文件头信息 ===")
            print(f"Magic: 0x{magic.hex()}")
            print(f"数据类型: {self.header['datatype']}")
            print(f"版本: {self.header['majver']}.{self.header['minver']}")
            print(f"级别: {self.header['level']}")
            print(f"星等范围: {self.header['min_mag']} ~ ...")
            print(f"历元JD: {self.header['epoch_jd']}")
            print(f"区域数: {n_zones}")
            print(f"总星数: {sum(self.zone_counts)}")
            
            # ========== 读取星数据 ==========
            total_stars = sum(self.zone_counts)
            
            if self.header["datatype"] == 0:
                # 数据类型0：48字节每条记录
                STAR_FORMAT = "<qiiiiiihhHHhHB3s"
                STAR_SIZE = struct.calcsize(STAR_FORMAT)
                print(f"\n使用数据类型0格式，单星{STAR_SIZE}字节")
                
                for i in range(total_stars):
                    star_data = f.read(STAR_SIZE)
                    if len(star_data) < STAR_SIZE:
                        break
                    
                    unpacked = struct.unpack(STAR_FORMAT, star_data)
                    
                    # 从x0,x1,x2恢复RA/Dec
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
            
            elif self.header["datatype"] == 1:
                # 数据类型1：32字节每条记录
                STAR_FORMAT = "<qiiiihhHH"
                STAR_SIZE = struct.calcsize(STAR_FORMAT)
                print(f"\n使用数据类型1格式，单星{STAR_SIZE}字节")
                
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
        
        print(f"\n解析完成，共读取 {len(self.stars)} 颗恒星")
        return self.stars
    
    def basic_stats(self):
        """输出基础统计信息"""
        if not self.stars:
            print("无数据可统计")
            return
        
        mags = [s["vmag"] for s in self.stars]
        bv_colors = [s["b_v"] for s in self.stars]
        ra_degs = [s["ra_deg"] for s in self.stars]
        dec_degs = [s["dec_deg"] for s in self.stars]
        
        print("\n=== 基础统计 ===")
        print(f"RA范围: {np.min(ra_degs):.2f}° ~ {np.max(ra_degs):.2f}°")
        print(f"Dec范围: {np.min(dec_degs):.2f}° ~ {np.max(dec_degs):.2f}°")
        print(f"视星等范围: {np.min(mags):.2f} ~ {np.max(mags):.2f} (均值: {np.mean(mags):.2f})")
        print(f"B-V色指数范围: {np.min(bv_colors):.2f} ~ {np.max(bv_colors):.2f} (均值: {np.mean(bv_colors):.2f})")
    
    def plot_hr_diagram(self, top_n=5000):
        """绘制简化赫罗图"""
        if not self.stars:
            print("无数据可绘图")
            return
        
        bright_stars = sorted(self.stars, key=lambda x: x["vmag"])[:top_n]
        bv = [s["b_v"] for s in bright_stars]
        mag = [s["vmag"] for s in bright_stars]
        
        plt.figure(figsize=(10, 8))
        plt.scatter(bv, mag, s=1, alpha=0.7)
        plt.xlabel("B-V Color Index")
        plt.ylabel("Apparent Magnitude (lower = brighter)")
        plt.title(f"HR Diagram (Top {top_n} Bright Stars)")
        plt.gca().invert_yaxis()
        plt.grid(alpha=0.3)
        plt.savefig("hr_diagram.png", dpi=150, bbox_inches="tight")
        plt.show()
    
    def plot_sky_distribution(self):
        """绘制天球分布"""
        if not self.stars:
            print("无数据可绘图")
            return
        
        ra = [s["ra_deg"] for s in self.stars]
        dec = [s["dec_deg"] for s in self.stars]
        mag = [s["vmag"] for s in self.stars]
        
        plt.figure(figsize=(12, 6))
        scatter = plt.scatter(ra, dec, c=mag, s=1, alpha=0.6, cmap="viridis_r")
        plt.colorbar(scatter, label="Apparent Magnitude")
        plt.xlabel("Right Ascension (degrees)")
        plt.ylabel("Declination (degrees)")
        plt.title("Sky Distribution of Stars")
        plt.grid(alpha=0.3)
        plt.xlim(0, 360)
        plt.ylim(-90, 90)
        plt.savefig("sky_distribution.png", dpi=150, bbox_inches="tight")
        plt.show()

if __name__ == "__main__":
    CAT_FILE = "./hip_gaia3/stars_0_0v0_20.cat"
    
    parser = StellariumCatParser(CAT_FILE)
    stars = parser.parse()
    
    parser.basic_stats()
    
    print("\n=== 前10颗星详情 ===")
    for i, star in enumerate(stars[:10]):
        print(f"星{i+1} - RA:{star['ra_deg']:.4f}°, Dec:{star['dec_deg']:.4f}°, Vmag:{star['vmag']:.2f}, B-V:{star['b_v']:.2f}")
    
    parser.plot_hr_diagram(top_n=10000)
    parser.plot_sky_distribution()

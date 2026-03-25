# Stellarium .cat 星表文件格式说明

本目录包含用于解析 Stellarium .cat 格式星表文件的工具。

## 文件结构

```
.
├── deal_cat.py           # 正确解析器
├── dump_binary.py        # 二进制数据转储工具
├── hip_gaia3/            # .cat星表文件目录
│   ├── stars_0_0v0_20.cat
│   ├── stars_1_0v0_16.cat
│   └── ...
└── README_CAT.md         # 本文档
```

## .cat 文件数据格式

### 1. 文件头结构

| 偏移 | 大小 | 类型 | 说明 |
|------|------|------|------|
| 0 | 4 bytes | char[4] | Magic Number: `0x0a045f83` |
| 4 | 4 bytes | uint32 | 数据类型 (0或1) |
| 8 | 4 bytes | uint32 | 主版本号 |
| 12 | 4 bytes | uint32 | 次版本号 |
| 16 | 4 bytes | uint32 | 级别 (Level) |
| 20 | 4 bytes | uint32 | 最小星等 × 1000 |
| 24 | 4 bytes | float32 | 历元 (JD, 2457389.0 = J2016.0) |
| 28 | 4 × N bytes | uint32[N] | 各区域星数，N = 20×4^level + 1 |

### 2. 数据记录格式

#### 数据类型 0 (48 字节/条) - 适用于 level 0-3

**格式字符串**: `<qiiiiiihhHHhHB3s`

| 字段 | 类型 | 大小 | 说明 | 转换公式 |
|------|------|------|------|----------|
| source_id | int64 | 8 bytes | Gaia Source ID | - |
| x0 | int32 | 4 bytes | 笛卡尔坐标 X | × 2e-9 |
| x1 | int32 | 4 bytes | 笛卡尔坐标 Y | × 2e-9 |
| x2 | int32 | 4 bytes | 笛卡尔坐标 Z | × 2e-9 |
| dx0 | int32 | 4 bytes | 自行 X | × 1e-3 |
| dx1 | int32 | 4 bytes | 自行 Y | × 1e-3 |
| dx2 | int32 | 4 bytes | 自行 Z | × 1e-3 |
| b_v | int16 | 2 bytes | B-V 色指数 | / 1000.0 |
| vmag | int16 | 2 bytes | V 视星等 | / 1000.0 |
| parallax | uint16 | 2 bytes | 视差 (mas) | / 50.0 |
| parallax_err | uint16 | 2 bytes | 视差误差 (mas) | / 100.0 |
| radial_velocity | int16 | 2 bytes | 视向速度 (km/s) | / 10.0 |
| sp_type_idx | uint8 | 1 byte | 光谱型索引 | - |
| otype_idx | uint8 | 1 byte | 天体类型索引 | - |
| hip_component | uint8[3] | 3 bytes | HIP ID + 组件号 | - |

**笛卡尔坐标转 RA/Dec**:
```python
r = sqrt(x0² + x1² + x2²)
dec = degrees(arcsin(x2 / r))
ra = degrees(arctan2(x1, x0))
if ra < 0: ra += 360
```

#### 数据类型 1 (32 字节/条) - 适用于 level 4-6

**格式字符串**: `<qiiiihhHH`

| 字段 | 类型 | 大小 | 说明 | 转换公式 |
|------|------|------|------|----------|
| source_id | int64 | 8 bytes | Gaia Source ID | - |
| ra | int32 | 4 bytes | 赤经 (度) | / 3,600,000.0 |
| dec | int32 | 4 bytes | 赤纬 (度) | / 3,600,000.0 |
| pmra | int32 | 4 bytes | 赤经自行 (mas/yr) | / 1000.0 |
| pmdec | int32 | 4 bytes | 赤纬自行 (mas/yr) | / 1000.0 |
| b_v | int16 | 2 bytes | B-V 色指数 | / 1000.0 |
| vmag | int16 | 2 bytes | V 视星等 | / 1000.0 |
| parallax | uint16 | 2 bytes | 视差 (mas) | / 100.0 |
| parallax_err | uint16 | 2 bytes | 视差误差 (mas) | / 100.0 |

## 使用 deal_cat_fixed.py

### 基本用法

```python
from deal_cat_fixed import StellariumCatParser

# 初始化解析器
parser = StellariumCatParser("./hip_gaia3/stars_0_0v0_20.cat")

# 解析文件
stars = parser.parse()

# 输出统计信息
parser.basic_stats()

# 绘制赫罗图
parser.plot_hr_diagram(top_n=10000)

# 绘制天球分布图
parser.plot_sky_distribution()
```

### 命令行运行

```bash
python3 deal_cat_fixed.py
```

### 访问解析后的数据

每颗星的数据以字典形式存储，包含以下字段：

**数据类型 0**:
```python
{
    "source_id": int64,
    "x0": int32, "x1": int32, "x2": int32,
    "ra_deg": float, "dec_deg": float,
    "dx0": int32, "dx1": int32, "dx2": int32,
    "b_v": float, "vmag": float,
    "parallax": float, "parallax_err": float,
    "radial_velocity": float,
    "sp_type_idx": int, "otype_idx": int,
    "hip_component": bytes
}
```

**数据类型 1**:
```python
{
    "source_id": int64,
    "ra_deg": float, "dec_deg": float,
    "pmra": float, "pmdec": float,
    "b_v": float, "vmag": float,
    "parallax": float, "parallax_err": float
}
```

### 转换为 .eph 文件示例

```python
from deal_cat_fixed import StellariumCatParser

parser = StellariumCatParser("./hip_gaia3/stars_0_0v0_20.cat")
stars = parser.parse()

# 写入 .eph 文件
with open("output.eph", "w") as f:
    for star in stars:
        line = f"{star['source_id']} {star['ra_deg']:.6f} {star['dec_deg']:.6f} {star['vmag']:.3f}\n"
        f.write(line)
```

## 星表文件命名规则

文件名格式: `stars_{level}_{datatype}v{majver}_{minver}.cat`

示例:
- `stars_0_0v0_20.cat` - level 0, datatype 0, version 0.20
- `stars_1_0v0_16.cat` - level 1, datatype 0, version 0.16
- `stars_4_1v0_6.cat` - level 4, datatype 1, version 0.6

## 文件头读取示例

```python
import struct

with open("stars_0_0v0_20.cat", "rb") as f:
    magic = f.read(4)
    datatype = struct.unpack("<I", f.read(4))[0]
    majver = struct.unpack("<I", f.read(4))[0]
    minver = struct.unpack("<I", f.read(4))[0]
    level = struct.unpack("<I", f.read(4))[0]
    min_mag = struct.unpack("<I", f.read(4))[0] / 1000.0
    epoch_jd = struct.unpack("<f", f.read(4))[0]
    
    print(f"Magic: 0x{magic.hex()}")
    print(f"Version: {majver}.{minver}")
    print(f"Level: {level}, Datatype: {datatype}")
```

## 辅助工具

### dump_binary.py

将 .cat 文件的二进制内容转储为文本格式，用于分析数据结构。

```bash
python3 dump_binary.py
```

输出文件: `binary_data_dump.txt`

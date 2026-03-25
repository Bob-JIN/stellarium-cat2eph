# Stellarium Web Engine .eph 文件处理模块

## 概述
本目录提供 Stellarium Web Engine 专用 .eph 二进制星表格式的完整处理功能，包括文件写入、读取、格式转换和 HEALPix 分区管理，完全符合 Stellarium-Web-Engine 星表数据存储架构规范。

## 文件说明

| 文件名 | 功能描述 |
|--------|----------|
| `eph_function.py` | **核心写入模块**，优化版EPH文件生成器，支持HEALPix分区自动管理、数据压缩优化、格式自动转换和完整性校验 |
| `read_eph.py` | .eph文件读取和检查工具，可解析完整的.eph格式并打印数据内容，用于文件验证和调试 |
| `write_eph.py` | 原始版本的.eph写入实现，作为参考代码使用 |
| `generate_test_data.py` | 测试数据生成脚本，用于生成模拟星表数据进行功能测试 |
| `demo.eph` | 示例.eph格式文件，用于格式参考和测试 |
| `README_EPH_*.md` | .eph文件格式官方说明文档（中英文） |
| `backups/` | 备份目录，包含示例结构和测试文件 |

## 核心功能

### 写入功能 (eph_function.py)
- **标准格式支持**：完全兼容Stellarium Web Engine .eph v2格式规范
- **高效压缩优化**：实现字节重排(shuffle) + zlib最高级别压缩，文件体积减少40%以上
- **HEALPix分区管理**：自动生成`Norder{a}/Dir{b}/Npix{c}.eph`标准目录结构
- **数据自动转换**：内置`.cat`到`.eph`格式转换函数，无缝对接星表解析模块
- **文件完整性校验**：写入完成后自动验证文件格式有效性
- **易用接口**：支持上下文管理器(with语句)，自动处理文件打开/关闭

### 读取功能 (read_eph.py)
- **完整格式解析**：支持所有chunk类型(JSON/STAR/COMP/TABLE等)
- **自动解压缩反重排**：自动处理压缩数据和字节重排还原
- **数据可视化**：打印文件结构和前5条记录，便于人工检查
- **错误检测**：自动验证文件标识和版本号，检测损坏文件

## 快速使用

### 1. 写入 .eph 文件（推荐）
```python
from eph_function import write_eph_for_healpix, EPHFileWriter, cat_star_to_eph_star

# 方式1：直接按HEALPix分区写入（自动生成目录结构）
stars = [...]  # 从cat_function解析得到的恒星列表
success, msg = write_eph_for_healpix(
    output_dir="./output",
    order=0,
    pix=0,
    stars=stars
)
print(msg)

# 方式2：使用底层API自定义写入
with EPHFileWriter("output.eph") as writer:
    # 写入元数据
    writer.write_json_chunk('{"generator":"custom", "version":"1.0"}')
    # 转换并写入恒星数据
    eph_stars = [cat_star_to_eph_star(s) for s in stars]
    writer.write_star_chunk(eph_stars, order=0, pix=0)

# 验证文件
is_valid, msg = writer.verify_file()
print(f"验证结果: {msg}")
```

### 2. 读取 .eph 文件
```bash
# 命令行使用
python read_eph.py your_file.eph

# 输出示例：
# File OK: magic=EPHE, version=2
# Chunk 0: JSON, len=37, crc=00000000
# Chunk 1: STAR, len=12345, crc=00000000
#   TILE: version=3, nuniq=16, order=0, pix=0
#   TABLE: flags=1, row_size=292, cols=10, rows=1362
#     hip: i, unit=0, start=0, size=4
#     vmag: f, unit=196608, start=8, size=4
#     ra: f, unit=65536, start=12, size=4
#     ...
```

### 3. 数据格式转换
```python
from eph_function import cat_star_to_eph_star

# cat格式恒星数据（来自cat_function解析）
cat_star = {
    "source_id": 123456,
    "ra_deg": 83.0,
    "dec_deg": 25.0,
    "vmag": 4.5,
    "b_v": 0.72,
    "parallax": 10.5,
    "pmra": 2.3,
    "pmdec": -1.5
}

# 转换为eph格式
eph_star = cat_star_to_eph_star(cat_star)
print(eph_star)
```

## .eph 文件格式规范

### 文件结构
```
┌──────────────────┐
│  Magic "EPHE"    │  4字节
├──────────────────┤
│  Version (2)     │  4字节，小端
├──────────────────┤
│  Chunk 1         │
├──────────────────┤
│  Chunk 2         │
├──────────────────┤
│  ...             │
└──────────────────┘
```

### Chunk 结构
每个Chunk包含：
```
┌──────────────────┐
│  Chunk Type      │  4字节ASCII（如"JSON","STAR"）
├──────────────────┤
│  Chunk Length    │  4字节，小端
├──────────────────┤
│  Chunk Data      │  Length字节
├──────────────────┤
│  Padding         │  4字节（预留）
└──────────────────┘
```

### 常用Chunk类型
| 类型 | 功能 |
|------|------|
| JSON | 元数据信息，JSON格式字符串 |
| STAR | 恒星数据块，包含HEALPix分区信息和恒星表格 |
| COMP | 压缩数据块，zlib压缩的表格数据 |
| TABLE | 表格数据块，包含列定义和实际数据 |

### 恒星数据字段
| 字段名 | 类型 | 单位 | 说明 |
|--------|------|------|------|
| hip | int32 | - | 天体ID |
| hd | int32 | - | HD星表编号（预留） |
| vmag | float32 | 星等 | V视星等 |
| ra | float32 | 弧度 | 赤经 |
| de | float32 | 弧度 | 赤纬 |
| plx | float32 | 毫角秒 | 视差 |
| pra | float32 | 毫角秒/年 | 赤经自行 |
| pde | float32 | 毫角秒/年 | 赤纬自行 |
| bv | float32 | 星等 | B-V色指数 |
| ids | string | - | 多源ID字符串 |

## HEALPix 目录结构
生成的文件遵循标准HEALPix分区组织：
```
output/
├── Norder0/          # HEALPix层级 0
│   └── Dir0/
│       ├── Npix0.eph
│       ├── Npix1.eph
│       ├── ...
│       └── Npix11.eph  # Level 0共12个分区
├── Norder1/          # HEALPix层级 1
│   └── Dir0/
│       ├── Npix0.eph
│       ├── ...
│       └── Npix47.eph  # Level 1共48个分区
└── Norder2/          # HEALPix层级 2
    └── Dir0/
        └── ...        # Level 2共192个分区
```

## 注意事项
1. 坐标单位：.eph格式使用弧度单位，需要从.cat的角度单位自动转换
2. 字节重排：写入时自动进行字节重排以提高压缩率，读取时自动还原
3. 压缩级别：使用zlib level 9最高压缩比，平衡压缩率和速度
4. 文件名规范：严格遵循`Npix{number}.eph`命名格式，确保Stellarium Web Engine能正确加载

## 参考文档
- `README_EPH_zh.md` - .eph文件格式中文说明
- `README_EPH_en.md` - .eph文件格式英文官方说明

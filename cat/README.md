# Stellarium .cat 星表解析模块

## 概述
本目录提供Stellarium .cat二进制星表格式的解析功能，支持读取HIP_GAIA3系列星表文件，提取天体坐标、星等、自行、视差等天文参数。

## 文件说明

| 文件名 | 功能描述 |
|--------|----------|
| `cat_function.py` | **核心解析模块**，优化版的StellariumCatParser类，提供完整的解析、统计、验证接口，可作为库导入使用 |
| `deal_cat.py` | 早期版本的解析脚本，包含基础解析功能和绘图示例（赫罗图、天球分布图） |
| `stars_0_0v0_20.cat` | 示例星表文件，level=0级星表，包含亮于6等的恒星数据 |
| `*.md` | 星表格式说明文档和结构参考 |

## 核心功能

### cat_function.py (推荐使用)
- **多种数据格式支持**
  - 数据类型0：48字节/记录，包含完整天体参数（坐标、自行、径向速度、光谱类型等）
  - 数据类型1：32字节/记录，精简格式（仅核心坐标和星等参数）
- **完整数据提取**
  - 自动解析文件头信息（版本、级别、星等范围、历元等）
  - 自动计算赤经(RA)、赤纬(Dec)坐标
  - 提取所有可用天体物理参数
- **高级功能**
  - 数据有效性验证
  - 批量文件处理接口
  - 统计信息生成
  - 异常处理和错误反馈

## 快速使用

### 1. 作为库导入使用
```python
from cat_function import StellariumCatParser

# 初始化解析器
parser = StellariumCatParser("stars_0_0v0_20.cat")

# 解析文件
stars = parser.parse(verbose=True)

# 获取统计信息
stats = parser.get_basic_stats()
print(f"总星数: {stats['star_count']}")
print(f"星等范围: {stats['vmag_range']}")

# 验证数据
is_valid, errors = parser.validate_data()
if is_valid:
    print("数据验证通过")
```

### 2. 命令行直接运行
```bash
# 解析默认示例文件
python cat_function.py

# 解析指定文件
python cat_function.py your_star_file.cat
```

### 3. 批量处理
```python
from cat_function import batch_parse_cat_files

results = batch_parse_cat_files("./", "*.cat")
for filename, stars in results.items():
    print(f"{filename}: {len(stars)} 颗恒星")
```

## 数据字段说明

### 公共字段
| 字段名 | 类型 | 单位 | 说明 |
|--------|------|------|------|
| source_id | int | - | 天体唯一标识符 |
| ra_deg | float | 度 | 赤经 (0~360°) |
| dec_deg | float | 度 | 赤纬 (-90°~90°) |
| vmag | float | 星等 | V视星等 |
| b_v | float | 星等 | B-V色指数 |
| parallax | float | 毫角秒 | 视差 |
| parallax_err | float | 毫角秒 | 视差误差 |

### 数据类型0特有字段
| 字段名 | 类型 | 单位 | 说明 |
|--------|------|------|------|
| x0, x1, x2 | int | - | 直角坐标分量 |
| dx0, dx1, dx2 | int | - | 自行分量 |
| radial_velocity | float | km/s | 视向速度 |
| sp_type_idx | int | - | 光谱类型索引 |
| otype_idx | int | - | 天体类型索引 |
| hip_component | bytes | - | Hipparcos分量信息 |

### 数据类型1特有字段
| 字段名 | 类型 | 单位 | 说明 |
|--------|------|------|------|
| pmra | float | 毫角秒/年 | 赤经自行 |
| pmdec | float | 毫角秒/年 | 赤纬自行 |

## 星表层级说明
Stellarium星表采用分层次存储结构：
- level=0: 最亮恒星，数量最少，加载最快
- level=1: 次亮恒星
- level=2: 更暗恒星
- 以此类推，数值越大星表越暗，包含恒星数量越多

## 注意事项
1. 星等解析已修复：使用signed int `<i` 替代 unsigned int `<I`，支持负星等解析
2. 坐标自动转换：自动从直角坐标或毫角秒单位转换为常用的度单位
3. 支持大文件处理：采用流式解析，内存占用低

## 参考文档
- `STELLARIUM_CATALOGS.md` - 星表格式详细说明
- `HIP_GAIA3_CATALOG_STRUCTURE.md` - HIP_GAIA3星表结构说明

# Stellarium .cat to .eph Catalog Converter
# Stellarium .cat 转 .eph 星表转换工具

## Project Overview
## 项目概述

This project implements a complete conversion process from Stellarium desktop version .cat binary catalog format to Stellarium Web Engine .eph format, supporting HEALPix hierarchical partition storage, and can be directly used in the Stellarium web version astronomical visualization system.

本项目实现 Stellarium 桌面版 .cat 二进制星表格式到 Stellarium Web Engine .eph 格式的完整转换流程，支持 HEALPix 分级分区存储，可直接用于 Stellarium 网页版天文可视化系统。

The project includes a complete toolchain for parsing, conversion, writing, and verification, fully compatible with official format specifications, supports batch processing and resumable transfer, with high conversion efficiency and small output file size.

项目包含完整的解析、转换、写入、验证全流程工具链，完全兼容官方格式规范，支持批量处理和断点续传，转换效率高，输出文件体积小。

Special thanks to Professor Yang Yafei for his guidance, the project was successfully implemented with his support.

特别感谢杨亚飞老师指导，项目在杨老师支持下成功实现。

## Directory Structure
## 目录结构

```
stellarium_catalog/
├── cat/                     # .cat format parsing module / .cat 格式解析模块
│   ├── cat_function.py      # Core parsing library / 核心解析库
│   ├── deal_cat.py          # Original parsing script (reference) / 原始解析脚本（参考）
│   ├── stars_0_0v0_20.cat   # Sample catalog file / 示例星表文件
│   └── README.md            # Module documentation / 模块说明文档
├── eph/                     # .eph format processing module / .eph 格式处理模块
│   ├── eph_function.py      # Core writing library / 核心写入库
│   ├── read_eph.py          # .eph file reading and checking tool / .eph文件读取检查工具
│   ├── write_eph.py         # Original writing script (reference) / 原始写入脚本（参考）
│   └── README.md            # Module documentation / 模块说明文档
├── cat2eph.py               # Main conversion script (batch processing) / 主转换脚本（批量处理）
├── check_eph_plot.py        # Conversion result checking and visualization tool / 转换结果检查和可视化工具
└── README.md                # Project documentation (this file) / 项目总说明（本文件）
```

## Core Features
## 核心功能

✅ **Full Format Support**: Fully compatible with Stellarium .cat v0/.cat v1 and .eph v2 official format specifications  
✅ **完整格式支持**：完全兼容 Stellarium .cat v0/.cat v1 和 .eph v2 官方格式规范  

✅ **HEALPix Partitioning**: Automatically generates standard `Norder{a}/Dir{b}/Npix{c}.eph` directory structure  
✅ **HEALPix 分区**：自动生成标准 `Norder{a}/Dir{b}/Npix{c}.eph` 目录结构  

✅ **Efficient Compression Optimization**: Byte rearrangement + zlib maximum compression, file size reduced by more than 40%  
✅ **高效压缩优化**：字节重排 + zlib 最高压缩，文件体积减少 40% 以上  

✅ **Intelligent Automatic Mapping**: Automatically recognizes stars_x.cat corresponding to Norderx level, no manual configuration required  
✅ **智能自动映射**：自动识别 stars_x.cat 对应 Norderx 层级，无需手动配置  

✅ **Professional Astronomy Library Support**: Priority use of healpy library for high-precision HEALPix partitioning, automatic fallback to alternative algorithm  
✅ **专业天文库支持**：优先使用 healpy 库进行高精度 HEALPix 分区，自动降级备用算法  

✅ **Resumable Transfer**: Automatically saves conversion progress, can continue processing unfinished files after interruption  
✅ **断点续传**：自动保存转换进度，中断后可继续处理未完成文件  

✅ **Data Validation**: Built-in format check and data validity check to ensure correct conversion results  
✅ **数据验证**：内置格式校验和数据有效性检查，确保转换结果正确  

✅ **Visual Verification**: Built-in plotting tool, can directly generate celestial sphere distribution maps and statistical charts  
✅ **可视化验证**：内置绘图工具，可直接生成天球分布图和统计图表  

## Quick Start
## 快速开始

### Environment Requirements
### 环境要求

- Python 3.8+
- Dependencies: `numpy`, `matplotlib`, `zlib`
- Optional: `healpy` (recommended for high-precision HEALPix partitioning)
- 可选：`healpy`（推荐，用于高精度HEALPix分区）

### Install Dependencies
### 安装依赖

```bash
pip install numpy matplotlib
# Optional (recommended): Install healpy for more accurate partitioning results
# 可选（推荐）：安装healpy获得更精确的分区结果
pip install healpy
```

### Quick Usage
### 快速使用

#### 1. Batch convert all .cat files
#### 1. 批量转换所有 .cat 文件

```bash
# Use default settings (input current directory, output to ./output_eph)
# 使用默认设置（输入当前目录，输出到./output_eph）
python cat2eph.py

# Specify input and output directories
# 指定输入输出目录
python cat2eph.py --input ./cat --output ./my_eph_output

# Reset progress and re-convert all files
# 重置进度，重新转换所有文件
python cat2eph.py --reset
```

#### 2. Check conversion results
#### 2. 检查转换结果

```bash
# Read the converted .eph files and draw the celestial sphere distribution map
# 读取转换后的.eph文件并绘制天球分布图
python check_eph_plot.py --input ./output_eph

# View the contents of a single .eph file
# 查看单个.eph文件内容
python eph/read_eph.py ./output_eph/Norder0/Dir0/Npix0.eph
```

## Module Description
## 模块说明

### 1. `.cat` Parsing Module (`/cat/`)
### 1. `.cat` 解析模块 (`/cat/`)

- **Core File**: `cat_function.py`
- **核心文件**：`cat_function.py`
- **Function**: Parse Stellarium binary .cat catalog files
- **功能**：解析 Stellarium 二进制 .cat 星表文件
- **Supported Formats**: Data type 0 (48 bytes/record) and data type 1 (32 bytes/record)
- **支持格式**：数据类型0（48字节/记录）和数据类型1（32字节/记录）
- **Extracted Fields**: Complete astronomical parameters such as object ID, coordinates (RA/Dec), magnitude, proper motion, parallax, color index, spectral type, etc.
- **提取字段**：天体ID、坐标（RA/Dec）、星等、自行、视差、色指数、光谱类型等完整天文参数
- **Advanced Features**: Data validation, batch processing, statistical information generation
- **高级功能**：数据验证、批量处理、统计信息生成

### 2. `.eph` Processing Module (`/eph/`)
### 2. `.eph` 处理模块 (`/eph/`)

- **Core File**: `eph_function.py`
- **核心文件**：`eph_function.py`
- **Function**: Generate .eph files conforming to Stellarium Web Engine specifications
- **功能**：生成符合 Stellarium Web Engine 规范的 .eph 文件
- **Features**: Automatic byte rearrangement to optimize compression rate, HEALPix partition management, file integrity verification
- **特性**：自动字节重排优化压缩率，HEALPix分区管理，文件完整性校验
- **Supporting Tool**: `read_eph.py` for reading and checking .eph file structure
- **配套工具**：`read_eph.py` 用于读取和检查 .eph 文件结构

### 3. Main Conversion Script (`cat2eph.py`)
### 3. 主转换脚本 (`cat2eph.py`)

- **Automatic Mapping**: `stars_0.cat` → `Norder0`, `stars_1.cat` → `Norder1`, automatic correspondence
- **自动映射**：`stars_0.cat` → `Norder0`，`stars_1.cat` → `Norder1`，自动对应
- **Partition Algorithm**: Priority use of healpy professional astronomy library, automatic use of alternative algorithm when no dependency
- **分区算法**：优先使用 healpy 专业天文库，无依赖时自动使用备用算法
- **Resumable Transfer**: Automatically saves conversion progress to avoid duplicate processing
- **断点续传**：自动保存转换进度，避免重复处理
- **Statistics**: Real-time display of conversion progress, number of stars, file generation status
- **统计信息**：实时显示转换进度、恒星数量、文件生成情况

### 4. Result Checking Tool (`check_eph_plot.py`)
### 4. 结果检查工具 (`check_eph_plot.py`)

- **Function**: Batch read all .eph files under Norder0, extract stellar data
- **功能**：批量读取 Norder0 下所有 .eph 文件，提取恒星数据
- **Visualization**: Generate celestial sphere distribution scatter plot, apparent magnitude distribution histogram, celestial sphere density heat map
- **可视化**：生成天球分布散点图、视星等分布直方图、天球密度热图
- **Chinese Support**: Configured Chinese fonts, Chinese characters in charts are displayed normally
- **中文支持**：已配置中文字体，图表中文正常显示
- **Statistical Output**: Automatically calculate total number of stars, magnitude range, average value and other information
- **统计输出**：自动计算恒星总数、星等范围、平均值等信息

## Conversion Process
## 转换流程

### Automatic Mapping Rules
### 自动映射规则

| Input Filename | Output Level | Number of Partitions | Description / 说明 |
|-----------|----------|----------|------|
| stars_0_*.cat | Norder0 | 12 .eph files / 12个.eph文件 | Brightest stars (brighter than 6 mag) / 最亮恒星（亮于6等） |
| stars_1_*.cat | Norder1 | 48 .eph files / 48个.eph文件 | Bright stars / 次亮恒星 |
| stars_2_*.cat | Norder2 | 192 .eph files / 192个.eph文件 | Fainter stars / 更暗恒星 |
| stars_3_*.cat | Norder3 | 768 .eph files / 768个.eph文件 | Faintest stars / 最暗恒星 |

### Conversion Steps
### 转换过程

1. **Scan input directory**: Automatically discover all `stars_*.cat` files
   **扫描输入目录**：自动发现所有 `stars_*.cat` 文件
2. **Parse .cat files**: Read binary catalog and extract all astronomical parameters
   **解析 .cat 文件**：读取二进制星表，提取所有天体参数
3. **HEALPix partitioning**: Assign to corresponding pixels according to object coordinates
   **HEALPix 分区**：根据天体坐标分配到对应像素
4. **Generate .eph files**: Write to standard format files by partition, automatic compression optimization
   **生成 .eph 文件**：按分区写入标准格式文件，自动压缩优化
5. **Verify file integrity**: Check if the generated file format conforms to specifications
   **验证文件完整性**：检查生成的文件格式是否符合规范
6. **Save progress**: Record completed files, support resumable transfer
   **保存进度**：记录已完成文件，支持断点续传

## Usage Examples
## 使用示例

### Complete Conversion Process
### 完整转换流程

```bash
# 1. Convert all catalog files
# 1. 转换所有星表文件
python cat2eph.py --input ./cat --output ./stellarium_eph

# 2. Check conversion results
# 2. 检查转换结果
python check_eph_plot.py --input ./stellarium_eph

# 3. View generated images
# 3. 查看生成的图片
# - sky_distribution.png: Celestial sphere star distribution map / 天球恒星分布图
# - statistics.png: Statistical charts / 统计图表
```

### Use as a Library
### 作为库使用

```python
# Parse .cat file
# 解析.cat文件
from cat.cat_function import StellariumCatParser
parser = StellariumCatParser("./cat/stars_0_0v0_20.cat")
stars = parser.parse()

# Convert and write .eph file
# 转换并写入.eph文件
from eph.eph_function import write_eph_for_healpix
success, msg = write_eph_for_healpix(
    output_dir="./output",
    order=0,
    pix=0,
    stars=stars[:1000]  # Write first 1000 stars to Npix0.eph / 写入前1000颗星到Npix0.eph
)
print(msg)
```

## Format Description
## 格式说明

### .cat Format (Stellarium Desktop Version)
### .cat 格式（Stellarium 桌面版）

- Binary format, divided into file header and star data parts
  二进制格式，分文件头和星数据两部分
- Supports two data types: 48 bytes/record (complete parameters) and 32 bytes/record (simplified parameters)
  支持两种数据类型：48字节/记录（完整参数）和32字节/记录（精简参数）
- Coordinate unit: Degrees (°)
  坐标单位：角度（度）

### .eph Format (Stellarium Web Engine)
### .eph 格式（Stellarium Web Engine）

- Chunk structure: `EPHE` identifier + version number + multiple Chunk blocks
  分块结构：`EPHE`标识 + 版本号 + 多个Chunk块
- Supported Chunk types: JSON (metadata), STAR (stellar data), COMP (compressed block), etc.
  支持Chunk类型：JSON（元数据）、STAR（恒星数据）、COMP（压缩块）等
- Coordinate unit: Radians
  坐标单位：弧度
- Built-in zlib compression and byte rearrangement optimization, small file size
  内置zlib压缩和字节重排优化，文件体积小

## Key Fix Notes
## 关键修复说明

1. **Magnitude parsing bug**: Fixed the numerical anomaly caused by using unsigned int to read negative magnitudes, changed to signed int
   **星等解析bug**：修复了使用unsigned int读取负星等导致的数值异常问题，改为signed int
2. **Column name matching problem**: Fixed the problem that column name trailing spaces could not be matched when reading .eph files
   **列名匹配问题**：修复了.eph文件读取时列名尾部空格导致无法匹配的问题
3. **Coordinate unit conversion**: Automatically handle degree → radian unit conversion to ensure correct format
   **坐标单位转换**：自动处理角度→弧度单位转换，确保格式正确

## Performance Reference
## 性能参考

- Parsing 100,000 stars: < 1 second
  解析10万颗恒星：< 1秒
- Converting 100,000 stars: < 2 seconds
  转换10万颗恒星：< 2秒
- Generated file compression rate: ~60% (raw data → .eph file)
  生成文件压缩率：约60%（原始数据→.eph文件）
- Memory usage: < 100MB (processing 1 million stars)
  内存占用：< 100MB（处理100万颗恒星）

## Output Directory Structure
## 输出目录结构

```
output_eph/
├── Norder0/
│   └── Dir0/
│       ├── Npix0.eph
│       ├── Npix1.eph
│       ├── ...
│       └── Npix11.eph  # Total 12 files / 共12个文件
├── Norder1/
│   └── Dir0/
│       └── ...         # Total 48 files / 共48个文件
├── Norder2/
│   └── Dir0/
│       └── ...         # Total 192 files / 共192个文件
└── conversion_progress.json  # Conversion progress file / 转换进度文件
```

## References
## 参考文档

- `/cat/README.md` - Detailed description of .cat parsing module / .cat 解析模块详细说明
- `/eph/README.md` - Detailed description of .eph processing module / .eph 处理模块详细说明
- `/eph/README_EPH_zh.md` - Chinese description of .eph official format / .eph 官方格式中文说明

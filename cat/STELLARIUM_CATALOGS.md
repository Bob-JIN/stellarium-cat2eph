# Stellarium 星表数据详解

## 概述

**Stellarium** 是一款功能强大的开源天文软件，能够渲染逼真的3D星空。其星表数据位于 `stars/` 目录下，采用 **Hipparcos + Gaia DR3** 组合星表，提供高精度的天体位置、光度和颜色数据。

---

## 星表目录结构

```
Stellarium/
└── stars/
    └── hip_gaia3/
        ├── defaultStarsConfig.json    # 星表配置文件（核心）
        ├── stars_0_0v0_20.cat         # 星等 -2.00 ~ 6.00（约5,000颗）
        ├── stars_1_0v0_16.cat         # 星等 6.00 ~ 7.50（约22,000颗）
        ├── stars_2_0v0_17.cat         # 星等 7.50 ~ 9.00（约140,000颗）
        ├── stars_3_0v0_10.cat         # 星等 9.00 ~ 10.50（约420,000颗）
        ├── stars_4_1v0_6.cat          # 星等 10.50 ~ 12.00（约170万颗，需下载）
        ├── stars_5_1v0_6.cat          # 星等 12.00 ~ 13.75（约800万颗，需下载）
        ├── stars_6_1v0_4.cat          # 星等 13.75 ~ 15.50（约2980万颗，需下载）
        ├── stars_7_1v0_4.cat          # 星等 15.50 ~ 16.75（约5750万颗，需下载）
        ├── stars_8_2v0_3.cat          # 星等 16.75 ~ 18.00（约1.23亿颗，需下载）
        ├── stars_hip_sp_0v0_6.cat     # Hipparcos 光谱类型
        ├── object_types_v0_1.cat      # 天体类型分类
        ├── name.fab                   # 恒星命名（拜耳/弗兰斯蒂德）
        ├── extra_name.fab             # 扩展恒星名称
        ├── gcvs.cat                   # 变星总表（GCVS）
        ├── cross-id.cat               # 星表交叉索引
        ├── binary_orbitparam.dat      # 双星轨道参数
        └── wds_hip_part.dat           # 双星目录数据
```

---

## 星表数据内容详解

### 1. 核心星表文件 (*.cat)

主星表文件采用**紧凑的二进制格式**存储，包含以下关键数据：

| 数据类型 | 说明 | 用途 |
|---------|------|------|
| **位置坐标** | ICRS赤经(RA) / 赤纬(Dec) | 天球上的精确位置定位 |
| **自行 (Proper Motion)** | μ_RA / μ_Dec (mas/yr) | 恒星在天球上的切向运动 |
| **视差 (Parallax)** | π (mas) | 用于计算距离（d = 1000/π 秒差距） |
| **视星等 (Magnitude)** | V波段 / G波段 | **光通量**的对数量度，值越小越亮 |
| **光谱类型 (Spectral Type)** | O/B/A/F/G/K/M/L/T | 决定恒星**表面温度和颜色** |
| **有效温度 (Teff)** | 开尔文(K) | 恒星表面有效温度 |
| **B-V 色指数** | 颜色指标 | 恒星颜色的量化指标 |

### 2. 光通量与星等

**星等**是光通量的对数表示：
```
m = -2.5 * log10(F / F0)
```
- `F` 是接收到的光通量
- `F0` 是零等星的参考通量
- 每相差5个星等，亮度差100倍

| 星等范围 | 恒星数量 | 可见性 |
|---------|---------|--------|
| -2 ~ +6 | ~5,000 | 肉眼可见 |
| +6 ~ +7.5 | ~22,000 | 双筒望远镜可见 |
| +7.5 ~ +9 | ~140,000 | 小型望远镜可见 |
| +9 ~ +10.5 | ~420,000 | 中等望远镜可见 |
| +10.5 ~ +18 | ~2亿颗 | 大型望远镜/专业设备 |

### 3. 光谱类型与恒星颜色

光谱类型直接决定恒星在软件中的渲染颜色：

| 光谱型 | 有效温度 | 颜色 | 代表星 |
|-------|---------|------|--------|
| **O** | 30,000-50,000K | 蓝色 | 参宿增一 |
| **B** | 10,000-30,000K | 蓝白色 | 猎户座β |
| **A** | 7,500-10,000K | 白色 | 天狼星A |
| **F** | 6,000-7,500K | 黄白色 | 南河三 |
| **G** | 5,000-6,000K | 黄色 | 太阳 |
| **K** | 3,500-5,000K | 橙黄色 | 大角星 |
| **M** | 2,500-3,500K | 红色 | 参宿四 |

### 4. 天体类型分类 (object_types_v0_1.cat)

该文件定义了约200种天体类型代码，包括：

**恒星类型：**
- `**` / `SB*` - 双星/分光双星
- `WR*` - 沃尔夫-拉叶星
- `RG*` / `RC*` - 红巨星/红团簇星
- `Be*` - Be发射线星
- `HB*` - 水平分支星
- `WD*` - 白矮星
- `V*` - 变星（通用）
- `RR*` - RR天琴座变星
- `C*` - 碳星

**特殊天体：**
- `Psr` - 脉冲星
- `BH` - 黑洞候选体
- `SNR` - 超新星遗迹
- `QSO` - 类星体
- `AGN` - 活动星系核
- `ULX` - 极亮X射线源

**星团与星云：**
- `OpC` - 疏散星团
- `GlC` - 球状星团
- `HII` - HII电离氢区
- `PN` - 行星状星云
- `ClG` - 星系团

---

## 辅助数据文件

### name.fab - 恒星命名文件

格式：`星表ID | 拜耳命名/弗兰斯蒂德编号`

```text
# 示例（仙女座）
    677|α_And      # 仙女座α（壁宿二）
   5447|β_And      # 仙女座β（奎宿九）
  3092|δ_And      # 仙女座δ
```

包含：
- 拜耳命名（希腊字母 + 星座）
- 弗兰斯蒂德编号（数字 + 星座）
- 变星命名
- 专有名称（如 Sirius, Betelgeuse）

### binary_orbitparam.dat - 双星轨道参数

```text
# 格式示例：
# primary_hip  secondary_hip  period  ecc  inc  omega  Omega  T0  a  distance  epoch  ra  dec  rv  pmra  pmdec  mass1  mass2
71683  71681  29133.07  0.519  1.38  3.58  4.04  2435314.75  17.49  1.33  2458667.38  3.84  -1.06  -22.39  -3639.95  700.4  1.08  0.91
```

**数据字段：**
- `period` - 轨道周期（天）
- `eccentricity` - 轨道偏心率
- `inclination` - 轨道倾角（弧度）
- `big_omega` - 升交点黄经
- `small_omega` - 近星点角距
- `periastron_epoch` - 过近星点时刻
- `semi_major` - 半长轴（毫角秒）
- `primary_mass/secondary_mass` - 主/伴星质量（太阳质量）

### gcvs.cat - 变星总表 (General Catalog of Variable Stars)

包含约5万颗变星的信息：
- 变星类型（造父变星、米拉变星、耀星等）
- 光变周期
- 极大/极小星等
- 光谱类型变化

---

## 星表配置文件详解 (defaultStarsConfig.json)

```json
{
  "version": 26,
  "hipSpectralFile": "stars_hip_sp_0v0_6.cat",
  "objecttypesFile": "object_types_v0_1.cat",
  "catalogs": [
    {
      "id": "stars0",
      "fileName": "stars_0_0v0_20.cat",
      "count": 0.005,           // 单位：百万颗
      "magRange": [-2.00, 6.00], // 星等范围
      "sizeMb": 0.2,            // 文件大小
      "checksum": "...",        // MD5校验
      "checked": true           // 是否已安装
    },
    // ... 更多星表级别
  ]
}
```

**命名规则：**
`stars_X_YvZ_N.cat`
- X - 星表级别（0=最亮）
- Y - 数据格式版本
- Z - 子版本
- N - 内容版本迭代次数

---

## 星表数据来源

| 数据来源 | 提供内容 | 精度 |
|---------|---------|------|
| **Hipparcos** | 位置、视差、自行、星等 | ~1 mas |
| **Gaia DR3** | 高精度位置、自行、光谱 | ~10 μas |
| **Tycho-2** | 测光数据 | ~0.01 mag |
| **2MASS** | 近红外测光 (J/H/Ks) | ~0.02 mag |
| **SIMBAD** | 天体交叉识别、类型 | - |
| **GCVS** | 变星数据 | - |
| **WDS** | 双星/聚星数据 | - |

---

## 扩展星表下载

默认安装只包含最亮的4个星表文件（约60万颗星）。完整星表需额外下载：

| 星表ID | 星等范围 | 恒星数量 | 大小 | 下载链接 |
|--------|---------|---------|------|---------|
| stars4 | 10.50-12.00 | ~1.7M | 53MB | SourceForge |
| stars5 | 12.00-13.75 | ~8.0M | 245MB | SourceForge |
| stars6 | 13.75-15.50 | ~29.8M | 912MB | SourceForge |
| stars7 | 15.50-16.75 | ~57.5M | 1.7GB | SourceForge |
| stars8 | 16.75-18.00 | ~122.9M | 1.8GB | SourceForge |

**完整星表总计：**
- 约 **2.1亿颗** 恒星
- 总数据量：约 **4.8 GB**

---

## 渲染管线

Stellarium 渲染恒星时使用以下数据流：

```
星表数据 (.cat)
    ↓
位置 (RA/Dec) + 自行 → 当前天球位置
    ↓
视差/距离 → 3D空间位置
    ↓
星等 + 光谱型 → 光度/颜色
    ↓
GLSL Shader → 屏幕像素渲染
    ↓
    (planet.frag / planet.vert)
```

**关键着色器：**
- `data/shaders/planet.vert` - 顶点着色器（位置变换）
- `data/shaders/planet.frag` - 片段着色器（颜色渲染）

---

## 进阶：星表二进制格式

`.cat` 文件采用紧凑的二进制存储以节省空间和提高加载速度。典型记录结构（未压缩）：

```c
struct Star {
    int64_t  hip_id;          // Hipparcos ID 或 Gaia Source ID
    double   ra;              // 赤经 (弧度)
    double   dec;             // 赤纬 (弧度)
    float    plx;             // 视差 (mas)
    float    pm_ra;           // 赤经自行 (mas/yr)
    float    pm_dec;          // 赤纬自行 (mas/yr)
    float    mag_v;           // V波段视星等
    float    mag_bv;          // B-V色指数
    float    teff;            // 有效温度 (K)
    uint16_t spectral_type;   // 光谱类型编码
    uint16_t flags;           // 标志位（变星/双星等）
};
```

实际文件使用 **zlib 压缩** 和 **量化编码** 进一步压缩。

---

## 相关资源

- [Stellarium 官网](https://stellarium.org)
- [GitHub 仓库](https://github.com/Stellarium/stellarium)
- [额外星表下载](https://sourceforge.net/projects/stellarium/files/Extra-data-files/)
- [用户指南](https://github.com/Stellarium/stellarium/releases)

---

## 许可证

Stellarium 星表数据：
- Hipparcos/Tycho: ESA (公共使用)
- Gaia DR3: ESA/Gaia DPAC (CC BY-SA 3.0)
- 其他: 各自原始来源许可

Stellarium 软件: **GPL v2**

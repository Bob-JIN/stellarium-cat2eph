# Stellarium .cat Catalog File Format Specification

This directory contains tools for parsing Stellarium .cat format catalog files.

## File Structure

```
.
├── deal_cat.py           # Correct Parser
├── dump_binary.py        # Binary Data Dump Tool
├── hip_gaia3/            # .cat Catalog File Directory
│   ├── stars_0_0v0_20.cat
│   ├── stars_1_0v0_16.cat
│   └── ...
└── README_CAT.md         # This Document
```

## .cat File Data Format

### 1. File Header Structure

| Offset | Size | Type | Description |
|--------|------|------|-------------|
| 0 | 4 bytes | char[4] | Magic Number: `0x0a045f83` |
| 4 | 4 bytes | uint32 | Data Type (0 or 1) |
| 8 | 4 bytes | uint32 | Major Version |
| 12 | 4 bytes | uint32 | Minor Version |
| 16 | 4 bytes | uint32 | Level |
| 20 | 4 bytes | uint32 | Minimum Magnitude × 1000 |
| 24 | 4 bytes | float32 | Epoch (JD, 2457389.0 = J2016.0) |
| 28 | 4 × N bytes | uint32[N] | Number of stars per region, N = 20×4^level + 1 |

### 2. Data Record Format

#### Data Type 0 (48 bytes/record) - Suitable for level 0-3

**Format String**: `<qiiiiiihhHHhHB3s`

| Field | Type | Size | Description | Conversion Formula |
|-------|------|------|-------------|--------------------|
| source_id | int64 | 8 bytes | Gaia Source ID | - |
| x0 | int32 | 4 bytes | Cartesian coordinate X | × 2e-9 |
| x1 | int32 | 4 bytes | Cartesian coordinate Y | × 2e-9 |
| x2 | int32 | 4 bytes | Cartesian coordinate Z | × 2e-9 |
| dx0 | int32 | 4 bytes | Proper motion X | × 1e-3 |
| dx1 | int32 | 4 bytes | Proper motion Y | × 1e-3 |
| dx2 | int32 | 4 bytes | Proper motion Z | × 1e-3 |
| b_v | int16 | 2 bytes | B-V color index | / 1000.0 |
| vmag | int16 | 2 bytes | V apparent magnitude | / 1000.0 |
| parallax | uint16 | 2 bytes | Parallax (mas) | / 50.0 |
| parallax_err | uint16 | 2 bytes | Parallax error (mas) | / 100.0 |
| radial_velocity | int16 | 2 bytes | Radial velocity (km/s) | / 10.0 |
| sp_type_idx | uint8 | 1 byte | Spectral type index | - |
| otype_idx | uint8 | 1 byte | Object type index | - |
| hip_component | uint8[3] | 3 bytes | HIP ID + component number | - |

**Cartesian coordinates to RA/Dec conversion**:
```python
r = sqrt(x0² + x1² + x2²)
dec = degrees(arcsin(x2 / r))
ra = degrees(arctan2(x1, x0))
if ra < 0: ra += 360
```

#### Data Type 1 (32 bytes/record) - Suitable for level 4-6

**Format String**: `<qiiiihhHH`

| Field | Type | Size | Description | Conversion Formula |
|-------|------|------|-------------|--------------------|
| source_id | int64 | 8 bytes | Gaia Source ID | - |
| ra | int32 | 4 bytes | Right ascension (degrees) | / 3,600,000.0 |
| dec | int32 | 4 bytes | Declination (degrees) | / 3,600,000.0 |
| pmra | int32 | 4 bytes | Proper motion in right ascension (mas/yr) | / 1000.0 |
| pmdec | int32 | 4 bytes | Proper motion in declination (mas/yr) | / 1000.0 |
| b_v | int16 | 2 bytes | B-V color index | / 1000.0 |
| vmag | int16 | 2 bytes | V apparent magnitude | / 1000.0 |
| parallax | uint16 | 2 bytes | Parallax (mas) | / 100.0 |
| parallax_err | uint16 | 2 bytes | Parallax error (mas) | / 100.0 |

## Using deal_cat_fixed.py

### Basic Usage

```python
from deal_cat_fixed import StellariumCatParser

# Initialize parser
parser = StellariumCatParser("./hip_gaia3/stars_0_0v0_20.cat")

# Parse file
stars = parser.parse()

# Output statistics
parser.basic_stats()

# Plot Hertzsprung-Russell diagram
parser.plot_hr_diagram(top_n=10000)

# Plot sky distribution map
parser.plot_sky_distribution()
```

### Command Line Execution

```bash
python3 deal_cat_fixed.py
```

### Accessing Parsed Data

Each star's data is stored as a dictionary, containing the following fields:

**Data Type 0**:
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

**Data Type 1**:
```python
{
    "source_id": int64,
    "ra_deg": float, "dec_deg": float,
    "pmra": float, "pmdec": float,
    "b_v": float, "vmag": float,
    "parallax": float, "parallax_err": float
}
```

### Example: Convert to .eph File

```python
from deal_cat_fixed import StellariumCatParser

parser = StellariumCatParser("./hip_gaia3/stars_0_0v0_20.cat")
stars = parser.parse()

# Write to .eph file
with open("output.eph", "w") as f:
    for star in stars:
        line = f"{star['source_id']} {star['ra_deg']:.6f} {star['dec_deg']:.6f} {star['vmag']:.3f}\n"
        f.write(line)
```

## Catalog File Naming Convention

Filename format: `stars_{level}_{datatype}v{majver}_{minver}.cat`

Examples:
- `stars_0_0v0_20.cat` - level 0, datatype 0, version 0.20
- `stars_1_0v0_16.cat` - level 1, datatype 0, version 0.16
- `stars_4_1v0_6.cat` - level 4, datatype 1, version 0.6

## File Header Reading Example

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

## Auxiliary Tools

### dump_binary.py

Dump the binary content of a .cat file to text format for analyzing data structures.

```bash
python3 dump_binary.py
```

Output file: `binary_data_dump.txt`

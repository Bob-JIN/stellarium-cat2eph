# EPH Binary Catalog File Format Specification

## Overview
EPH (EPHEmeris) is a binary catalog file format used by the Stellarium Web Engine for efficient storage and transmission of astronomical data such as stars and deep sky objects. The format is designed to be compact, compression-friendly, and optimized for fast reading and rendering.

## Overall File Structure
| Offset | Length | Type | Description |
|--------|--------|------|-------------|
| 0 | 4 bytes | ASCII | File magic identifier, fixed as "EPHE" |
| 4 | 4 bytes | Little-endian uint32 | File version, currently 2 |
| 8 | Variable | - | List of Chunks, the file is composed of a series of Chunks |

## Chunk Structure
Each Chunk follows this format:
| Offset | Length | Type | Description |
|--------|--------|------|-------------|
| 0 | 4 bytes | ASCII | Chunk type, padded with spaces if less than 4 characters |
| 4 | 4 bytes | Little-endian uint32 | Chunk data length (len) |
| 8 | len bytes | - | Actual Chunk data |
| 8 + len | 4 bytes | Little-endian uint32 | CRC32 checksum (currently filled with 0 in this implementation) |

### Common Chunk Types
1. **JSON** - Metadata storage
   - Content: UTF-8 encoded JSON string storing file generation information, version, and other metadata
   - Example: `{"generator":"python", "version":"1.0"}`

2. **STAR** - Star data block
   - Contains star tile header and table data
   - See detailed structure below

3. **DSO** - Deep Sky Object data block
   - Format similar to STAR, stores data for deep sky objects (galaxies, nebulae, etc.)

4. **COMP** - Compressed data block
   - Stores zlib-compressed data of other Chunk types
   - Structure: 4 bytes uncompressed size + 4 bytes compressed size + compressed data

5. **TABLE** - Generic table data block
   - Stores structured table data, can be compressed or directly included in STAR/DSO blocks

## STAR Chunk Detailed Structure
STAR Chunk is the most commonly used block type for storing star data:
| Offset | Length | Type | Description |
|--------|--------|------|-------------|
| 0 | 4 bytes | Little-endian uint32 | Tile version, currently 3 |
| 4 | 8 bytes | Little-endian uint64 | nuniq, HEALPix hierarchical pixel encoding |
| 12 | Variable | - | TABLE data block |

### TABLE Data Block Structure
TABLE block contains structured tabular data:
| Offset | Length | Type | Description |
|--------|--------|------|-------------|
| 0 | 4 bytes | Little-endian uint32 | Flags |
| | | | - Bit 0: 1 = data is shuffled (column-wise reordered), 0 = original order |
| 4 | 4 bytes | Little-endian uint32 | Row size in bytes |
| 8 | 4 bytes | Little-endian uint32 | Number of columns |
| 12 | 4 bytes | Little-endian uint32 | Number of rows |
| 16 | columns × 20 bytes | - | Column descriptors, 20 bytes per column |
| 16 + columns×20 | Variable | - | Table data (raw or compressed block) |

### Column Descriptor Structure
Each column descriptor occupies 20 bytes:
| Offset | Length | Type | Description |
|--------|--------|------|-------------|
| 0 | 4 bytes | ASCII | Column name, padded with NULL bytes if less than 4 characters |
| 4 | 4 bytes | - | Type field, first byte is type identifier: |
| | | | - 'f': float (single precision) |
| | | | - 'i': uint32 (unsigned integer) |
| | | | - 'Q': uint64 (64-bit unsigned integer) |
| | | | - 's': string |
| 8 | 4 bytes | Little-endian uint32 | Unit identifier |
| 12 | 4 bytes | Little-endian uint32 | Start offset of column data within each row |
| 16 | 4 bytes | Little-endian uint32 | Byte size of column data |

### Compressed Block Structure
If TABLE data is compressed (which is usually the case), the data section has this structure:
| Offset | Length | Type | Description |
|--------|--------|------|-------------|
| 0 | 4 bytes | Little-endian uint32 | Uncompressed data size |
| 4 | 4 bytes | Little-endian uint32 | Compressed data size |
| 8 | compressed_size bytes | - | zlib-compressed data |

## Data Optimization Techniques
1. **Byte Shuffling**
   - To improve compression ratio, data is reordered column-wise
   - Original row-wise storage: [row1col1, row1col2, ..., row1colN, row2col1, ...]
   - Shuffled column-wise storage: [row1col1, row2col1, ..., rowNcol1, row1col2, ...]
   - Reverse shuffle is required during reading to restore original order

2. **zlib Compression**
   - Shuffled data is compressed using zlib to further reduce file size
   - Highest compression level (level=9) is typically used

## Standard Star Data Columns
Standard star data contains 10 columns with a total row size of 292 bytes:
| Column | Type | Unit | Offset | Size | Description |
|--------|------|------|--------|------|-------------|
| hip | i | 0 | 0 | 4 | Hipparcos catalog ID |
| hd | i | 0 | 4 | 4 | Henry Draper catalog ID |
| vmag | f | 196608 | 8 | 4 | Visual magnitude |
| ra | f | 65536 | 12 | 4 | Right Ascension (radians) |
| de | f | 65536 | 16 | 4 | Declination (radians) |
| plx | f | 65543 | 20 | 4 | Parallax |
| pra | f | 393216 | 24 | 4 | Proper motion in Right Ascension |
| pde | f | 393216 | 28 | 4 | Proper motion in Declination |
| bv | f | 0 | 32 | 4 | B-V color index |
| ids | s | 0 | 36 | 256 | Object name/identifier string |

## Tools
- `read_eph.py`: EPH file parsing and inspection tool
  ```bash
  python read_eph.py <filename.eph>
  ```

- `write_eph.py`: EPH file generation tool
  ```bash
  python write_eph.py <input.txt> <output.eph>
  ```

- `generate_test_data.py`: Test data generation tool
  ```bash
  python generate_test_data.py
  ```

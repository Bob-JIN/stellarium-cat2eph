import struct
import zlib
import os


FILE_VERSION = 2


def shuffle_bytes(data, n_row, row_size):
    buf = bytearray(data)
    result = bytearray(len(data))
    for j in range(row_size):
        for i in range(n_row):
            result[j * n_row + i] = buf[i * row_size + j]
    return bytes(result)


class EPHFileWriter:
    def __init__(self, file_path):
        self.file_path = file_path
        self.fp = None

    def open_file(self):
        if os.path.exists(self.file_path):
            try:
                os.remove(self.file_path)
            except OSError as e:
                raise IOError(f"无法删除现有文件: {e}")
        self.fp = open(self.file_path, "wb")
        self.fp.write(b"EPHE")
        self.fp.write(struct.pack("<I", FILE_VERSION))

    def write_chunk(self, chunk_type, data):
        if len(chunk_type) > 4:
            raise ValueError("Chunk type too long (max 4 chars)")
        chunk_type_bytes = chunk_type.ljust(4).encode("ascii")
        chunk_len = len(data)
        self.fp.write(chunk_type_bytes)
        self.fp.write(struct.pack("<I", chunk_len))
        self.fp.write(data)
        self.fp.write(struct.pack("<I", 0))

    def write_json_chunk(self, json_str):
        self.write_chunk("JSON", json_str.encode("utf-8"))

    def write_star_chunk(self, stars, order=0, pix=0):
        nuniq = 4 * (1 << (2 * order)) + pix
        tile_data = struct.pack("<IQ", 3, nuniq)
        
        columns = [
            {"name": "hip", "type": "i", "unit": 0, "start": 0, "size": 4},
            {"name": "hd", "type": "i", "unit": 0, "start": 4, "size": 4},
            {"name": "vmag", "type": "f", "unit": 196608, "start": 8, "size": 4},
            {"name": "ra", "type": "f", "unit": 65536, "start": 12, "size": 4},
            {"name": "de", "type": "f", "unit": 65536, "start": 16, "size": 4},
            {"name": "plx", "type": "f", "unit": 65543, "start": 20, "size": 4},
            {"name": "pra", "type": "f", "unit": 393216, "start": 24, "size": 4},
            {"name": "pde", "type": "f", "unit": 393216, "start": 28, "size": 4},
            {"name": "bv", "type": "f", "unit": 0, "start": 32, "size": 4},
            {"name": "ids", "type": "s", "unit": 0, "start": 36, "size": 256},
        ]
        
        row_size = 292
        n_col = 10
        n_row = len(stars)
        flags = 1
        
        table_header = struct.pack("<IIII", flags, row_size, n_col, n_row)
        table_data = table_header
        
        for col in columns:
            name_bytes = col["name"].ljust(4).encode("ascii")
            typ_byte = col["type"].encode("ascii") + b"\x00\x00\x00"
            col_data = name_bytes + typ_byte + struct.pack("<III", col["unit"], col["start"], col["size"])
            table_data += col_data
        
        row_data = b""
        for star in stars:
            row = bytearray(row_size)
            
            struct.pack_into("<I", row, 0, star["hip"])
            struct.pack_into("<I", row, 4, star["hd"])
            struct.pack_into("<f", row, 8, star["vmag"])
            struct.pack_into("<f", row, 12, star["ra"])
            struct.pack_into("<f", row, 16, star["de"])
            struct.pack_into("<f", row, 20, star["plx"])
            struct.pack_into("<f", row, 24, star["pra"])
            struct.pack_into("<f", row, 28, star["pde"])
            struct.pack_into("<f", row, 32, star["bv"])
            
            ids_bytes = star["ids"].encode("ascii", errors="replace")[:255]
            ids_bytes = ids_bytes.ljust(256, b"\x00")
            row[36:36+256] = ids_bytes
            
            row_data += bytes(row)
        
        shuffled_data = shuffle_bytes(row_data, n_row, row_size)
        compressed_data = zlib.compress(shuffled_data, level=9)
        
        comp_header = struct.pack("<II", len(row_data), len(compressed_data))
        table_data += comp_header + compressed_data
        
        self.write_chunk("STAR", tile_data + table_data)

    def close(self):
        if self.fp:
            self.fp.flush()
            self.fp.close()


def read_test_txt(filename):
    stars = []
    current_star = {}
    
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith("hip:"):
                if current_star:
                    stars.append(current_star)
                current_star = {"hip": int(line.split(":", 1)[1].strip())}
            elif line.startswith("hd:"):
                current_star["hd"] = int(line.split(":", 1)[1].strip())
            elif line.startswith("vmag:"):
                current_star["vmag"] = float(line.split(":", 1)[1].strip())
            elif line.startswith("ra:"):
                current_star["ra"] = float(line.split(":", 1)[1].strip())
            elif line.startswith("de:"):
                current_star["de"] = float(line.split(":", 1)[1].strip())
            elif line.startswith("plx:"):
                current_star["plx"] = float(line.split(":", 1)[1].strip())
            elif line.startswith("pra:"):
                current_star["pra"] = float(line.split(":", 1)[1].strip())
            elif line.startswith("pde:"):
                current_star["pde"] = float(line.split(":", 1)[1].strip())
            elif line.startswith("bv:"):
                current_star["bv"] = float(line.split(":", 1)[1].strip())
            elif line.startswith("ids:"):
                current_star["ids"] = line.split(":", 1)[1].strip()
        
        if current_star:
            stars.append(current_star)
    
    return stars


def write_eph_from_txt(input_txt, output_eph):
    try:
        stars = read_test_txt(input_txt)
        print(f"读取到 {len(stars)} 颗恒星数据")
        
        writer = EPHFileWriter(output_eph)
        writer.open_file()
        writer.write_json_chunk('{"generator":"python"}')
        writer.write_star_chunk(stars, order=0, pix=0)
        writer.close()
        
        print(f"成功写入 {output_eph}")
        return True
    except Exception as e:
        print(f"写入失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python write_eph.py <input_txt> <output_eph>")
        sys.exit(1)
    
    input_txt = sys.argv[1]
    output_eph = sys.argv[2]
    success = write_eph_from_txt(input_txt, output_eph)
    sys.exit(0 if success else 1)

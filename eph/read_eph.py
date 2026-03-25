import struct
import zlib
import sys

# 解析 Stellarium Web Engine 的 EPHE (.eph) 二进制文件的简单工具。
# 基于 tianqiu/src/eph-file.c 中的文件格式说明，实现了对常见 chunk
# 类型（JSON, TILE/STAR/DSO, COMP, TABLE）的解析，并打印前 5 条记录
# 以便人工检查。
#
# 主要注意点：
# - 文件以 ASCII magic "EPHE" 开头，紧随 4 字节整型版本号（目前为 2）。
# - 文件由一系列 chunk 组成：4 字节 type, 4 字节 len, len 字节 data, 4 字节 CRC（本脚本不校验 CRC）。
# - TILE/STAR/DSO chunk 含一个 tile header（version + nuniq），随后是表格数据（TABLE）或压缩块（COMP）。
# - TABLE 结构：flags, row_size, n_col, n_row，随后每列 20 字节的列描述，再是数据（可能已经被 shuffle 以优化压缩）。

FILE_VERSION = 2


class EPHFileChecker:
    """EPHE 文件检查器/解析器。

    方法概览：
    - open_file(): 打开文件并验证 magic/version
    - parse_chunks(): 按 chunk 逐个读取并分发解析
    - _parse_chunk(): 根据 chunk 类型选择解析逻辑（TABLE/COMP/STAR 等）
    - _unshuffle_bytes(): 反转 C 端 eph_shuffle_bytes 的字节重排操作
    - _parse_stars(): 解析包含 TILE/STAR 专用头部的表格数据
    - _parse_table(): 通用表格解析并打印前 5 行内容
    """

    def __init__(self, file_path):
        self.file_path = file_path
        self.fp = None

    def open_file(self):
        self.fp = open(self.file_path, "rb")
        magic = self.fp.read(4)
        if magic != b"EPHE":
            raise ValueError(f"Invalid magic: {magic}")
        version = struct.unpack("<I", self.fp.read(4))[0]
        if version != FILE_VERSION:
            raise ValueError(f"Invalid version: {version}")
        print(f"File OK: magic=EPHE, version={version}")

    def parse_chunks(self):
        idx = 0
        while True:
            header = self.fp.read(8)
            if len(header) < 8:
                break
            chunk_type = header[:4].decode("ascii", errors="replace").strip()
            chunk_len  = struct.unpack("<I", header[4:])[0]
            
            chunk_data = self.fp.read(chunk_len)
            chunk_crc  = struct.unpack("<I", self.fp.read(4))[0]
            
            if chunk_type in ("JSON", "TILE", "COMP", "TABLE", "STAR", "DSO"):
                print(f"Chunk {idx}: {chunk_type}, len={chunk_len}, crc={chunk_crc:08X}")
                self._parse_chunk(chunk_type, chunk_data)
            idx += 1

    def _parse_chunk(self, chunk_type, data):
        if   chunk_type == "DSO" or chunk_type == "STAR":
            self._parse_stars(chunk_type, data)
        elif chunk_type == "COMP":
            data_size, comp_size = struct.unpack("<II", data[:8])
            comp_data  = data[8:8+comp_size]
            uncomp     = zlib.decompress(comp_data)
            print(f"  COMP: compressed={comp_size}, uncompressed={data_size}")
            self._parse_chunk("TABLE", uncomp)
        elif chunk_type == "TABLE":
            self._parse_table(data)

    def _unshuffle_bytes(self, data, n_row, row_size):
        # 反向操作：C 中的 eph_shuffle_bytes 将字节按 (i*size + j) -> (j*nb + i)
        # 重排以便压缩。这里给出还原逻辑：把按列存储的缓冲区重新按行恢复。
        buf     = bytearray(data)
        result  = bytearray(len(data))
        for j in range(row_size):
            for i in range(n_row):
                result[i * row_size + j] = buf[j * n_row + i]
        return bytes(result)

    def _parse_stars(self, chunk_type, data):
        # TILE header: 4 字节 version + 8 字节 nuniq（hips 编码）
        version, nuniq = struct.unpack("<IQ", data[:12])
        # C 侧通过 log2(nuniq/4)/2 推导 order，这里使用位操作近似计算相同值
        order = int((nuniq.bit_length() - 1 - 2) // 2)
        pix = nuniq - 4 * (1 << (2 * order))
        print(f"  TILE: version={version}, nuniq={nuniq}, order={order}, pix={pix}")

        # 接下来是 TABLE 头部（flags, row_size, n_col, n_row）
        data_ofs = 12
        flags, row_size, n_col, n_row = struct.unpack("<IIII", data[data_ofs:data_ofs+16])
        print(f"  TABLE: flags={flags}, row_size={row_size}, cols={n_col}, rows={n_row}")

        # 读取每列的描述信息：每列 20 字节（4 名称, 4 类型(先字节是类型字母), 4 单位, 4 start, 4 size）
        col_offset  = data_ofs + 16
        columns     = []
        for i in range(n_col):
            name    = data[col_offset:col_offset+4].decode("ascii", errors="replace").strip("\x00")
            # 类型字段在 C 端是 4 字节，但首字节包含字母类型 ('f','i','Q','s')
            typ     = data[col_offset+4:col_offset+8][:1].decode("ascii", errors="replace")
            unit    = struct.unpack("<I", data[col_offset+ 8:col_offset+12])[0]
            start   = struct.unpack("<I", data[col_offset+12:col_offset+16])[0]
            size    = struct.unpack("<I", data[col_offset+16:col_offset+20])[0]
            columns.append({"name": name, "type": typ, "unit": unit, "start": start, "size": size})
            print(f"    {name}: {typ}, unit={unit}, start={start}, size={size}")
            col_offset += 20

        # 读取压缩块头并解压（data_size, comp_size, comp_data）
        data_size, comp_size = struct.unpack("<II", data[col_offset:col_offset+8])
        comp_data  = data[col_offset+8:col_offset+8+comp_size]
        table_data = zlib.decompress(comp_data)
        print(f"  Block: compressed={comp_size}, uncompressed={data_size}")

        # 如果 flags 的第 0 位被设置，表示数据经过 shuffle（按列重排），需要还原
        if flags & 1:
            print("  Unshuffling data...")
            table_data = self._unshuffle_bytes(table_data, n_row, row_size)
        
        print(f"\n  First 5 objects:")
        for i in range(min(5, n_row)):
            row = table_data[i*row_size:(i+1)*row_size]
            print(f"\n  Object {i+1}:")
            for col in columns:
                val = row[col["start"]:col["start"]+col["size"]]
                if col["type"] == "f" and len(val) >= 4:
                    v = struct.unpack("<f", val[:4])[0]
                    print(f"    {col['name']}: {v}")
                elif col["type"] == "i" and len(val) >= 4:
                    v = struct.unpack("<I", val[:4])[0]
                    print(f"    {col['name']}: {v}")
                elif col["type"] == "Q" and len(val) >= 8:
                    v = struct.unpack("<Q", val[:8])[0]
                    print(f"    {col['name']}: {v}")
                elif col["type"] == "s":
                    v = val.decode("ascii", errors="replace").strip("\x00")
                    if len(v) <= 32:
                        print(f"    {col['name']}: {v}")

    def _parse_table(self, data):
        # 通用 TABLE 解析：读取头部、列定义和实际表格数据
        flags, row_size, n_col, n_row = struct.unpack("<IIII", data[:16])
        print(f"  TABLE: flags={flags}, row_size={row_size}, cols={n_col}, rows={n_row}")

        col_offset = 16
        columns = []
        for i in range(n_col):
            name    = data[col_offset:col_offset+4].decode("ascii", errors="replace").strip("\x00")
            typ     = data[col_offset+4:col_offset+8][:1].decode("ascii", errors="replace")
            unit    = struct.unpack("<I", data[col_offset+8:col_offset+12])[0]
            start   = struct.unpack("<I", data[col_offset+12:col_offset+16])[0]
            size    = struct.unpack("<I", data[col_offset+16:col_offset+20])[0]
            columns.append({"name": name, "type": typ, "unit": unit, "start": start, "size": size})
            print(f"    {name}: {typ}, unit={unit}, start={start}, size={size}")
            col_offset += 20

        table_data = data[col_offset:]

        # 如果表数据经过 shuffle，需要先反转回原始字节顺序
        if flags & 1:
            print("  Unshuffling data...")
            table_data = self._unshuffle_bytes(table_data, n_row, row_size)

        # 打印前 5 条记录以供检查。对不同 type 做合适的 unpack。
        print(f"\n  First 5 objects:")
        for i in range(min(5, n_row)):
            row = table_data[i*row_size:(i+1)*row_size]
            print(f"\n  Object {i+1}:")
            for col in columns:
                val = row[col["start"]:col["start"]+col["size"]]
                if col["type"] == "f" and len(val) >= 4:
                    v = struct.unpack("<f", val[:4])[0]
                    print(f"    {col['name']}: {v}")
                elif col["type"] == "i" and len(val) >= 4:
                    v = struct.unpack("<I", val[:4])[0]
                    print(f"    {col['name']}: {v}")
                elif col["type"] == "Q" and len(val) >= 8:
                    v = struct.unpack("<Q", val[:8])[0]
                    print(f"    {col['name']}: {v}")
                elif col["type"] == "s":
                    v = val.decode("ascii", errors="replace").strip("\x00")
                    if len(v) <= 32:
                        print(f"    {col['name']}: {v}")

    def run(self):
        try:
            self.open_file()
            self.parse_chunks()
            print("\nDone")
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if self.fp:
                self.fp.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python read_eph.py <eph_file>")
        sys.exit(1)
    EPHFileChecker(sys.argv[1]).run()

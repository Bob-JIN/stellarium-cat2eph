import struct
import numpy as np
from pathlib import Path

def extract_binary_data_to_text(cat_file_path, output_txt_path):
    """
    以二进制模式读取.cat文件，将所有数据转换为小端字节序浮点数并保存为.txt文件
    """
    cat_path = Path(cat_file_path)
    output_path = Path(output_txt_path)
    
    if not cat_path.exists():
        raise FileNotFoundError(f"星表文件不存在: {cat_path}")
    
    print(f"读取文件: {cat_path}")
    print(f"文件大小: {cat_path.stat().st_size} 字节")
    
    # 以二进制模式读取整个文件
    with open(cat_path, "rb") as f:
        binary_data = f.read()
    
    total_bytes = len(binary_data)
    print(f"成功读取 {total_bytes} 字节")
    
    # 准备输出文件
    with open(output_path, "w", encoding="utf-8") as out_f:
        out_f.write(f"原始二进制文件: {cat_path.name}\n")
        out_f.write(f"文件大小: {total_bytes} 字节\n")
        out_f.write("="*80 + "\n\n")
        
        # 按4字节(float32)和8字节(float64)分别解析
        out_f.write("===== 按4字节小端float32解析 =====\n")
        num_floats32 = total_bytes // 4
        out_f.write(f"共 {num_floats32} 个float32值\n\n")
        
        for i in range(num_floats32):
            offset = i * 4
            if offset + 4 > total_bytes:
                break
            float_bytes = binary_data[offset:offset+4]
            value = struct.unpack("<f", float_bytes)[0]
            out_f.write(f"[{i:06d}] offset={offset:08d}: 0x{float_bytes.hex()} -> {value:.10g}\n")
        
        out_f.write("\n" + "="*80 + "\n\n")
        
        out_f.write("===== 按8字节小端float64解析 =====\n")
        num_floats64 = total_bytes // 8
        out_f.write(f"共 {num_floats64} 个float64值\n\n")
        
        for i in range(num_floats64):
            offset = i * 8
            if offset + 8 > total_bytes:
                break
            double_bytes = binary_data[offset:offset+8]
            value = struct.unpack("<d", double_bytes)[0]
            out_f.write(f"[{i:06d}] offset={offset:08d}: 0x{double_bytes.hex()} -> {value:.15g}\n")
        
        out_f.write("\n" + "="*80 + "\n\n")
        
        # 同时按原始结构解析前几条记录用于对比
        out_f.write("===== 按原代码结构(IffHBBB)解析前20条记录 =====\n")
        STAR_FORMAT = "<IffHBBB"
        STAR_SIZE = struct.calcsize(STAR_FORMAT)
        num_records = min(20, total_bytes // STAR_SIZE)
        
        for i in range(num_records):
            offset = i * STAR_SIZE
            record_bytes = binary_data[offset:offset+STAR_SIZE]
            unpacked = struct.unpack(STAR_FORMAT, record_bytes)
            out_f.write(f"\n记录{i+1} (offset={offset}):\n")
            out_f.write(f"  原始字节: 0x{record_bytes.hex()}\n")
            out_f.write(f"  HIP: {unpacked[0]}\n")
            out_f.write(f"  RA: {unpacked[1]:.10g}°\n")
            out_f.write(f"  Dec: {unpacked[2]:.10g}°\n")
            out_f.write(f"  Mag: {unpacked[3]/100:.2f}\n")
            out_f.write(f"  B-V: {unpacked[4]/256:.4f}\n")
            out_f.write(f"  SpType: {unpacked[5]}\n")
            out_f.write(f"  VarFlag: {unpacked[6]}\n")
    
    print(f"数据已保存到: {output_path}")
    return output_path

if __name__ == "__main__":
    CAT_FILE = "./hip_gaia3/stars_0_0v0_20.cat"
    OUTPUT_FILE = "./binary_data_dump.txt"
    
    extract_binary_data_to_text(CAT_FILE, OUTPUT_FILE)

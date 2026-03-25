import random
import string

def generate_star_data(n_stars=10):
    stars = []
    for i in range(n_stars):
        star = {
            "hip": random.randint(10000, 99999),
            "hd": random.randint(100000, 999999),
            "vmag": random.uniform(0.0, 10.0),
            "ra": random.uniform(0.0, 6.283185307179586),
            "de": random.uniform(-1.5707963267948966, 1.5707963267948966),
            "plx": random.uniform(0.0, 0.1),
            "pra": random.uniform(-0.01, 0.01),
            "pde": random.uniform(-0.01, 0.01),
            "bv": random.uniform(-0.5, 2.0),
            "ids": ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(2, 10)))
        }
        stars.append(star)
    return stars


def write_test_txt(filename, stars):
    with open(filename, 'w', encoding='utf-8') as f:
        for star in stars:
            f.write(f"    hip: {star['hip']}\n")
            f.write(f"    hd: {star['hd']}\n")
            f.write(f"    vmag: {star['vmag']}\n")
            f.write(f"    ra: {star['ra']}\n")
            f.write(f"    de: {star['de']}\n")
            f.write(f"    plx: {star['plx']}\n")
            f.write(f"    pra: {star['pra']}\n")
            f.write(f"    pde: {star['pde']}\n")
            f.write(f"    bv: {star['bv']}\n")
            f.write(f"    ids: {star['ids']}\n")


if __name__ == "__main__":
    stars = generate_star_data(10)
    write_test_txt("test.txt", stars)
    print("test.txt文件生成成功！")

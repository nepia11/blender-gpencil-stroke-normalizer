import os
import random
import shutil
import string
import sys
import zipfile

# リリース用のzipを作るスクリプト

file_list = (
    "__init__.py",
    "gpencil_normalizer.py",
    "translations.py",
    "LICENSE",
    "README.md"
)

# 引数
args = sys.argv


def random_name(n: int) -> string:
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))


def make_zip(file_list: tuple, prefix: str):
    org_name: str = "bleder_gpencil_stroke_normalizer"
    zip_name: str = org_name+"_"+prefix
    zip_dir = "./"+zip_name
    zip_path = "./" + zip_name + ".zip"

    os.mkdir(zip_name)
    for s in file_list:
        shutil.copy("./"+s, zip_name)

    zp = zipfile.ZipFile(zip_path, mode="w", compression=zipfile.ZIP_DEFLATED)

    for dirname, subdirs, filenames in os.walk(zip_dir):
        for fname in filenames:
            zp.write(os.path.join(dirname, fname))

    zp.close
    shutil.rmtree(zip_dir)


def main(args):
    try:
        _hash = args[1]
    except IndexError:
        _hash = random_name(4)

    make_zip(file_list, _hash)


main(args)

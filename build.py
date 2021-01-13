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
    "rainbow_strokes.py"
    "LICENSE",
    "README.md"
)

# 引数
args = sys.argv


def random_name(n: int) -> string:
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))


def make_zip(org_name: str, file_list: tuple, prefix: str):
    zip_name: str = org_name+"_"+prefix
    zip_dir = "./"+zip_name
    zip_path = "./" + zip_name + ".zip"
    print(zip_path)

    os.mkdir(zip_name)
    for s in file_list:
        shutil.copy("./"+s, zip_name)

    zp = zipfile.ZipFile(zip_path, mode="w", compression=zipfile.ZIP_DEFLATED)

    for dirname, subdirs, filenames in os.walk(zip_dir):
        for filename in filenames:
            zp.write(os.path.join(dirname, filename))

    zp.close
    shutil.rmtree(zip_dir)


def main(args):
    arg_len = len(args)
    org_name: str = "blender_gpencil_stroke_normalizer"
    prefix: str = ""
    if arg_len == 1:
        prefix = random_name(4)
    elif arg_len == 2:
        prefix = args[1]
    else:
        org_name = args[1]
        prefix = args[2]

    make_zip(org_name, file_list, prefix)


main(args)

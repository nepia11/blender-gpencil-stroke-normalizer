import importlib
from logging import getLogger, StreamHandler, Formatter, handlers, DEBUG
import inspect
import sys
import bpy
import os
import datetime


# アドオン用のいろいろ
bl_info = {
    "name": "Blender Gpencil Stroke Normalizer",
    "author": "nepia",
    "version": (0, 6, 0),
    "blender": (2, 83, 0),
    "location": "view3d > ui > GPN",
    "description": "Provides the ability to arbitrarily adjust the number of points "
    "in a gpencil stroke.",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "https://github.com/nepia11/blender-gpencil-stroke-normalizer/issues",
    "category": "Gpencil",
}


# log周りの設定
def setup_logger(log_folder: str, modname=__name__):
    """ loggerの設定をする """
    logger = getLogger(modname)
    logger.setLevel(DEBUG)
    # log重複回避　https://nigimitama.hatenablog.jp/entry/2021/01/27/084458
    if not logger.hasHandlers():
        sh = StreamHandler()
        sh.setLevel(DEBUG)
        formatter = Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        sh.setFormatter(formatter)
        logger.addHandler(sh)
        fh = handlers.RotatingFileHandler(log_folder, maxBytes=500000, backupCount=2)
        fh.setLevel(DEBUG)
        fh_formatter = Formatter(
            "%(asctime)s - %(filename)s - %(name)s"
            " - %(lineno)d - %(levelname)s - %(message)s"
        )
        fh.setFormatter(fh_formatter)
        logger.addHandler(fh)
    return logger


scripts_dir = os.path.dirname(os.path.abspath(__file__))
log_folder = os.path.join(scripts_dir, f"{datetime.date.today()}.log")
logger = setup_logger(log_folder, modname=__name__)
logger.debug("hello")


# サブモジュールのインポート
module_names = [
    "ops_rainbow_strokes",
    "ops_gpencil_normalizer",
    "ui_mypanel",
    "util",
    "translations",
]
namespace = {}
for name in module_names:
    fullname = "{}.{}.{}".format(__package__, "lib", name)
    # if "bpy" in locals():
    if fullname in sys.modules:
        namespace[name] = importlib.reload(sys.modules[fullname])
    else:
        namespace[name] = importlib.import_module(fullname)
logger.debug(namespace)

# モジュールからクラスの取得 このままだと普通のクラスも紛れ込むのでどうしよっかな
classes = []
for module in module_names:
    for module_class in [
        obj
        for name, obj in inspect.getmembers(namespace[module])
        if inspect.isclass(obj)
    ]:
        classes.append(module_class)


# 翻訳用の辞書
translation_dict = namespace["translations"].get_dict()
translation = bpy.app.translations.pgettext


def register():
    for c in classes:
        logger.debug(f"class:{c},type:{type(c)}")
        try:
            # 少々行儀が悪いが厳密に判定するのめんどいので
            bpy.utils.register_class(c)
        except Exception as e:
            logger.exception(e)

    # 翻訳辞書の登録
    bpy.app.translations.register(__name__, translation_dict)


def unregister():
    # 翻訳辞書の登録解除
    bpy.app.translations.unregister(__name__)

    for c in classes:
        try:
            bpy.utils.unregister_class(c)
        except Exception as e:
            logger.exception(e)


if __name__ == "__main__":
    register()

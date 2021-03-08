import random
import string
import bpy
from logging import getLogger, StreamHandler, Formatter, FileHandler, DEBUG


def setup_logger(log_folder: str, modname=__name__):
    """ loggerの設定をする """
    logger = getLogger(modname)
    logger.setLevel(DEBUG)
    # log重複回避　https://nigimitama.hatenablog.jp/entry/2021/01/27/084458
    if not logger.hasHandlers():
        sh = StreamHandler()
        sh.setLevel(DEBUG)
        formatter = Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        sh.setFormatter(formatter)
        logger.addHandler(sh)

        fh = FileHandler(log_folder)  # fh = file handler
        fh.setLevel(DEBUG)
        fh_formatter = Formatter(
            '%(asctime)s - %(filename)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s')
        fh.setFormatter(fh_formatter)
        logger.addHandler(fh)
    return logger


logger = getLogger(__name__)


def random_name(n: int) -> string:
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))


def object_duplicate_helper(
        obj: bpy.types.Object, name: str) -> bpy.types.Object:
    """
    オブジェクトに任意の名前をつけて複製するヘルパー　複製したオブジェクトを返す
    """
    _mode = bpy.context.mode
    temp_name = random_name(10)
    orig_name = obj.name
    obj.name = temp_name
    bpy.ops.object.duplicate({"selected_objects": [obj]})
    obj.name = orig_name
    new_obj = bpy.data.objects[temp_name + ".001"]
    new_obj.name = name
    bpy.ops.object.mode_set(mode=_mode)
    new_obj.select_set(False)
    return new_obj


def gp_licker(
        gp_data: bpy.types.GreasePencil,
        func,
        state={}):

    if type(gp_data) is not bpy.types.GreasePencil:
        logger.debug("not gpencil")
        return 1

    for li, layer in enumerate(gp_data.layers):
        func(state["layers"][li], layer, "layer")
        for fi, frame in enumerate(layer.frames):
            func(state["layers"][li]["frames"][fi], frame, "frame")
            for si, stroke in enumerate(frame.strokes):
                func(
                    state["layers"][li]["frames"][fi]["strokes"][si],
                    stroke,
                    "stroke")

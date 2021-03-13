import bpy
import colorsys
import numpy as np
from . import util

logger = util.getLogger(__name__)
logger.debug("hello")


def rainbow(index: int) -> [float, float, float, float]:
    h, s, v, a = 1.0, 0.2, 1.0, 1.0
    s_collection = (1.0, 0.8, 0.6, 0.4)

    # 定数　hueの1回転と1ステップに何度回転するかを定義
    ROTATION = 360
    STEP = 40
    step = index * STEP
    rot = step // ROTATION
    h = step / ROTATION % 1
    s = s_collection[rot % len(s_collection)]
    rgba = colorsys.hsv_to_rgb(h, s, v) + (a,)
    # 謎の演算誤差が出るのでfloat32にに変換してから比較
    # もしかしてpythonのfloatってdouble?
    color = np.array(rgba, dtype="float32").tolist()
    return color


def colorize_stroke(
    stroke: bpy.types.GPencilStroke, index: int, visible_start: bool = True
):
    """
    参照方法メモ \n
    lines.frames[0].strokes[0].points[0].vertex_color=(1,0,0,1)
    """
    color = rainbow(index)
    points = stroke.points
    stroke_len = len(points)
    n = -1

    if stroke_len == 1:
        n = 0
        visible_start = False

    # すでに同色に変更済みのストロークを無視する
    test_value = list(points[n].vertex_color)
    # logger.debug(f"testvalue:{test_value}, color:{test_color}")
    if test_value == color:
        return 0

    for point in points:
        point.vertex_color = color

    if visible_start:
        points[0].vertex_color = [0, 0, 0, 1]

    return 1


def rainbow_strokes(strokes: bpy.types.GPencilStrokes):
    """
    strokesのインデックスに合せて頂点カラーを設定します
    """
    n = [colorize_stroke(stroke, i, True) for i, stroke in enumerate(strokes)]
    return n
    # logger.debug(f"update:{sum(n)}")
    # logger.debug(rainbow.cache_info())


def get_stroke_vertex_color(stroke: bpy.types.GPencilStroke) -> list:
    return [tuple(point.vertex_color) for point in stroke.points]


def get_all_strokes_vertex_color(strokes: bpy.types.GPencilStrokes) -> list:
    return [get_stroke_vertex_color(stroke) for stroke in strokes]


class RainbowStrokeObject:
    def init(self, context):
        orig_mode: str = context.mode
        if orig_mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        # もとのオブジェクトを取得、複製
        orig_obj = context.active_object
        new_name = orig_obj.name + ".gpnRsPrev"
        rs_obj = util.object_duplicate_helper(orig_obj, new_name)
        # ロックしておく
        rs_obj.hide_select = True
        rs_obj.show_in_front = True

        self.colorize(rs_obj.data)
        self.orig_obj_name = orig_obj.name
        # https://docs.blender.org/api/current/info_gotcha.html#undo-redo
        # 名前で参照するより直接参照を持ったほうが負荷が少ないんだろうけど、undoした時にバグるのでしょうがなく名前で参照するようにしている
        self.rs_obj_name = rs_obj.name
        context.view_layer.objects.active = orig_obj

        bpy.ops.object.mode_set(mode=orig_mode)

    def update(self, opacity=0.5, emphasize_index=0):
        # old_data = self.rs_obj.data
        old_data = bpy.data.objects[self.rs_obj_name].data
        old_data.name = "trash"
        # new_data = self.orig_obj.data.copy()
        new_data = bpy.data.objects[self.orig_obj_name].data.copy()
        new_data.name = self.rs_obj_name
        for layer in new_data.layers:
            layer.opacity *= opacity
        self.colorize(new_data, emphasize_index)
        # self.rs_obj.data = new_data
        bpy.data.objects[self.rs_obj_name].data = new_data
        bpy.data.batch_remove([old_data.id_data])

    def clear(self):
        try:
            logger.debug("clear rso")
            bpy.ops.object.mode_set(mode="OBJECT")
            logger.debug("clean id_data")
            remove_obj = bpy.data.objects[self.rs_obj_name]
            bpy.data.batch_remove([remove_obj.data])
            logger.debug("clean id_data success")
            bpy.ops.object.delete({"selected_objects": [remove_obj]})
            logger.debug("clean object success")
            pass
        except (KeyError):
            #  見つからないならしょうがない。それ以外のときは例外を見たい
            pass
        del self.orig_obj_name
        del self.rs_obj_name

    @staticmethod
    def colorize(gp_data: bpy.types.GreasePencil, emphasize_index=0):
        for layer in gp_data.layers:
            for frame in layer.frames:
                rainbow_strokes(frame.strokes)
                if len(frame.strokes) - 1 > emphasize_index:
                    points = frame.strokes[emphasize_index].points
                    color = [0, 0, 0, 0]
                    for point in points:
                        point.vertex_color = color

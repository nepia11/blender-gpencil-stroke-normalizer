import bpy
import colorsys
import numpy as np
from functools import cache
from . import util


# 関数の返り値をキャッシュしてくれるらしい
@cache
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
        stroke: bpy.types.GPencilStroke,
        index: int,
        visible_start: bool = True):
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
    # print("testvalue: ", test_value, "color: ", test_color)
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
    print("update:", sum(n))
    print(rainbow.cache_info())


def get_stroke_vertex_color(stroke: bpy.types.GPencilStroke) -> list:
    return [tuple(point.vertex_color) for point in stroke.points]


def get_all_strokes_vertex_color(strokes: bpy.types.GPencilStrokes) -> list:
    return [get_stroke_vertex_color(stroke) for stroke in strokes]


class RainbowStrokes:
    """
    a
    """

    def __init__(self):
        pass

    def save(self, context):
        def _save(state: dict, obj, type_str: str):
            state["tag"] = util.random_name(8)
            if type_str == "layer":
                fl = len(obj.frames)
                state["frames"] = [{} for _ in range(fl)]
            if type_str == "frame":
                sl = len(obj.strokes)
                state["strokes"] = [{} for _ in range(sl)]
            if type_str == "stroke":
                v_color = get_stroke_vertex_color(obj)
                state["vertex_color"] = v_color

        if type(context.active_object.data) is bpy.types.GreasePencil:
            gp_data = context.active_object.data
            self.current_gp_data = gp_data
            state = {
                "layers": [{"tag": util.random_name(8)
                            } for _ in range(len(gp_data.layers))]
            }
            util.gp_licker(gp_data, _save, state)
            self.state = state
            print(state)
            return state

    def load(self, context):
        def _load(state: dict, obj, type_str: str):
            if type_str == "layer":
                pass
            if type_str == "frame":
                pass
            if type_str == "stroke":
                v_color = state["vertex_color"]
                # print("load", v_color)
                for i, point in enumerate(obj.points):
                    point.vertex_color = v_color[i]

        if type(context.active_object.data) is bpy.types.GreasePencil:
            gp_data = context.active_object.data
            self.current_gp_data = gp_data
            util.gp_licker(gp_data, _load, self.state)

    def update(self, context):
        if type(context.active_object.data) is bpy.types.GreasePencil:
            gp_data = context.active_object.data
            for layer in gp_data.layers:
                for frame in layer.frames:
                    rainbow_strokes(frame.strokes)

    def cache_clear(self):
        print(rainbow.cache_info())
        rainbow.cache_clear()
        print(rainbow.cache_info())

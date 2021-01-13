import bpy
import colorsys


def rainbow(index: int) -> (float, float, float, float):
    index = index
    h, s, v, a = 1.0, 0.2, 1.0, 1.0
    # s_collection = (0.2, 0.4, 0.6, 0.8, 1.0)
    s_collection = (1.0, 0.8, 0.6, 0.4, 0.2)

    # 定数　hueの1回転と1ステップに何度回転するかを定義
    ROTATION = 360
    STEP = 40
    step = index * STEP
    rot = step // ROTATION
    h = step / ROTATION % 1
    s = s_collection[rot % len(s_collection)]
    rgb = colorsys.hsv_to_rgb(h, s, v)
    return rgb + (a,)


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
    for point in points:
        point.vertex_color = color

    if visible_start:
        points[0].vertex_color = (0, 0, 0, 1)


def rainbow_strokes(strokes: bpy.types.GPencilStrokes):
    """
    strokesのインデックスに合せて頂点カラーを設定します
    """
    for i, stroke in enumerate(strokes):
        colorize_stroke(stroke, i, True)


def get_stroke_vertex_color(stroke: bpy.types.GPencilStroke) -> list:
    return [tuple(point.vertex_color) for point in stroke.points]


def get_all_strokes_vertex_color(strokes: bpy.types.GPencilStrokes):
    return [get_stroke_vertex_color(stroke) for stroke in strokes]

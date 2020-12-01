# from mathutils import Vector
# from bpy_extras.object_utils import AddObjectHelper, object_data_add
# from bpy.props import FloatVectorProperty
# from bpy.types import Operator

import bpy
import numpy as np


# 2つのベクトルから長さ(ノルム?)を求める。わからなくなるのでラップしてる
def calc_vector3_length(a: "Vector3", b: "Vector3") -> float:
    vec = np.array(b - a)
    return np.linalg.norm(vec)


# ストロークの長さとポイント数を計算して返す
def calc_stroke_length_and_point(gp_stroke: bpy.types.GPencilStroke) -> (float, int):
    vectors = [p.co for p in gp_stroke.points]
    point_count: int = len(vectors)
    norms = np.zeros(point_count)
    for index in range(point_count-1):
        vec_length = calc_vector3_length(vectors[index], vectors[index+1])
        norms[index] = vec_length

    return np.sum(norms), point_count


# 複数フレーム内の１ストロークの長さとポイント最大数を返す
def calc_frames_stroke_length_and_max_count(gp_frames: bpy.types.GPencilFrames, strokes_index: int = 0) -> ([float], int):
    # flag_all = False
    # if select_index == None:
    #     flag_all = True

    point_max_count: int = 0
    lengths: [float] = [0] * len(gp_frames)

    for i, frame in enumerate(gp_frames):
        # if select_index[i] or flag_all:

        stroke_length, count = calc_stroke_length_and_point(
            frame.strokes[strokes_index])
        lengths[i] = stroke_length
        print(stroke_length, count)
        if count > point_max_count:
            point_max_count = count

    return lengths, point_max_count


# ポイント最大数に合わせてストロークをリサンプルする
def normalize_gpencil_by_stroke(gp_frames: bpy.types.GPencilFrames, select_index: [int], stroke_index: int = 0):
    lengths, count = calc_frames_stroke_length_and_max_count(
        gp_frames, select_index, 0)

    for frame_index in range(len(gp_frames)):
        # segment_length = total_length / point_count
        resample_length: float = lengths[frame_index] / count
        print(resample_length)
        # bpy.ops.gpencil.stroke_sample()でストロークをリサンプルできる
        # select = Trueすれば良い
        gp_frames[frame_index].strokes[stroke_index].select = True
        bpy.ops.gpencil.stroke_sample(length=resample_length)


def return_selected_frame_index(gp_frames: bpy.types.GPencilFrames) -> [bool]:
    return [frame.select for frame in gp_frames]


def normalize_gpencil_by_select_frame(gp_frames: bpy.types.GPencilFrames):
    # ストロークペアごとにループしたい
    select_index = return_selected_frame_index(gp_frames)
    stroke_index_length = [len(frame.strokes) for frame in gp_frames]
    frame_length = len(gp_frames)

    for i in range(frame_length):
        pass


def main():
    #    ここにグリースペンシルのストロークのポイントが入っている
    #    bpy.data.grease_pencils['Stroke'].layers["Lines"].frames[0].strokes[0].points
    if bpy.context.active_object.type == "GPENCIL":
        gp_object = bpy.context.active_object.data
        gp_frames = gp_object.layers["Lines"].frames

        normalize_gpencil_by_stroke(gp_frames)


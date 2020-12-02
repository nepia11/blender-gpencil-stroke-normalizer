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
def calc_frames_stroke_length_and_count(gp_frames: bpy.types.GPencilFrames, strokes_index: int = 0) -> ([float], [int], int):

    point_max_count: int = 0
    lengths: [float] = [0.0] * len(gp_frames)
    counts: [int] = [0] * len(gp_frames)

    for i, frame in enumerate(gp_frames):
        print("frame ",i,"stroke",strokes_index)
        stroke_length, count = calc_stroke_length_and_point(
            frame.strokes[strokes_index])
        lengths[i] = stroke_length
        counts[i] = count
        print(stroke_length, count)
        if count > point_max_count:
            point_max_count = count

    return lengths, counts, point_max_count


def get_selected_frame_index(gp_frames: bpy.types.GPencilFrames) -> [bool]:
    return [frame.select for frame in gp_frames]


def get_max_count_by_selected_frames(counts: [int], select_frame_indexs: [bool]) -> int:
    max_count = 0
    for i, count in enumerate(counts):
        if select_frame_indexs[i] and count > max_count:
            max_count = count
    return max_count


"""(flag_select_only and select_frame_indexs[frame_index]
フラグが有効なら選択範囲内でのポイント最大数に合わせてリサンプルする

"""


def normalize_gpencil(gp_frames: bpy.types.GPencilFrames, flag_select_only: bool):
    # フレームの選択状態を一括取得
    select_frame_indexs: [bool] = get_selected_frame_index(gp_frames)
    # フレームごとストローク数
    strokes_counts = [len(frame.strokes) for frame in gp_frames]
    # フレーム総数
    frames_length = len(gp_frames)

    def resample_stroke(frame_index, stroke_index):
        if frames_length == 1:
            print("スキップ",frames_length,stroke_index)
            return 0

        
        print("resample_stroke")
        lengths, counts, max_count = calc_frames_stroke_length_and_count(
            gp_frames, stroke_index)

        # 選択フレームのみリサンプルしたいときのmax_countを取得
        if flag_select_only:
            max_count = get_max_count_by_selected_frames(
                counts, select_frame_indexs)

        resample_length: float = lengths[frame_index] / max_count
        # bpy.ops.gpencil.stroke_sample()でストロークをリサンプルできる
        # select = Trueになってるストローク全部にかかるので選択解除してからやる
        for stroke in gp_frames[frame_index].strokes:
            stroke.select = False

        gp_frames[frame_index].strokes[stroke_index].select = True
        bpy.ops.gpencil.stroke_sample(length=resample_length)

    # 選択条件を判定して、すべての有効ストロークをリサンプルする
    print("frames_length",frames_length)
    for frame_index in range(frames_length):
        # フラグが有効かつ選択フレームかのフラグ
        is_select_enable: bool = flag_select_only and select_frame_indexs[frame_index]
        if (flag_select_only == False) or is_select_enable:
            for _stroke_index in range(strokes_counts[frame_index]):
                resample_stroke(frame_index, _stroke_index)


# operatorから呼ぶやつ
def ops_execute(select_only:bool, context:bpy.types.Context):
    # active_obj = context.active_object
    if context.active_object.type == "GPENCIL":
        gp_object = context.active_object.data
        gp_layers = gp_object.layers
        active_layers_index = [layer.select for layer in gp_layers]
        layer_names = []

        if select_only:
            for i, layer in enumerate(gp_layers):
                if active_layers_index[i]:
                    layer_names.append(layer.info)
                    print(layer.info)
                    normalize_gpencil(gp_frames=layer.frames,
                                      flag_select_only=True)
        else:
            for i, layer in enumerate(gp_layers):
                layer_names.append(layer.info)
                print(layer.info)
                normalize_gpencil(gp_frames=layer.frames,
                                  flag_select_only=False)

    return layer_names


# アドオン用のいろいろ
bl_info = {
    "name": "gpencil normalizer",
    "author": "nepia",
    "version": (0, 1),
    "blender": (2, 80, 0),
    "location": "3Dビューポート > 編集モード",
    "description": "gpencilのストロークのポイント数をフレーム間の最大値にリサンプルする",
    "warning": "",
    "support": "TESTING",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Gpencil"
}


class NP_GPN_OT_GPencilStrokeNormalizer(bpy.types.Operator):

    bl_idname = "gpencil.np_gpencil_stroke_normalizer"
    bl_label = "stroke normalizer"
    bl_description = "すべてのストロークを正規化する"
    bl_options = {'REGISTER', 'UNDO'}

    # メニューを実行したときに呼ばれるメソッド
    def execute(self, context):
        layer_names = ops_execute(select_only=False,context=context)

        self.report(
            {'INFO'}, "gpencil normalizer: resampled {}".format(layer_names))
        return {'FINISHED'}

class NP_GPN_OT_GPencilStrokeNormalizerSelectOnly(bpy.types.Operator):

    bl_idname = "gpencil.np_gpencil_stroke_normalizer_select_only"
    bl_label = "stroke normalizer(select only)"
    bl_description = "選択されたレイヤー、フレームのストロークを正規化する"
    bl_options = {'REGISTER', 'UNDO'}

    # メニューを実行したときに呼ばれるメソッド
    def execute(self, context):
        layer_names = ops_execute(select_only=True,context=context)

        self.report(
            {'INFO'}, "gpencil normalizer: resampled {}".format(layer_names))
        return {'FINISHED'}


def menu_fn(self, context):
    self.layout.separator()
    self.layout.operator(NP_GPN_OT_GPencilStrokeNormalizer.bl_idname)
    self.layout.operator(NP_GPN_OT_GPencilStrokeNormalizerSelectOnly.bl_idname)


classes = [
    NP_GPN_OT_GPencilStrokeNormalizer,
    NP_GPN_OT_GPencilStrokeNormalizerSelectOnly,
]


def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.VIEW3D_MT_gpencil_edit_context_menu.append(menu_fn)


def unregister():
    bpy.types.VIEW3D_MT_gpencil_edit_context_menu.remove(menu_fn)
    for c in classes:
        bpy.utils.unregister_class(c)


if __name__ == "__main__":
    register()

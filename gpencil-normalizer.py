from bpy.props import FloatProperty, IntProperty, EnumProperty
from bpy.types import Operator

import bpy
import numpy as np

DEBUG = True


def debug_print(*args):
    if DEBUG == True:
        print(*args)


# 2つのベクトルから長さ(ノルム?)を求める。わからなくなるのでラップしてる
def calc_vector3_length(a: "Vector3", b: "Vector3") -> float:
    vec = np.array(b - a, dtype="float64")
    return np.linalg.norm(vec)


# ストロークの長さとポイント数を計算して返す
def calc_stroke_length_and_point(gp_stroke: bpy.types.GPencilStroke) -> (float, int):
    vectors = [p.co for p in gp_stroke.points]
    point_count: int = len(vectors)
    norms = np.zeros(point_count, dtype="float64")
    for index in range(point_count-1):
        vec_length = calc_vector3_length(vectors[index], vectors[index+1])
        norms[index] = vec_length

    length = np.sum(norms, dtype="float64")

    return length, point_count


# 複数フレーム内の１ストロークの長さとポイント最大数を返す
def calc_frames_stroke_length_and_count(gp_frames: bpy.types.GPencilFrames, strokes_index: int = 0) -> ([float], [int], int):

    point_max_count: int = 0
    lengths: [float] = [0.0] * len(gp_frames)
    counts: [int] = [0] * len(gp_frames)

    for i, frame in enumerate(gp_frames):
        debug_print("frame ", i, "stroke", strokes_index)
        stroke_length, count = calc_stroke_length_and_point(
            frame.strokes[strokes_index])
        lengths[i] = stroke_length
        counts[i] = count
        debug_print(stroke_length, count)
        if count > point_max_count:
            point_max_count = count

    return lengths, counts, point_max_count


# def get_selected_frame_index(gp_frames: bpy.types.GPencilFrames) -> [bool]:
#     return [frame.select for frame in gp_frames]


# def get_max_count_by_selected_frames(counts: [int], select_frame_indexs: [bool]) -> int:
#     max_count = 0
#     for i, count in enumerate(counts):
#         if select_frame_indexs[i] and count > max_count:
#             max_count = count
#     return max_count


# ストロークをポイント数でサンプリングする
def stroke_count_resampler(gp_stroke: bpy.types.GPencilStroke, result_count: int) -> (int, float, int, int):
    # 長さとポイント数を計算
    src_length, src_count = calc_stroke_length_and_point(gp_stroke)
    # サンプリングレートを決定
    sample_length = src_length / (result_count-1)
    # 適当なオフセットをつける 意味なかったかも
    offset = sample_length / (result_count*2)
    sample_length = sample_length + offset
    # サンプリング実行
    gp_stroke.select = True
    bpy.ops.gpencil.stroke_sample(length=sample_length)

    dst_count = len(gp_stroke.points)
    return src_count, src_length, dst_count, result_count


# def get_layers_select_state(gp_data: bpy.types.GreasePencil) -> [bool]:
#     return [layer.select for layer in gp_data.layers]


# def get_frames_select_state(gp_frames: bpy.types.GPencilFrames) -> [bool]:
#     return [frame.select for frame in gp_frames]


# def get_strokes_select_state(gp_strokes: bpy.types.GPencilStrokes):
#     return [stroke.select for stroke in gp_strokes]


# def get_strokes_select_state_by_frames(gp_frames: bpy.types.GPencilFrames) -> ([[bool]]):
#     return [get_strokes_select_state(frame.strokes) for frame in gp_frames]

# この機能いるか？


# def get_select_state(gp_data: bpy.types.GreasePencil):
#     layers = gp_data.layers
#     layer_state = get_layers_select_state(gp_data)
#     # [layer0[bool,bool],layre1[,,,]]
#     frame_state = [get_frames_select_state(layer.frames) for layer in layers]
#     stroke_state = [get_strokes_select_state_by_frames(
#         layer.frames) for layer in layers]  # [l[f[s:bool,,],,],,]
#     return layer_state, frame_state, stroke_state


class GpSelectState:
    def __init__(self, gp_data: bpy.types.GreasePencil):
        self.layers = gp_data.layers
        self.state = {}

    def _lick(self, state, func):
        for li, layer in enumerate(self.layers):
            func(state["layers"][li], layer)
            for fi, frame in enumerate(layer.frames):
                func(state["layers"][li]["frames"][fi], frame)
                for si, stroke in enumerate(frame.strokes):
                    func(state["layers"][li]["frames"]
                         [fi]["strokes"][si], stroke)

    def save(self) -> "state":
        state = {"layers": [{"select": False}]*len(self.layers)}

        def _save(state, obj):
            debug_print(state, obj)
            obj_type = type(obj)
            if obj_type is bpy.types.GPencilLayer:
                state["frames"] = [{}]*len(obj.frames)
            elif obj_type is bpy.types.GPencilFrame:
                state["strokes"] = [{}]*len(obj.strokes)
            state["select"] = obj.select

        self._lick(state, _save)
        self.state = state
        return state

    def load(self):
        def _load(state, obj):
            obj.select = state["select"]
        self._lick(self.state, _load)

    def deselect_all(self):

        def _deselect(state, obj):
            obj.select = False
        self._lick(self.state, _deselect)

    def apply(self, result_count):
        debug_print(self.state)
        def _apply(state, obj):
            _type = type(obj)
            is_type = _type is bpy.types.GPencilStroke
            debug_print("state select", state["select"], _type, is_type)
            if state["select"] and is_type:
                debug_print("exec")
                obj.select = True
                stroke_count_resampler(obj, result_count)
                obj.select = False
        self._lick(self.state, _apply)


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


class NP_GPN_OT_GPencilStrokeCountResampler(bpy.types.Operator):

    bl_idname = "gpencil.np_gpencil_stroke_count_resampler"
    bl_label = "stroke count resampler"
    bl_description = "ストロークをポイント数でサンプリングする"
    bl_options = {'REGISTER', 'UNDO'}

    amount: IntProperty(
        name="ポイント数",
        description="ポイント数を設定します",
        default=100,
        min=0
    )

    # メニューを実行したときに呼ばれるメソッド
    def execute(self, context):
        # bpy.context.active_object.data = bpy.data.grease_pencils['Stroke']
        gp_data = context.active_object.data
        result_count = self.amount

        select_state = GpSelectState(gp_data)
        state = select_state.save()
        # select_state.deselect_all()
        # select_state.apply(result_count)
        select_state.load()

        self.report(
            {'INFO'}, "done stroke resample")

        return {'FINISHED'}


def menu_fn(self, context):
    self.layout.separator()
    self.layout.operator(NP_GPN_OT_GPencilStrokeCountResampler.bl_idname)


classes = [
    NP_GPN_OT_GPencilStrokeCountResampler,
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

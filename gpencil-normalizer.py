from bpy.props import FloatProperty, IntProperty, EnumProperty
from bpy.types import Operator

import bpy
import numpy as np
import pprint
import random
import string

DEBUG = False


def debug_print(*args):
    if DEBUG == True:
        print(*args)


def random_name(n):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=n))


# 2つのベクトルから長さ(ノルム?)を求める。わからなくなるのでラップしてる
def calc_vector3_length(a: "Vector3", b: "Vector3") -> float:
    vec = np.array(b - a, dtype="float64")
    return np.linalg.norm(vec)


# ストロークの長さとポイント数を計算して返す これ分解したほうが良いかもな
def calc_stroke_length_and_point(gp_stroke: bpy.types.GPencilStroke) -> (float, int):
    vectors = [p.co for p in gp_stroke.points]
    point_count: int = len(vectors)
    norms = np.zeros(point_count, dtype="float64")
    for index in range(point_count-1):
        vec_length = calc_vector3_length(vectors[index], vectors[index+1])
        norms[index] = vec_length

    length = np.sum(norms, dtype="float64")

    return length, point_count


def count_stroke_points(gp_stroke: bpy.types.GPencilStroke) -> int:
    vectors = [p.co for p in gp_stroke.points]
    point_count: int = len(vectors)
    return point_count


# フレーム間の各ストロークのポイント最大数を返す
def calc_frames_strokes_max_count(gp_frames: bpy.types.GPencilFrames) -> ([int]):
    frames_counts = [0]*len(gp_frames)
    for i, frame in enumerate(gp_frames):
        counts = [count_stroke_points(stroke) for stroke in frame.strokes]
        frames_counts[i] = counts

    np_counts = np.array(frames_counts)
    results_max = np.max(np_counts, axis=0)
    pprint.pprint(np_counts)

    return results_max
    """
    [
        frame[stroke1,2,3,4],
        frame[stroke1,2,3,4],
        frame[stroke1,2,3,4],
        frame[stroke1,2,3,4],
    ]
    こんな感じで入ってるのを
    [stroke_max,stroke_max,stroke_max,stroke_max,]
    こうしてる感じ
    """


# ストロークをポイント数でサンプリングする
def stroke_count_resampler(gp_stroke: bpy.types.GPencilStroke, result_count: int) -> (int, float, int, int):
    # 長さとポイント数を計算
    src_length, src_count = calc_stroke_length_and_point(gp_stroke)
    # サンプリングレートを決定
    sample_length = src_length / (result_count-1)
    # 適当なオフセットをつける 意味なかったかも
    offset = sample_length / (result_count)
    sample_length = sample_length + offset
    # サンプリング実行
    gp_stroke.select = True
    bpy.ops.gpencil.stroke_sample(length=sample_length)

    dst_count = len(gp_stroke.points)
    return src_count, src_length, dst_count, result_count


class GpSelectState:
    """
    選択状態を保持したり、読み込んだりしてくれる君
    """

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
        # state = {"layers": [{"select": False}]*len(self.layers)}
        state = {"layers": [{"select": False}
                            for i in range(len(self.layers))]}
        # 現在のフレームを保存しておく
        state["frame_current"] = bpy.context.scene.frame_current

        def _save(state, obj):
            debug_print("## start _save()")
            debug_print("state,obj", state, obj)
            obj_type = type(obj)
            if obj_type is bpy.types.GPencilLayer:
                debug_print("### init state[frames]")
                state["frames"] = [{} for i in range(len(obj.frames))]
                max_counts = calc_frames_strokes_max_count(obj.frames)
                state["max_counts"] = max_counts

            elif obj_type is bpy.types.GPencilFrame:
                debug_print("### init state[strokes]")
                state["strokes"] = [{} for i in range(len(obj.strokes))]
                state["frame_number"] = obj.frame_number

            state["select"] = obj.select
            state["tag"] = random_name(8)
            debug_print("### state[select]:", state, obj.select)

        debug_print("# start save() loop")
        self._lick(state, _save)
        self.state = state
        debug_print("# end state")
        # pprint.pprint(self.state)
        return state

    def load(self):
        bpy.context.scene.frame_current = self.state["frame_current"]

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
            is_stroke = _type is bpy.types.GPencilStroke
            is_valid = state["select"] and is_stroke
            # debug_print("state select", state["select"], _type, is_type)
            if _type is bpy.types.GPencilFrame:
                bpy.context.scene.frame_current = state["frame_number"]
            if is_valid:
                obj.select = True
                stroke_count_resampler(obj, result_count)
                obj.select = False
        self._lick(self.state, _apply)


# アドオン用のいろいろ
bl_info = {
    "name": "gpencil normalizer",
    "author": "nepia",
    "version": (0, 2, 1),
    "blender": (2, 83, 0),
    "location": "3Dビューポート > 編集モード",
    "description": "gpencilのストロークのポイント数をフレーム間の最大値にリサンプルする",
    "warning": "",
    "support": "TESTING",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Gpencil"
}

# 翻訳用の辞書
# bpy.app.translations.pgettext("Template")
translation_dict = {
    "en_US": {
        # ("*", "Template"): "Template",
        ("*", "Sampling selection strokes by number of points"): "Sampling selection strokes by number of points",
        ("*", "Sampling strokes"): "Sampling strokes",
        ("*", "number of points"): "number of points",
        ("*", "Normalize stroke"): "Normalize stroke",
        ("*", "Normalize stroke description"): "Match the maximum number of points for the same stroke between frames.",




    },
    "ja_JP": {
        # ("*", "Template"): "テンプレート",
        ("*", "Sampling selection strokes by number of points"): "選択ストロークをポイント数でサンプリングする",
        ("*", "Sampling strokes"): "ストロークをサンプリング",
        ("*", "number of points"): "ポイント数",
        ("*", "Normalize stroke"): "ストロークを正規化",
        ("*", "Normalize stroke description"): "フレーム間、同一ストロークのポイント数を最大値に合わせる",


    }
}


translation = bpy.app.translations.pgettext


class NP_GPN_OT_GPencilStrokeCountResampler(bpy.types.Operator):

    bl_idname = "gpencil.np_gpencil_stroke_count_resampler"
    bl_label = translation("Sampling strokes")
    bl_description = translation(
        "Sampling selection strokes by number of points")

    bl_options = {'REGISTER', 'UNDO'}

    amount: IntProperty(
        name=translation("number of points"),
        description="",
        default=100,
        min=0
    )

    # メニューを実行したときに呼ばれるメソッド
    def execute(self, context):
        # bpy.context.active_object.data = bpy.data.grease_pencils['Stroke']
        gp_data = context.active_object.data
        result_count = self.amount

        select_state = GpSelectState(gp_data)
        select_state.save()
        select_state.deselect_all()
        select_state.apply(result_count)
        select_state.load()

        self.report(
            {'INFO'}, "done stroke resample")

        return {'FINISHED'}


class NP_GPN_OT_GPencilStrokeCountNormalizer(bpy.types.Operator):

    bl_idname = "gpencil.np_gpencil_stroke_count_normalizer"
    bl_label = translation("Normalize stroke")
    bl_description = translation("Normalize stroke description")
    bl_options = {'REGISTER', 'UNDO'}

    # メニューを実行したときに呼ばれるメソッド
    def execute(self, context):
        # bpy.context.active_object.data = bpy.data.grease_pencils['Stroke']
        gp_data = context.active_object.data
        result_count = 100

        select_state = GpSelectState(gp_data)
        state1 = select_state.save()
        select_state.deselect_all()

        for li, layer in enumerate(select_state.layers):
            max_counts = state1["layers"][li]["max_counts"]
            for fi, frame in enumerate(layer.frames):
                frame_number = state1["layers"][li]["frames"][fi]["frame_number"]
                bpy.context.scene.frame_current = frame_number
                for si, stroke in enumerate(frame.strokes):
                    stroke.select = True
                    debug_print("## max,si", max_counts, si)
                    stroke_count_resampler(stroke, result_count=max_counts[si])
                    stroke.select = False

        # bpy.context.scene.frame_current = select_state.state["frame_current"]

        select_state.load()

        self.report(
            {'INFO'}, "done stroke resample")

        return {'FINISHED'}


def menu_fn(self, context):
    self.layout.separator()
    self.layout.operator(NP_GPN_OT_GPencilStrokeCountResampler.bl_idname)
    self.layout.operator(NP_GPN_OT_GPencilStrokeCountNormalizer.bl_idname)


classes = [
    NP_GPN_OT_GPencilStrokeCountResampler,
    NP_GPN_OT_GPencilStrokeCountNormalizer,
]


def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.VIEW3D_MT_gpencil_edit_context_menu.append(menu_fn)

    # 翻訳辞書の登録
    bpy.app.translations.register(__name__, translation_dict)


def unregister():
    # 翻訳辞書の登録解除
    bpy.app.translations.unregister(__name__)

    bpy.types.VIEW3D_MT_gpencil_edit_context_menu.remove(menu_fn)
    for c in classes:
        bpy.utils.unregister_class(c)


if __name__ == "__main__":
    register()

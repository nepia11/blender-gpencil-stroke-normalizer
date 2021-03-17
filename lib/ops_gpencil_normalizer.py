import bpy
import mathutils
import numpy as np
import util
from bpy import ops, props, types

# log setup
logger = util.getLogger(__name__)
logger.debug("hello")

translation = bpy.app.translations.pgettext
random_name = util.random_name


# 2つのベクトルから長さを求める
def calc_vector_length(a: mathutils.Vector, b: mathutils.Vector) -> float:
    vec = b - a
    return vec.length


# ストロークの長さとポイント数を計算して返す これ分解したほうが良いかもな
def calc_stroke_length_and_point(gp_stroke: types.GPencilStroke) -> (float, int):
    vectors = [p.co for p in gp_stroke.points]
    point_count: int = len(vectors)
    norms = [
        calc_vector_length(vectors[i], vectors[i + 1]) for i in range(point_count - 1)
    ]
    length = sum(norms)
    return length, point_count


def count_stroke_points(gp_stroke: types.GPencilStroke) -> int:
    point_count: int = len(gp_stroke.points)
    return point_count


# フレーム間の各ストロークのポイント最大数を返す
def calc_frames_strokes_max_count(gp_frames: types.GPencilFrames) -> ([int]):
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
    frame_len = len(gp_frames)

    logger.debug(f"#calc_frames_strokes_max_count():->frame_len: {frame_len}")

    if frame_len == 0:
        return 0

    frames_counts = [0] * frame_len
    length = 0
    for i, frame in enumerate(gp_frames):
        counts = [
            count_stroke_points(stroke) for stroke in frame.strokes
        ]  # [int,int,,,]
        frames_counts[i] = counts  # [[counts],[],]
        counts_len = len(counts)
        if length < counts_len:
            length = counts_len
    # padding
    for counts in frames_counts:
        counts += [0] * (length - len(counts))
    np_counts = np.array(frames_counts)
    results_max = np.max(np_counts, axis=0)
    # pprint.pprint(np_counts)
    # pprint.pprint(results_max)

    return results_max


def calc_offset(src_len: float, segment_len: float, point_count: int) -> float:
    # 演算誤差をチェックしたい
    FACTOR = 1.5
    total_error = sum([segment_len] * point_count)
    segment_error = src_len - total_error
    offset = (segment_error / point_count) * FACTOR
    return offset


# ストロークをポイント数でサンプリングする
def stroke_count_resampler(
    gp_stroke: types.GPencilStroke, result_count: int
) -> (int, float, int, int):
    # 単純にresult_countで割るとポイント数に1,2程度の誤差が起きるのでオフセット値をつける
    # 1.5でうまく行くことはわかったけど理由がわからない　ほんとに何？？？
    OFFSET = 1.6
    # 長さとポイント数を計算
    src_length, src_count = calc_stroke_length_and_point(gp_stroke)
    # サンプリングレートを決定
    sample_length = src_length / (result_count - OFFSET)
    # サンプリング実行
    gp_stroke.select = True
    ops.gpencil.stroke_sample(length=sample_length)

    # 結果を確認するとき用
    dst_count = len(gp_stroke.points)
    return src_count, src_length, dst_count, result_count


class GpSelectState:
    """
    選択状態を保持したり、読み込んだりしてくれる君
    """

    def __init__(self, gp_data: types.GreasePencil, context: types.Context):
        self.layers = gp_data.layers
        self.context = context
        self.state = {}

    def _lick(self, state, func):
        for li, layer in enumerate(self.layers):
            func(state["layers"][li], layer)
            for fi, frame in enumerate(layer.frames):
                func(state["layers"][li]["frames"][fi], frame)
                for si, stroke in enumerate(frame.strokes):
                    func(state["layers"][li]["frames"][fi]["strokes"][si], stroke)

    def save(self) -> dict:
        # state = {"layers": [{"select": False}]*len(self.layers)}
        state = {"layers": [{"select": False} for i in range(len(self.layers))]}
        # 現在のフレームを保存しておく
        state["frame_current"] = self.context.scene.frame_current

        def _save(state, obj):
            logger.debug("## start _save()")
            logger.debug(f"state,obj{state},{obj}")
            obj_type = type(obj)
            if obj_type is types.GPencilLayer:
                logger.debug("### init state[frames]")
                state["frames"] = [{} for i in range(len(obj.frames))]
                max_counts = calc_frames_strokes_max_count(obj.frames)
                state["max_counts"] = max_counts

            elif obj_type is types.GPencilFrame:
                logger.debug("### init state[strokes]")
                state["strokes"] = [{} for i in range(len(obj.strokes))]
                state["frame_number"] = obj.frame_number

            state["select"] = obj.select
            state["tag"] = random_name(8)
            logger.debug(f"### state[select]:{state},{obj.select}")

        logger.debug("# start save() loop")
        self._lick(state, _save)
        self.state = state
        logger.debug("# end state")
        # pprint.pprint(self.state)
        return state

    def load(self):
        self.context.scene.frame_current = self.state["frame_current"]

        def _load(state, obj):
            obj.select = state["select"]

        self._lick(self.state, _load)

    def deselect_all(self):
        def _deselect(state, obj):
            obj.select = False

        self._lick(self.state, _deselect)

    # この機能はこいつの責務なのか？
    def apply(self, result_count):
        logger.debug(self.state)

        def _apply(state, obj):
            _type = type(obj)
            is_stroke = _type is types.GPencilStroke
            is_valid = state["select"] and is_stroke
            # logger.debug(f"state select:{state["select"]} {_type} {is_type}")
            if _type is types.GPencilFrame:
                self.context.scene.frame_current = state["frame_number"]
            if is_valid:
                obj.select = True
                stroke_count_resampler(obj, result_count)
                obj.select = False

        self._lick(self.state, _apply)


class NP_GPN_OT_GPencilStrokeCountResampler(types.Operator):

    bl_idname = "gpencil.np_gpencil_stroke_count_resampler"
    bl_label = translation("Sampling strokes")
    bl_description = translation("Sampling selection strokes by number of points")

    bl_options = {"REGISTER", "UNDO"}

    amount = props.IntProperty(
        name=translation("number of points"),
        default=100,
        min=2,
    )

    # メニューを実行したときに呼ばれるメソッド
    def execute(self, context):
        # context.active_object.data = data.grease_pencils['Stroke']
        gp_data = context.active_object.data
        result_count = self.amount

        select_state = GpSelectState(gp_data, context)
        select_state.save()
        select_state.deselect_all()
        select_state.apply(result_count)
        select_state.load()

        self.report({"INFO"}, "done stroke resample")
        return {"FINISHED"}


class NP_GPN_OT_GPencilStrokeCountNormalizer(types.Operator):

    bl_idname = "gpencil.np_gpencil_stroke_count_normalizer"
    bl_label = translation("Normalize strokes")
    bl_description = translation(
        "Match the maximum number of points " "for the same stroke between frames."
    )
    bl_options = {"REGISTER", "UNDO"}

    # メニューを実行したときに呼ばれるメソッド
    def execute(self, context):
        # context.active_object.data = data.grease_pencils['Stroke']
        gp_data = context.active_object.data

        select_state = GpSelectState(gp_data, context)
        state1 = select_state.save()
        select_state.deselect_all()

        for li, layer in enumerate(select_state.layers):
            max_counts = state1["layers"][li]["max_counts"]
            # 選択レイヤーだけ処理したいので
            if state1["layers"][li]["select"]:
                for fi, frame in enumerate(layer.frames):
                    frame_number = state1["layers"][li]["frames"][fi]["frame_number"]
                    context.scene.frame_current = frame_number
                    for si, stroke in enumerate(frame.strokes):
                        stroke.select = True
                        stroke_count_resampler(stroke, result_count=max_counts[si])
                        stroke.select = False

        # context.scene.frame_current = select_state.state["frame_current"]

        select_state.load()

        self.report({"INFO"}, "done stroke resample")

        return {"FINISHED"}

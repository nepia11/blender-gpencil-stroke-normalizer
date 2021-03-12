# blenderのreload scripts対応
if not ("bpy" in locals()):
    from .lib import translations
    from .lib import gpencil_normalizer
    from .lib import rainbow_strokes
    from .lib import util
else:
    import imp

    imp.reload(translations)
    imp.reload(gpencil_normalizer)
    imp.reload(rainbow_strokes)
    imp.reload(util)

import bpy
from bpy import props, types
import datetime

# log周りの設定
log_folder = "{0}.log".format(datetime.date.today())
logger = util.setup_logger(log_folder, modname=__name__)
logger.debug("hello")

GpSelectState = gpencil_normalizer.GpSelectState
stroke_count_resampler = gpencil_normalizer.stroke_count_resampler

# 翻訳用の辞書
translation_dict = translations.translation_dict
translation = bpy.app.translations.pgettext

# アドオン用のいろいろ
bl_info = {
    "name": "Blender Gpencil Stroke Normalizer",
    "author": "nepia",
    "version": (0, 5, 0),
    "blender": (2, 83, 0),
    "location": "types.VIEW3D_PT_tools_grease_pencil_interpolate",
    "description": "Provides the ability to arbitrarily adjust the number of points "
    "in a gpencil stroke.",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "https://github.com/nepia11/blender-gpencil-stroke-normalizer/issues",
    "category": "Gpencil",
}


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


class NP_GPN_OT_RainbowStrokes(types.Operator):
    # timer eventについて参照
    # https://colorful-pico.net/introduction-to-addon-development-in-blender/2.8/html/chapter_03/03_Handle_Timer_Event.html

    bl_idname = "gpencil.np_rainbow_strokes"
    bl_label = "rainbow strokes"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    # タイマのハンドラ
    __timer = None

    interval = 0.2

    rso = rainbow_strokes.RainbowStrokeObject()

    @classmethod
    def is_running(cls):
        # モーダルモード中はTrue
        return True if cls.__timer else False

    def __handle_add(self, context):
        if not self.is_running():
            # タイマを登録
            interval = self.interval
            NP_GPN_OT_RainbowStrokes.__timer = context.window_manager.event_timer_add(
                interval, window=context.window
            )
            # モーダルモードへの移行
            self.rso.init(context)
            context.window_manager.modal_handler_add(self)

    def __handle_remove(self, context):
        if self.is_running():
            # タイマの登録を解除
            context.window_manager.event_timer_remove(NP_GPN_OT_RainbowStrokes.__timer)
            NP_GPN_OT_RainbowStrokes.__timer = None
            self.rso.clear()

    def modal(self, context, event):
        # op_cls = NP_GPN_OT_RainbowStrokes
        # エリアを再描画
        if context.area:
            context.area.tag_redraw()
        if not self.is_running():
            return {"FINISHED"}

        emphasize_index = context.scene.gpn_rainbowStroke_emphasize_index
        opacity = context.scene.gpn_rainbowStroke_opacity
        # タイマーイベントが来た時にする処理
        if event.type == "TIMER":
            try:
                self.rso.update(opacity=opacity, emphasize_index=emphasize_index)
            except (KeyError):
                # モーダルモードを終了
                logger.debug("key error")
                self.__handle_remove(context)
                return {"FINISHED"}
                # return {'CANCELLED'}

        return {"PASS_THROUGH"}

    def invoke(self, context, event):
        op_cls = NP_GPN_OT_RainbowStrokes

        if context.area.type == "VIEW_3D":
            if not op_cls.is_running():
                # モーダルモードを開始
                self.__handle_add(context)
                return {"RUNNING_MODAL"}
            # [終了] ボタンが押された時の処理
            else:
                # モーダルモードを終了
                self.__handle_remove(context)
                return {"FINISHED"}
        else:
            return {"FINISHED"}


class NP_GPN_PT_GPencilNormalizer(bpy.types.Panel):

    bl_label = "GPencil Normalizer"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "GPN"

    # 本クラスの処理が実行可能かを判定する
    @classmethod
    def poll(cls, context):
        # アクティブオブジェクトがgpencilか
        try:
            if type(context.active_object.data) is bpy.types.GreasePencil:
                return True
        except AttributeError:
            return False

    def draw(self, context):
        layout = self.layout
        # ranbow strokes
        layout.label(text="rainbow strokes")
        # [開始] / [終了] ボタンを追加
        if not NP_GPN_OT_RainbowStrokes.is_running():
            layout.operator(
                NP_GPN_OT_RainbowStrokes.bl_idname, text="Start", icon="PLAY"
            )
        else:
            layout.operator(
                NP_GPN_OT_RainbowStrokes.bl_idname, text="Stop", icon="PAUSE"
            )
        layout.prop(context.scene, "gpn_rainbowStroke_opacity", text="rainbow opacity")
        layout.prop(context.scene, "gpn_rainbowStroke_emphasize_index")
        layout.separator()
        # ストローク並べ替え
        layout.label(text="Sorting strokes")
        arrange_props = [
            ("TOP", "Bring to Front"),
            ("UP", "Bring Forward"),
            ("DOWN", "Send Backward"),
            ("BOTTOM", "Send to Back"),
        ]
        for prop in arrange_props:
            op = layout.operator("gpencil.stroke_arrange", text=translation(prop[1]))
            op.direction = prop[0]
        layout.separator()
        # ストロークサンプリング機能
        layout.label(text=translation("Normalize strokes"))
        layout.operator(
            NP_GPN_OT_GPencilStrokeCountResampler.bl_idname,
            text=translation("Sampling strokes"),
        )
        layout.operator(
            NP_GPN_OT_GPencilStrokeCountNormalizer.bl_idname,
            text=translation("Normalize strokes"),
        )


def init_props():
    scene = bpy.types.Scene
    scene.gpn_rainbowStroke_opacity = bpy.props.FloatProperty(
        name="rainbow_opacity",
        description="rainbowStrokeの透明度",
        default=0.75,
        min=0.0,
        max=1.0,
    )
    scene.gpn_rainbowStroke_emphasize_index = bpy.props.IntProperty(
        name="Emphasize index", description="強調するストロークのインデックス", min=0
    )


classes = [
    NP_GPN_OT_GPencilStrokeCountResampler,
    NP_GPN_OT_GPencilStrokeCountNormalizer,
    NP_GPN_OT_RainbowStrokes,
    NP_GPN_PT_GPencilNormalizer,
]


def register():
    for c in classes:
        bpy.utils.register_class(c)

    init_props()
    # 翻訳辞書の登録
    bpy.app.translations.register(__name__, translation_dict)


def unregister():
    # 翻訳辞書の登録解除
    bpy.app.translations.unregister(__name__)

    for c in classes:
        bpy.utils.unregister_class(c)


if __name__ == "__main__":
    register()

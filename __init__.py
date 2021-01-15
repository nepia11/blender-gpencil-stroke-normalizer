if not("bpy" in locals()):
    from . import translations
    from . import gpencil_normalizer
    from . import rainbow_strokes
else:
    import imp
    imp.reload(translations)
    imp.reload(gpencil_normalizer)
    imp.reload(rainbow_strokes)


import bpy
from bpy import props, types


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
    "description":
            "Provides the ability to arbitrarily adjust the number of points "
            "in a gpencil stroke.",
    "warning": "",
    "support": "TESTING",
    "wiki_url": "",
    "tracker_url":
        "https://github.com/nepia11/blender-gpencil-stroke-normalizer/issues",
    "category": "Gpencil",
}


class NP_GPN_OT_GPencilStrokeCountResampler(types.Operator):

    bl_idname = "gpencil.np_gpencil_stroke_count_resampler"
    bl_label = translation("Sampling strokes")
    bl_description = translation(
        "Sampling selection strokes by number of points")

    bl_options = {"REGISTER", "UNDO"}

    amount = props.IntProperty(
        name=translation("number of points"),
        default=100,
        min=1,
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
        "Match the maximum number of points "
        "for the same stroke between frames."
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
                    frame_number = (
                        state1["layers"][li]["frames"][fi]["frame_number"]
                    )
                    context.scene.frame_current = frame_number
                    for si, stroke in enumerate(frame.strokes):
                        stroke.select = True
                        stroke_count_resampler(
                            stroke, result_count=max_counts[si])
                        stroke.select = False

        # context.scene.frame_current = select_state.state["frame_current"]

        select_state.load()

        self.report({"INFO"}, "done stroke resample")

        return {"FINISHED"}


class NP_GPN_OT_RainbowStrokes(types.Operator):
    """
    timer eventについて参照
    https://colorful-pico.net/introduction-to-addon-development-in-blender/2.8/html/chapter_03/03_Handle_Timer_Event.html
    """

    bl_idname = "gpencil.np_rainbow_strokes"
    bl_label = "rainbow strokes"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    # タイマのハンドラ
    __timer = None

    rs = rainbow_strokes.RainbowStrokes()

    @classmethod
    def is_running(cls):
        # モーダルモード中はTrue
        return True if cls.__timer else False

    def __handle_add(self, context):
        if not self.is_running():
            # タイマを登録
            interval = 0.5
            NP_GPN_OT_RainbowStrokes.__timer = \
                context.window_manager.event_timer_add(
                    interval, window=context.window
                )
            # モーダルモードへの移行
            context.window_manager.modal_handler_add(self)

    def __handle_remove(self, context):
        if self.is_running():
            # タイマの登録を解除
            context.window_manager.event_timer_remove(
                NP_GPN_OT_RainbowStrokes.__timer)
            NP_GPN_OT_RainbowStrokes.__timer = None

    def modal(self, context, event):
        # op_cls = NP_GPN_OT_RainbowStrokes

        # エリアを再描画
        if context.area:
            context.area.tag_redraw()

        # パネル [日時を表示] のボタン [終了] を押したときに、モーダルモードを終了
        if not self.is_running():
            return {'FINISHED'}

        # タイマーイベントが来た時にする処理
        if event.type == 'TIMER':
            try:
                self.rs.update(context)
            except AttributeError:
                # モーダルモードを終了
                self.__handle_remove(context)
                return {'FINISHED'}

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        op_cls = NP_GPN_OT_RainbowStrokes

        if context.area.type == 'VIEW_3D':
            # [開始] ボタンが押された時の処理
            if not op_cls.is_running():
                # 何らかの処理

                # モーダルモードを開始
                self.__handle_add(context)
                return {'RUNNING_MODAL'}
            # [終了] ボタンが押された時の処理
            else:
                # モーダルモードを終了
                self.__handle_remove(context)
                return {'FINISHED'}
        else:
            return {'CANCELLED'}

    # メニューを実行したときに呼ばれるメソッド
    # def execute(self, context):
    #     # context.active_object.data = data.grease_pencils['Stroke']
    #     gp_data = context.active_object.data

    #     for layer in gp_data.layers:
    #         for frame in layer.frames:
    #             rainbow_strokes.rainbow_strokes(frame.strokes)

    #     self.report({"INFO"}, "rainbow strokes!")

    #     return {"FINISHED"}


class NP_GPN_PT_GPencilNormalizer(bpy.types.Panel):

    bl_label = "GPencil Normalizer"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "GPSN"
    # bl_context = "objectmode"

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
        layout.label(text=translation("rainbow strokes")+":")

        # [開始] / [終了] ボタンを追加
        if not NP_GPN_OT_RainbowStrokes.is_running():
            layout.operator(
                NP_GPN_OT_RainbowStrokes.bl_idname,
                text="start", icon='PLAY')
        else:
            layout.operator(
                NP_GPN_OT_RainbowStrokes.bl_idname,
                text="stop", icon='PAUSE')
        # ストロークサンプリング機能
        layout.label(text=translation("Normalize strokes")+":")
        layout.operator(
            NP_GPN_OT_GPencilStrokeCountResampler.bl_idname,
            text=translation("Sampling strokes")
        )
        layout.operator(
            NP_GPN_OT_GPencilStrokeCountNormalizer.bl_idname,
            text=translation("Normalize strokes"))


# def menu_fn(self, context):
#     self.layout.separator()
#     self.layout.operator(
#         NP_GPN_OT_GPencilStrokeCountResampler.bl_idname,
#         text=translation("Sampling strokes")
#     )
#     self.layout.operator(
#         NP_GPN_OT_GPencilStrokeCountNormalizer.bl_idname,
#         text=translation("Normalize strokes")
#     )
#     self.layout.operator(NP_GPN_OT_RainbowStrokes.bl_idname)


classes = [
    NP_GPN_OT_GPencilStrokeCountResampler,
    NP_GPN_OT_GPencilStrokeCountNormalizer,
    NP_GPN_OT_RainbowStrokes,
    NP_GPN_PT_GPencilNormalizer,
]


def register():
    for c in classes:
        bpy.utils.register_class(c)
    # types.VIEW3D_PT_tools_grease_pencil_interpolate.append(menu_fn)

    # 翻訳辞書の登録
    bpy.app.translations.register(__name__, translation_dict)


def unregister():
    # 翻訳辞書の登録解除
    bpy.app.translations.unregister(__name__)
    # types.VIEW3D_PT_tools_grease_pencil_interpolate.remove(menu_fn)
    for c in classes:
        bpy.utils.unregister_class(c)


if __name__ == "__main__":
    register()

if "bpy" in locals():
    import imp
    imp.reload(translations)
    imp.reload(gpencil_normalizer)
else:
    from . import translations
    from . import gpencil_normalizer


import bpy
from bpy import props, types
# from . import translations
# from . import gpencil_normalizer


# 翻訳用の辞書
GpSelectState = gpencil_normalizer.GpSelectState
stroke_count_resampler = gpencil_normalizer.stroke_count_resampler
translation_dict = translations.translation_dict

translation = bpy.app.translations.pgettext

# アドオン用のいろいろ
bl_info = {
    "name": "Blender Gpencil Stroke Normalizer",
    "author": "nepia",
    "version": (0, 4, 0),
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

    amount: props.IntProperty(
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


def menu_fn(self, context):
    self.layout.separator()
    self.layout.operator(
        NP_GPN_OT_GPencilStrokeCountResampler.bl_idname,
        text=translation("Sampling strokes")
        )
    self.layout.operator(
        NP_GPN_OT_GPencilStrokeCountNormalizer.bl_idname,
        text=translation("Normalize strokes")
        )


classes = [
    NP_GPN_OT_GPencilStrokeCountResampler,
    NP_GPN_OT_GPencilStrokeCountNormalizer,
]


def register():
    for c in classes:
        bpy.utils.register_class(c)
    # types.VIEW3D_MT_gpencil_edit_context_menu.append(menu_fn)
    types.VIEW3D_PT_tools_grease_pencil_interpolate.append(menu_fn)

    # 翻訳辞書の登録
    bpy.app.translations.register(__name__, translation_dict)


def unregister():
    # 翻訳辞書の登録解除
    bpy.app.translations.unregister(__name__)

    # types.VIEW3D_MT_gpencil_edit_context_menu.remove(menu_fn)
    types.VIEW3D_PT_tools_grease_pencil_interpolate.remove(menu_fn)
    for c in classes:
        bpy.utils.unregister_class(c)


if __name__ == "__main__":
    register()

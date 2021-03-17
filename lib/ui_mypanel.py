import bpy
from . import ops_gpencil_normalizer
from . import ops_rainbow_strokes

NP_GPN_OT_RainbowStrokes = ops_rainbow_strokes.NP_GPN_OT_RainbowStrokes
NP_GPN_OT_GPencilStrokeCountResampler = (
    ops_gpencil_normalizer.NP_GPN_OT_GPencilStrokeCountResampler
)
NP_GPN_OT_GPencilStrokeCountNormalizer = (
    ops_gpencil_normalizer.NP_GPN_OT_GPencilStrokeCountNormalizer
)
translation = bpy.app.translations.pgettext


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

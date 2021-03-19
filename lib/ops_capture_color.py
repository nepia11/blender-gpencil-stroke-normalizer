import bpy
import bgl
from logging import getLogger

logger = getLogger(__name__)

translation = bpy.app.translations.pgettext


def capture_under_cursor(buffer, mouse_x=0, mouse_y=0, type_flg="i") -> list:
    """
    フラットなrgba(float)のlistを返す
    """
    # GL_FLOATでバッファ作って読むと馬鹿みたいに重いのでGL_BYTE,GL_UNSIGNED_BYTEになってる
    bgl.glReadBuffer(bgl.GL_FRONT)
    bgl.glReadPixels(
        mouse_x,
        mouse_y,
        1,
        1,
        bgl.GL_RGBA,
        bgl.GL_UNSIGNED_BYTE,
        buffer,
    )
    if type_flg == "i":
        return [value for value in buffer]
    elif type_flg == "f":
        return [value / 255 for value in buffer]


def bytes_to_color_code(color: list) -> str:
    """ RGBAのイテラブルを投げるとカラーコードを返してくれる"""
    c = color
    return f"#{c[0]:x}{c[1]:x}{c[2]:x}{c[3]:x}"


def create_buffer(src_width: int = 1, src_height: int = 1):
    buffer = bgl.Buffer(bgl.GL_BYTE, src_width * src_height * 4)
    return buffer


class TEMPLATE_OT_CaptureColor(bpy.types.Operator):
    """ カーソル下の色を取得するやつ """

    bl_idname = "template.capture_color"
    bl_label = translation("my operator")
    bl_description = "operator description"
    bl_options = {"REGISTER", "UNDO"}

    buffer = create_buffer()
    keymaps = []
    # イベントを受け取りたいときはexecuteの代わりにinvokeが使える

    def invoke(self, context, event):
        color = capture_under_cursor(self.buffer, event.mouse_x, event.mouse_y, "f")
        context.tool_settings.gpencil_paint.brush.color = color[:3]
        # brushes = [b for b in bpy.data.brushes]
        # for b in brushes:
        #     b.color = (color[:3])
        # logging
        logger.debug(color)
        # infoにメッセージを通知
        self.report({"INFO"}, f"{color}")
        # 正常終了ステータスを返す
        return {"FINISHED"}

    @classmethod
    def register(cls):
        wm = bpy.context.window_manager
        kc = wm.keyconfigs.addon
        if kc:
            # [3Dビューポート] スペースのショートカットキーとして登録
            km = kc.keymaps.new(name="3D View", space_type="VIEW_3D")
            # ショートカットキーの登録
            kmi = km.keymap_items.new(
                idname=cls.bl_idname,
                type="P",
                value="PRESS",
                shift=False,
                ctrl=False,
                alt=False,
            )
            # ショートカットキー一覧に登録
            cls.keymaps.append((km, kmi))

    @classmethod
    def unregister(cls):
        for km, kmi in cls.keymaps:
            # ショートカットキーの登録解除
            km.keymap_items.remove(kmi)
        # ショートカットキー一覧をクリア
        cls.keymaps.clear()


class TEMPLATE_PT_CursorColor(bpy.types.Panel):
    bl_label = "CursorColor"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout
        layout.operator(TEMPLATE_OT_CaptureColor.bl_idname)

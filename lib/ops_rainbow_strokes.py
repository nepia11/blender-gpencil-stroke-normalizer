import bpy
import colorsys
import numpy as np
from . import util

logger = util.getLogger(__name__)
logger.debug("hello")


def rainbow(index: int) -> [float, float, float, float]:
    h, s, v, a = 1.0, 0.2, 1.0, 1.0
    s_collection = (1.0, 0.8, 0.6, 0.4)

    # 定数　hueの1回転と1ステップに何度回転するかを定義
    ROTATION = 360
    STEP = 40
    step = index * STEP
    rot = step // ROTATION
    h = step / ROTATION % 1
    s = s_collection[rot % len(s_collection)]
    rgba = colorsys.hsv_to_rgb(h, s, v) + (a,)
    # 謎の演算誤差が出るのでfloat32にに変換してから比較
    # もしかしてpythonのfloatってdouble?
    color = np.array(rgba, dtype="float32").tolist()
    return color


def colorize_stroke(
    stroke: bpy.types.GPencilStroke, index: int, visible_start: bool = True
):
    """
    参照方法メモ \n
    lines.frames[0].strokes[0].points[0].vertex_color=(1,0,0,1)
    """
    color = rainbow(index)
    points = stroke.points
    stroke_len = len(points)
    n = -1

    if stroke_len == 1:
        n = 0
        visible_start = False

    # すでに同色に変更済みのストロークを無視する
    test_value = list(points[n].vertex_color)
    # logger.debug(f"testvalue:{test_value}, color:{test_color}")
    if test_value == color:
        return 0

    for point in points:
        point.vertex_color = color

    if visible_start:
        points[0].vertex_color = [0, 0, 0, 1]

    return 1


def rainbow_strokes(strokes: bpy.types.GPencilStrokes):
    """
    strokesのインデックスに合せて頂点カラーを設定します
    """
    n = [colorize_stroke(stroke, i, True) for i, stroke in enumerate(strokes)]
    return n
    # logger.debug(f"update:{sum(n)}")
    # logger.debug(rainbow.cache_info())


def get_stroke_vertex_color(stroke: bpy.types.GPencilStroke) -> list:
    return [tuple(point.vertex_color) for point in stroke.points]


def get_all_strokes_vertex_color(strokes: bpy.types.GPencilStrokes) -> list:
    return [get_stroke_vertex_color(stroke) for stroke in strokes]


class RainbowStrokeObject:
    def init(self, context):
        orig_mode: str = context.mode
        if orig_mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        # もとのオブジェクトを取得、複製
        orig_obj = context.active_object
        new_name = orig_obj.name + ".gpnRsPrev"
        rs_obj = util.object_duplicate_helper(orig_obj, new_name)
        # ロックしておく
        rs_obj.hide_select = True
        rs_obj.show_in_front = True

        self.colorize(rs_obj.data)
        self.orig_obj_name = orig_obj.name
        # https://docs.blender.org/api/current/info_gotcha.html#undo-redo
        # 名前で参照するより直接参照を持ったほうが負荷が少ないんだろうけど、undoした時にバグるのでしょうがなく名前で参照するようにしている
        self.rs_obj_name = rs_obj.name
        context.view_layer.objects.active = orig_obj

        bpy.ops.object.mode_set(mode=orig_mode)

    def update(self, opacity=0.5, emphasize_index=0, emphasize_color=(0, 0, 0, 0)):
        # old_data = self.rs_obj.data
        old_data = bpy.data.objects[self.rs_obj_name].data
        old_data.name = "trash"
        # new_data = self.orig_obj.data.copy()
        new_data = bpy.data.objects[self.orig_obj_name].data.copy()
        new_data.name = self.rs_obj_name
        for layer in new_data.layers:
            layer.opacity *= opacity
        self.colorize(new_data, emphasize_index, emphasize_color)
        # self.rs_obj.data = new_data
        bpy.data.objects[self.rs_obj_name].data = new_data
        bpy.data.batch_remove([old_data.id_data])

    def clear(self):
        try:
            logger.debug("clear rso")
            bpy.ops.object.mode_set(mode="OBJECT")
            logger.debug("clean id_data")
            remove_obj = bpy.data.objects[self.rs_obj_name]
            bpy.data.batch_remove([remove_obj.data])
            logger.debug("clean id_data success")
            bpy.ops.object.delete({"selected_objects": [remove_obj]})
            logger.debug("clean object success")
            pass
        except (KeyError):
            #  見つからないならしょうがない。それ以外のときは例外を見たい
            pass
        del self.orig_obj_name
        del self.rs_obj_name

    @staticmethod
    def colorize(
        gp_data: bpy.types.GreasePencil, emphasize_index=0, emphasize_color=(0, 0, 0, 0)
    ):
        for layer in gp_data.layers:
            for frame in layer.frames:
                rainbow_strokes(frame.strokes)
                if len(frame.strokes) - 1 > emphasize_index:
                    points = frame.strokes[emphasize_index].points
                    color = emphasize_color
                    for point in points:
                        point.vertex_color = color


class NP_GPN_OT_RainbowStrokes(bpy.types.Operator):
    # timer eventについて参照
    # https://colorful-pico.net/introduction-to-addon-development-in-blender/2.8/html/chapter_03/03_Handle_Timer_Event.html

    bl_idname = "gpencil.np_rainbow_strokes"
    bl_label = "rainbow strokes"
    bl_description = ""
    # bl_options = {"REGISTER", "UNDO"}

    # タイマのハンドラ
    __timer = None

    interval = 0.2

    __props = []

    rso = RainbowStrokeObject()

    @classmethod
    def register(cls):
        """ registerする時にやっときたい処理 あったら勝手に呼ばれるらしい"""
        scene = bpy.types.Scene
        append = cls.__props.append

        scene.gpn_rainbowStroke_opacity = bpy.props.FloatProperty(
            name="rainbow_opacity",
            description="rainbowStrokeの透明度",
            default=0.75,
            min=0.0,
            max=1.0,
        )
        append(scene.gpn_rainbowStroke_opacity)

        scene.gpn_rainbowStroke_emphasize_index = bpy.props.IntProperty(
            name="Emphasize index", description="強調するストロークのインデックス", min=0
        )
        append(scene.gpn_rainbowStroke_emphasize_index)

        scene.gpn_ranbowStroke_emphasize_color = bpy.props.FloatVectorProperty(
            name="Emphasize color",
            description="強調色",
            subtype="COLOR",
            default=(1.0, 1.0, 1.0, 1.0),
            min=0.0,
            max=1.0,
            size=4,
        )
        append(scene.gpn_ranbowStroke_emphasize_color)

    @classmethod
    def unregister(cls):
        """ unregisterする時にやっときたい処理 あったら勝手に呼ばれるらしい"""
        for prop in cls.__props:
            del prop
        cls.__props = []

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
        emphasize_color = context.scene.gpn_ranbowStroke_emphasize_color
        opacity = context.scene.gpn_rainbowStroke_opacity
        # タイマーイベントが来た時にする処理
        if event.type == "TIMER":
            try:
                # logger.debug("try modal")qq
                self.rso.update(
                    opacity=opacity,
                    emphasize_index=emphasize_index,
                    emphasize_color=emphasize_color,
                )
            except (KeyError) as e:
                # モーダルモードを終了
                logger.exception(f"{e}")
                self.__handle_remove(context)
                return {"FINISHED"}
                # return {'CANCELLED'}

        return {"PASS_THROUGH"}

    def invoke(self, context, event):
        op_cls = NP_GPN_OT_RainbowStrokes
        logger.debug("invoke rainbowstrokes")
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

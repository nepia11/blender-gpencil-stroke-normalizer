import random
import string
import bpy


def random_name(n: int) -> string:
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))


def gp_licker(
        gp_data: bpy.types.GreasePencil,
        func,
        state={}):

    if type(gp_data) is not bpy.types.GreasePencil:
        print("not gpencil")
        return 1

    for li, layer in enumerate(gp_data.layers):
        func(state["layers"][li], layer, "layer")
        for fi, frame in enumerate(layer.frames):
            func(state["layers"][li]["frames"][fi], frame, "frame")
            for si, stroke in enumerate(frame.strokes):
                func(
                    state["layers"][li]["frames"][fi]["strokes"][si],
                    stroke,
                    "stroke")

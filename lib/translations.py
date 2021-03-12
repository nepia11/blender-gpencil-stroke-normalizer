keys = [
    "Sampling selection strokes by number of points",
    "Sampling strokes",
    "number of points",
    "Normalize strokes",
    "Match the maximum number of points for the same stroke between frames.",
    "Provides the ability to arbitrarily adjust the number of points "
    "in a gpencil stroke.",
    "rainbow strokes",
    "Sorting strokes",
    "Emphasize index",
]

jp = [
    "選択ストロークをポイント数でサンプリングする",
    "ストロークをサンプリング",
    "ポイント数",
    "ストロークを正規化",
    "フレーム間、同一ストロークのポイント数を最大値に合わせる",
    "gpencilのストロークのポイント数を任意に調整する機能を提供します。",
    "レインボーストローク",
    "ストロークの並び替え",
    "強調するインデックス",
]

translation_dict = {
    "en_US": {("*", key): key for key in keys},
    "ja_JP": {("*", key): j for key, j in zip(keys, jp)},
}

# debug
# import pprint
# pprint.pprint(translation_dict)

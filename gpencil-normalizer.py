import bpy
import numpy as np

#　2つのベクトルから長さ(ノルム?)を求める。わからなくなるのでラップしてる
def calc_vector3_length(a,b):
    vec = np.array(b - a)
    return np.linalg.norm(vec)

#  ストロークの長さとポイント数を計算して返す
def calc_stroke_length_and_point(gp_stroke):
    vectors = [p.co for p in gp_stroke.points]
    point_count = len(vectors)
    norms = np.zeros(point_count)
    for index in range(point_count-1):
        vec_length=calc_vector3_length(vectors[index],vectors[index+1])
        norms[index] = vec_length
        
    return np.sum(norms),point_count

#　複数フレーム内の１ストロークの長さとポイント最大数を返す
def calc_frames_stroke_length_and_max_count(gp_frames,strokes_index=0):
    gp_stroke = gp_frames[0].strokes[strokes_index]
    point_max_count = 0
    lengths = [0] * len(gp_frames)
    for i,frame in enumerate(gp_frames):
        stroke_length,count = calc_stroke_length_and_point(frame.strokes[strokes_index])
        lengths[i] = stroke_length
        if count > point_max_count:
            point_max_count = count
        
    return lengths,point_max_count
    
def main():
#    ここにグリースペンシルのストロークのポイントが入っている
#    bpy.data.grease_pencils['Stroke'].layers["Lines"].frames[0].strokes[0].points
    gp_frames = bpy.data.grease_pencils['Stroke'].layers["Lines"].frames
    
    lengths,count = calc_frames_stroke_length_and_max_count(gp_frames,0)
    print(lengths)
#    segment_length = total_length / point_count 
    for i in range(len(gp_frames)):
#        ポイント最大数に合わせてストロークをリサンプルする
        resample_length = lengths[i] / count
#        bpy.ops.gpencil.stroke_sample()でストロークをリサンプルできる
#        どうやって任意のストロークを指定するんだ・・・？
        bpy.ops.gpencil.stroke_sample()
        
main()

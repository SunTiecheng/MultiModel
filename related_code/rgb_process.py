import argparse
import numpy as np
from plyfile import PlyData, PlyElement
from utils.sh_utils import SH2RGB


def rgb_process(input_path, output_path):

    ply_data = PlyData.read(f"{input_path}/point_cloud.ply")

    vertex_data = ply_data['vertex'].data

    f_dc_0 = vertex_data['f_dc_0']
    f_dc_1 = vertex_data['f_dc_1']
    f_dc_2 = vertex_data['f_dc_2']
    sh = np.vstack((f_dc_0, f_dc_1, f_dc_2)).T
    colors = SH2RGB(sh)
    colors = (colors + 0.5) * (255.0 / 2.0)

    new_vertex_dtype = vertex_data.dtype.descr + [('red', 'u1'), ('green', 'u1'), ('blue', 'u1')]

    new_vertex_data = np.empty(len(vertex_data), dtype=new_vertex_dtype)

    for name in vertex_data.dtype.names:
        new_vertex_data[name] = vertex_data[name]

    new_vertex_data['red'] = colors[:, 0]
    new_vertex_data['green'] = colors[:, 1]
    new_vertex_data['blue'] = colors[:, 2]

    new_vertex_element = PlyElement.describe(new_vertex_data, 'vertex')

    elements = [element for element in ply_data.elements if element.name != 'vertex']
    elements.append(new_vertex_element)

    new_ply_data = PlyData(elements, text=ply_data.text)

    new_ply_data.write(f"{output_path}/colored_points.ply")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="rgb process.")
    parser.add_argument('-i', '--input_path', type=str, default= './output/iteration_60000', help="Path to the input video file.")
    parser.add_argument('-o', '--output_path', type=str, default= './output/iteration_60000', help="Folder to save the extracted frames.")

    args = parser.parse_args()

    rgb_process(args.input_path, args.output_path)

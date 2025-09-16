from sugar_utils.spherical_harmonics import SH2RGB
from sugar_scene.gs_model import GaussianSplattingWrapper
import numpy as np
from plyfile import PlyData

nerfmodel = GaussianSplattingWrapper(
        source_path='./data',
        output_path='./data/output',
        iteration_to_load=7000,
        load_gt_images=False,
        eval_split=True,
        eval_split_interval=8,
        )
colors = SH2RGB(nerfmodel.gaussians.get_features[:, 0].detach().float().cuda())
colors_unnorm = (colors + 0.5) * (255.0 / 2.0)
print("括号中的东西", nerfmodel.gaussians.get_features[:, 0].detach().float().cuda())
print("colors", colors)
print("len_colors", len(colors))
print("colors_unnorm", colors_unnorm)

print("==================================================")

# 读取 PLY 文件
ply_data = PlyData.read('./data/output/point_cloud/iteration_7000/point_cloud.ply')

# 提取顶点数据
vertex_data = ply_data['vertex'].data

# 提取 f_dc_0, f_dc_1, f_dc_2 属性
f_dc_0 = vertex_data['f_dc_0']
f_dc_1 = vertex_data['f_dc_1']
f_dc_2 = vertex_data['f_dc_2']

# 组合成所需的数组
combined_data = np.vstack((f_dc_0, f_dc_1, f_dc_2)).T

# 打印或保存结果
print(combined_data)
# From Videos to Multi-Modal Dataset

Author


# Introduction

In recent years, 3D generation methods in Artificial Intelligence Generated Content (AIGC) is popular, such as text-to-3D and image-to-3D. These methods require large-scale multi-modal datasets with the 3D modal and text or image modal aligned. However, we still lack a large number of 3D models of real scenes for training when it comes to generating realistic 3D models. To address this problem, we propose a multi-modal data construction system that only takes a single real massive video modality as input. The output multi-modal data includes aligned text, image, and 3D models. The 3D modality further includes mesh, 3D Gaussian splatting representation and point cloud.
For the text in the multi-modal dataset, we use images as input and generate the text using image captioning method. To construct the 3D models, we first generate 3D Gaussian splatting representation via 3D reconstruction algorithms, then convert them into other formats, and apply masks to remove background regions from the reconstructed models. Additionally, to check the quality of the 3D models included in the dataset, we employ a quantitative evaluation method to verify the reconstruction accuracy. Experimental results show that our method can rapidly generate demonstrate that our method provides effectively provides high-quality data. The quantitative evaluations further confirm that the 3D models in our dataset are both realistic and of high fidelity. The data provided by our multi-modal dataset can better help address current challenges in 3D generation, particularly the shortage of realistic textures and high-quality 3D models in existing multi-modal datasets.

## Environment

准备搭建环境：

    conda env create --file environment.yml

准备完整代码：

    cd From_Videos_to_Multui-Modal_Dataset
    git clone https://github.com/hbb1/2d-gaussian-splatting.git
    git clone https://github.com/joeyz0z/MeaCap.git
    git clone https://github.com/hkchengrex/XMem.git

## File Location
所有视频文件放在/From_Videos_to_Multui-Modal_Dataset/video
输出的模型文件放在/2dgs_gen/

## Construction of Multi-modal Dataset

获取物体主体网格模型：

    bash run_2dgs.sh
    bash run_bg.sh

 - 运行run_2dgs.sh时报错中断时，运行`bash stop_and_go.sh`
 - 如已经完成colmap计算，将文件夹移入/colmap_done/下，并命名。再运行：`load_from_colmap_done.sh`

获取具有颜色的点云模型：

    python rgb_process.py -i 输入目录 -o 输出目录

获取mask和图像描述，请参照：[mask](https://github.com/hkchengrex/XMem)      [图像描述](https://github.com/joeyz0z/MeaCap?tab=readme-ov-file)

## Quantitative Evaluation

一、使用Blender打开trajectory.blender生成CAD模型多视角图像（输出路径需重新定义）。
输出的图片放入/From_Videos_to_Multi-Modal_Dataset/colmap_test/images/下
输出的camera_poses.txt放到/From_Videos_to_Multui-Modal_Dataset/下，运行：

    python generate_colmap_data.py 

将/From_Videos_to_Multui-Modal_Dataset/下生成的images.txt放入/From_Videos_to_Multui-Modal_Dataset/colmap_test/created/sparse下
二、Colmap重建

    colmap feature_extractor --database_path database.db --image_path images
    python fix_database.py
    colmap exhaustive_matcher --database_path database.db
    colmap point_triangulator --database_path database.db --image_path images --input_path created/sparse --output_path triangulated/sparse

（如需进行Colmap稠密重建）

    colmap image_undistorter --image_path images --input_path triangulated/sparse --output_path dense
	colmap patch_match_stereo --workspace_path dense
	colmap stereo_fusion --workspace_path dense --output_path dense/fused.ply

参考链接：[参考1](https://blog.csdn.net/qq_38677322/article/details/126269726)  [参考2](https://www.cnblogs.com/li-minghao/p/11865794.html)
三、将/colmap_test/triangulated/sparse中的相机内外参替换到三维重建算法的相机参数，并重建
四、均匀采样到与重建点云的分辨率相同

    python uniformed_sample.py
   
   详细调整参数请查看代码进行修改
 五、将均匀采样的点云与重建点云复制到/myutils/下，运行:（在ubuntu下可以运行，但在windows下可能无法运行）
 
    python eval.py

其中请在eval.py中修改需要进行评价的点云，cloudA为采样点云，cloudB为重建点云。


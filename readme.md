# From Videos to Multi-Modal Dataset

Author:
- Zijun Zhou[City University of Macau]
- Tiecheng Sun*[Great Wall Motor Company Limited]
- Yingzhe Luo*[City University of Macau]

*Corresponding author


# Introduction

In recent years, 3D generation methods in Artificial Intelligence Generated Content (AIGC) is popular, such as text-to-3D and image-to-3D. These methods require large-scale multi-modal datasets with the 3D modal and text or image modal aligned. However, we still lack a large number of 3D models of real scenes for training when it comes to generating realistic 3D models. To address this problem, we propose a multi-modal data construction system that only takes a single real massive video modality as input. The output multi-modal data includes aligned text, image, and 3D models. The 3D modality further includes mesh, 3D Gaussian splatting representation and point cloud.
For the text in the multi-modal dataset, we use images as input and generate the text using image captioning method. To construct the 3D models, we first generate 3D Gaussian splatting representation via 3D reconstruction algorithms, then convert them into other formats, and apply masks to remove background regions from the reconstructed models. Additionally, to check the quality of the 3D models included in the dataset, we employ a quantitative evaluation method to verify the reconstruction accuracy. Experimental results show that our method can rapidly generate demonstrate that our method provides effectively provides high-quality data. The quantitative evaluations further confirm that the 3D models in our dataset are both realistic and of high fidelity. The data provided by our multi-modal dataset can better help address current challenges in 3D generation, particularly the shortage of realistic textures and high-quality 3D models in existing multi-modal datasets.

## Multi-modal Dataset
We have make the multi-modal dataset publicly available. You can download the multi-modal datast by this [link](https://pan.baidu.com/s/1JSAnr_3G9Y3_8xkViZLLGA?pwd=data).

In order to further expand our multi-modal dataset, we have publicly released our multi-modal dataset and the construction code on the homepage of the project. We encouage more scholars and creators enrich our multi-modal dataset together based on our released code. If scholars or creators use our construction tools to create new multi-modal data, they can provide it to us through the e-mail. We will package, classify, and integrate the data and add it to our multi-modal dataset.



## Installation


	#download
	git clone https://github.com/SunTiecheng/MultiModel.git --recursive
	#create new environment
    cd MultiModel
	conda env create --file environment.yml
    git clone https://github.com/hbb1/2d-gaussian-splatting.git
    git clone https://github.com/joeyz0z/MeaCap.git
    git clone https://github.com/hkchengrex/XMem.git

## File Location
Put the video files into /From_Videos_to_Multui-Modal_Dataset/video

The outputs of 3D objects are located in /2dgs_gen/

## Construction of Multi-modal Dataset



    bash run_2dgs.sh
    bash run_bg.sh

 - When running run_2dgs.sh and encountering an error interrupt, please run:`bash stop_and_go.sh`
 - If you have already finish the estimation of COLMAP, please put the whole folder into /colmap_done/ , then run：`load_from_colmap_done.sh`

To get the point cloud with RGB color：

    python rgb_process.py -i INPUT_FOLDER -o OUTPUT_FOLDER

To extract masks from images and export image caption, please follow the guidance of XMem: [mask](https://github.com/hkchengrex/XMem) and Meacap: [image caption](https://github.com/joeyz0z/MeaCap?tab=readme-ov-file)

## Quantitative Evaluation

1、Render mluti-view images of CAD model based on the **trajectory.blender** in the project folder through Blender API.
	*Notice: The output path need to be changed to yours.*

Then, put the **output images** into folder: 
**/From_Videos_to_Multi-Modal_Dataset/colmap_test/images/**
and the output **camera_poses.txt** need to be put into folder: **/From_Videos_to_Multui-Modal_Dataset/**

run:

    python generate_colmap_data.py 

Put the **images.tx**t in the folder **/From_Videos_to_Multui-Modal_Dataset/** into folder **/From_Videos_to_Multui-Modal_Dataset/colmap_test/created/sparse**

2、Reconstruction by COLMAP

    colmap feature_extractor --database_path database.db --image_path images
    python fix_database.py
    colmap exhaustive_matcher --database_path database.db
    colmap point_triangulator --database_path database.db --image_path images --input_path created/sparse --output_path triangulated/sparse

（If you want to make a dense reconstruction with COLMAP, please go on）

    colmap image_undistorter --image_path images --input_path triangulated/sparse --output_path dense
	colmap patch_match_stereo --workspace_path dense
	colmap stereo_fusion --workspace_path dense --output_path dense/fused.ply

Detailed guidance：[Reference1](https://blog.csdn.net/qq_38677322/article/details/126269726)  [Reference2](https://www.cnblogs.com/li-minghao/p/11865794.html)

3、Replace the camera intrinsic and extrinsic parameters in **/colmap_test/regularized/sparse** to 3D reconstruction algorithm. It might be the folder **/data/sparse/0/**.
Then, use your 3D reconstruction algorithm to reconstruct.

4、Make the resolution of CAD model same as the reconstructed point cloud through uniform sampling. Run:

    python uniformed_sample.py
   
   *Notice: If you want to change the detialed parameters, please review the code file.*
   
5、Put the uniform sampling point cloud and the reconstructed point cloud into folder **/myutils/**, and run: 
(This code can not be runned in Windows currently.)
 
    python eval.py

*Notice: Please change the name of the point clouds which need to be evaluated. cloudA represents the sampled point cloud, cloudB represents the reconstructed point cloud.*


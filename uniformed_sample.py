import logging
import open3d as o3d
import numpy as np
import pandas as pd
import argparse
import os
from os.path import join, split, splitext
from os import makedirs
from glob import glob
from tqdm import tqdm
from multiprocessing import Pool
import functools

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
    datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger(__name__)


def process(path, args):
    ori_path = join(args.source, path)
    target_path, _ = splitext(join(args.dest, path))
    target_path += args.target_extension
    target_folder, _ = split(target_path)
    makedirs(target_folder, exist_ok=True)

    logger.debug(f"Processing mesh {ori_path}")

    # Load the mesh using open3d
    mesh = o3d.io.read_triangle_mesh(ori_path)

    if not mesh.has_triangle_normals():
        mesh.compute_triangle_normals()
    if not mesh.has_vertex_normals():
        mesh.compute_vertex_normals()

    # Sample points from the mesh
    pcd = mesh.sample_points_uniformly(number_of_points=args.n_samples)

    # Extract sampled points and normals
    points = np.asarray(pcd.points)
    normals = np.asarray(pcd.normals)

    # Create a DataFrame to store points and normals
    pc_data = pd.DataFrame(data={
        'x': points[:, 0],
        'y': points[:, 1],
        'z': points[:, 2],
        'nx': normals[:, 0],
        'ny': normals[:, 1],
        'nz': normals[:, 2]
    })

    # Save to target path as a point cloud
    o3d_pcd = o3d.geometry.PointCloud()
    o3d_pcd.points = o3d.utility.Vector3dVector(pc_data[['x', 'y', 'z']].values)
    o3d_pcd.normals = o3d.utility.Vector3dVector(pc_data[['nx', 'ny', 'nz']].values)

    logger.debug(f"Writing point cloud to {target_path}")
    o3d.io.write_point_cloud(target_path, o3d_pcd)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='ds_mesh_to_pc.py',
        description='Converts a folder containing meshes to point clouds with normals',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument('source', help='Source directory')
    parser.add_argument('dest', help='Destination directory')
    parser.add_argument('--vg_size', type=int, help='Voxel Grid resolution for x, y, z dimensions', default=64)
    parser.add_argument('--n_samples', type=int, help='Number of samples', default=500000)
    parser.add_argument('--source_extension', help='Mesh files extension', default='.ply')
    parser.add_argument('--target_extension', help='Point cloud extension', default='.ply')

    args = parser.parse_args()

    assert os.path.exists(args.source), f'{args.source} does not exist'
    assert not os.path.exists(args.dest), f'{args.dest} already exists'
    assert args.vg_size > 0, f'vg_size must be positive'
    assert args.n_samples > 0, f'n_samples must be positive'

    paths = glob(join(args.source, '**', f'*{args.source_extension}'), recursive=True)
    files = [x[len(args.source) + 1:] for x in paths]
    files_len = len(files)
    assert files_len > 0
    logger.info(f'Found {files_len} models in {args.source}')

    with Pool() as p:
        process_f = functools.partial(process, args=args)
        list(tqdm(p.imap(process_f, files), total=files_len))

    logger.info(f'{files_len} models written to {args.dest}')

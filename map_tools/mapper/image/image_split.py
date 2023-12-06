import os.path
from pathlib import Path

import cv2

from mapper.gdal import gdal_tool


def _structure_image_info(x_offset: int, y_offset: int, x_size: int, y_size: int, image_path: str) -> list[dict]:
    """
    Calculates the GPS coordinates for the given image.
    :return: a dict with GPS info for the image.
    """
    image_info = {}
    image_info["filename"] = Path(image_path).name
    image_info["file_path"] = image_path
    image_info["x_offset"] = x_offset
    image_info["y_offset"] = y_offset
    image_info["x_size"] = x_size
    image_info["y_size"] = y_size

    return image_info


def split_image(image_path: str, line_size:int) -> list[dict]:
    """
    Creates subpictures for a given image, preserving GeoTIFF data if any.
    :param: line_size: the max amount of pixels to have per dimension (both width and height) for each part.
    :return: a list of dicts with information about the split images.
    """
    out_images = []
    print(f"Creating subimages of max size {line_size}x{line_size}")

    # Open image and get dimensions.
    img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise Exception(f"Image {image_path} was not found.")
    ysize = img.shape[0]
    xsize = img.shape[1]
    print(f"Original map file is {xsize} x {ysize}")

    # Divide image in sub images of SUB_SIZE x SUB_SIZE.
    num_x_cuts = xsize // line_size
    num_y_cuts = ysize // line_size

    # If the image size is not dividable by SUB_SIZE, we will need another image of a smaller size.
    if num_x_cuts * line_size < xsize:
        num_x_cuts += 1
    if num_y_cuts * line_size < ysize:
        num_y_cuts += 1
    print(f"Number of x cuts: {num_x_cuts}, number of y cuts: {num_y_cuts}")

    # Create all images, looping over a mesh.
    x_offset = 0
    y_offset = 0
    for i in range(0, num_x_cuts):
        # Update the offset, and if we are at the end of a row, update the final size.
        x_offset = i * line_size
        curr_x_size = line_size
        if xsize - x_offset < line_size:
            curr_x_size = xsize - x_offset

        # Same with y.
        for j in range(0, num_y_cuts):
            y_offset = j * line_size
            curr_y_size = line_size
            if ysize - y_offset < line_size:
                curr_y_size = ysize - y_offset

            # Give a name to the new subimage.
            image_path_without_ext, ext = os.path.splitext(image_path)
            output_image_path = f"{image_path_without_ext}_{i}_{j}{ext}"

            # Create each sub image.
            gdal_tool.gdal_create_subpic(x_offset, y_offset, curr_x_size, curr_y_size, image_path, output_image_path)
            image_info = _structure_image_info(x_offset, y_offset, curr_x_size, curr_y_size, output_image_path)
            out_images.append(image_info)

    return out_images

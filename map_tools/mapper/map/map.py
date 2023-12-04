import os
import os.path

import cv2

from mapper.io import csv_generator
from mapper.gdal import gdal_tool

DEFAULT_SUB_SIZE = 1000
DEFAULT_OUTPUT_FORMAT = "png"
MAP_DATA_FILE = "map.csv"


def create_subpictures(image_name: str, line_size:int) -> list[str]:
    """Creates subpictures for a diven image."""
    out_images = []
    print(f"Creating subimages of max size {line_size}x{line_size}")

    # Open image and get dimensions.
    img = cv2.imread(image_name, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise Exception(f"Image {image_name} was not found.")
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
            image_name_without_ext, ext = os.path.splitext(image_name)
            output_image_name = f"{image_name_without_ext}_{i}_{j}{ext}"

            # Create each sub image.
            gdal_tool.gdal_create_subpic(x_offset, y_offset, curr_x_size, curr_y_size, image_name, output_image_name)
            out_images.append(output_image_name)

    return out_images


def create_map_data_file(output_folder: str, parts_gps_info: list[dict]):
    """Creates a CSV file with data about the parts of a map, from the provided base image and GPS info coordinates."""
    if len(parts_gps_info) > 0:
        print(f"Creating CSV with coordinates from each subimage.")
        map_csv_filename = os.path.join(output_folder, MAP_DATA_FILE)
        csv_generator.write_map_csv_coordinates(parts_gps_info, map_csv_filename)


def split_map(image_path: str, size: int = None, out_format: str = None) -> list[str]:
    """
    Splits a map into subimages of the given format.
    :return: A list with the paths of the subimages.
    """
    if size is None:
        size = DEFAULT_SUB_SIZE
    if out_format is None:
        out_format = DEFAULT_OUTPUT_FORMAT

    print(f"Starting image splitting for {image_path} to size {size}")
    out_images = create_subpictures(image_path, size)

    print(f"Converting image parts to {out_format}, if needed")
    for image in out_images:
        converted = gdal_tool.gdal_convert_to_format(image, out_format)
        if converted:
            print(f"Removing intermediate image {image}")
            os.remove(image)

    return out_images

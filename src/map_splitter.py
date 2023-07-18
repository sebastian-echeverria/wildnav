import subprocess
import os
import os.path
import argparse
import csv

import cv2

import geotiff


MAP_DATA_FILE = "map.csv"
SUB_SIZE = 1000


def create_subpictures(image_name: str, line_size:int = SUB_SIZE) -> list[str]:
    """Creates subpictures for a diven image."""
    out_images = []

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
            gdal_create_subpic(x_offset, y_offset, curr_x_size, curr_y_size, image_name, output_image_name)
            out_images.append(output_image_name)

    return out_images


def gdal_create_subpic(x: int, y: int, xsize: int, ysize:int, inname: str, outname: str):
    """Creates a subpicture of a given picture, starting at the given x,y, with the given sizes."""
    print(f"Executing GDAL translate: {x}, {y}, {xsize}, {ysize}, {inname}, {outname}")
    result = subprocess.run(["gdal_translate", "-srcwin", f"{x}", f"{y}", f"{xsize}", f"{ysize}", inname, outname])
    print(result)


def gdal_convert_to_png(image_name: str):
    """Converts the image to PNG."""
    image_name_without_ext, _ = os.path.splitext(image_name)
    outname = f"{image_name_without_ext}.png"
    print(f"Executing GDAL translate to convert to PNG: {image_name}, {outname}")
    result = subprocess.run(["gdal_translate", "-of", "PNG", image_name, outname, "--config", "GDAL_PAM_ENABLED", "NO"])
    print(result)    


def create_map_data_file(image_file: str, geotiff_images: list[str]):
    """Creates a CSV file with data about the parts of a map, from the provided GeoTIFF images."""
    image_path = os.path.dirname(image_file)
    filename = os.path.join(image_path, MAP_DATA_FILE)

    try:
        with open(filename, 'w', encoding='UTF8') as f:
            writer = csv.writer(f)

            # Headers first.
            header = ['Filename', 'Top_left_lat', 'Top_left_lon', 'Bottom_right_lat', 'Bottom_right_long']
            writer.writerow(header)

            # Now info for each image.
            for image in geotiff_images:
                image_name = os.path.basename(image)
                geotiff_image = geotiff.GeoTIFFImage(image)
                top_left_long, top_left_lat, _ = geotiff_image.top_left_coords()
                bottom_right_long, bottom_right_lat, _ = geotiff_image.bottom_right_coords()
                line = [image_name, str(top_left_lat), str(top_left_long), str(bottom_right_lat), str(bottom_right_long)]
                writer.writerow(line)
    except RuntimeError as ex:
        os.remove(filename)
        print(f"Could not generate metadata from images, they may not be GeoTIFF files: {ex}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("IMAGE_PATH")
    parser.add_argument("--no_tiff")
    args = parser.parse_args()
    image_path = args.IMAGE_PATH

    print(f"Starting image splitting for {image_path}")
    out_images = create_subpictures(image_path)

    print(f"Creating CSV with coordinates from each subimage, if they are GeoTIFF images.")
    if args.no_tiff is None:
        create_map_data_file(image_path, out_images)

    print(f"Converting images to PNG")
    for image in out_images:
        gdal_convert_to_png(image)

    print(f"Removing intermediate images")
    for image in out_images:
        os.remove(image)


if __name__ == "__main__":
    main()

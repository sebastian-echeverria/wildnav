import subprocess
import os
import os.path
import argparse

import cv2


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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("IMAGE_PATH")
    args = parser.parse_args()

    print(f"Starting image splitting for {args.IMAGE_PATH}")
    out_images = create_subpictures(args.IMAGE_PATH)

    print(f"Creating CSV with coordinates from each subimage.")
    for image in out_images:
        # TODO: function to create CSV with coordinates for each image.
        pass

    print(f"Converting images to PNG")
    for image in out_images:
        gdal_convert_to_png(image)

    print(f"Removing intermediate images")
    for image in out_images:
        os.remove(image)


if __name__ == "__main__":
    main()

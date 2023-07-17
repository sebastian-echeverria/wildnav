import subprocess
import os.path
import cv2

# 1. Get current Geotiff dimensions
# 2. Split into 1000 to 1500 by 1000 to 1500 pieces
# 3. Use gdal_translate through popen or similar.
    # Use gdal to convert to PNG (-of) and to cut to pieces (-srcwin x y xsize ysize)

SUB_SIZE = 1000

def create_subpictures(image_name: str, line_size:int = SUB_SIZE):
    """Creates subpictures for a diven image."""

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
            image_name_without_ext, _ = os.path.splitext(image_name)
            output_image_name = f"{image_name_without_ext}_{i}_{j}"

            # Create each sub image.
            create_subpic(x_offset, y_offset, curr_x_size, curr_y_size, image_name, output_image_name)


def create_subpic(x: int, y: int, xsize: int, ysize:int, inname: str, outname: str):
    """Creates a subpicture of a given picture, starting at the given x,y, with the given sizes."""
    full_outname = f"{outname}.png"
    print(f"Executing GDAL translate: {x}, {y}, {xsize}, {ysize}, {inname}, {full_outname}")
    result = subprocess.run(["gdal_translate", "-of", "PNG", "-srcwin", f"{x}", f"{y}", f"{xsize}", f"{ysize}", inname, full_outname])
    print(result)


if __name__ == "__main__":
    print("Starting map splitting")
    create_subpictures("../assets/map/nust/nust.tif")
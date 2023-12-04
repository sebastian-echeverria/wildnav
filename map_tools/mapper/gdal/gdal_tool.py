import os.path
import subprocess


def gdal_create_subpic(x: int, y: int, xsize: int, ysize:int, inname: str, outname: str):
    """Creates a subpicture of a given picture, starting at the given x,y, with the given sizes."""
    print(f"Executing GDAL translate: {x}, {y}, {xsize}, {ysize}, {inname}, {outname}")
    result = subprocess.run(["gdal_translate", "-srcwin", f"{x}", f"{y}", f"{xsize}", f"{ysize}", inname, outname])
    print(result)


def gdal_convert_to_format(image_name: str, output_format: str = "png") -> bool:
    """
    Converts the image to the given format.
    :return: boolean that indicates whether image was converted or not.
    """
    image_name_without_ext, ext = os.path.splitext(image_name)
    if ext == output_format:
        print(f"Not converting: image {image_name} already has extension {output_format}")
        return False

    outname = f"{image_name_without_ext}.{output_format}"
    print(f"Executing GDAL translate to convert to {output_format}: {image_name}, {outname}")

    # GDAL_PAM_ENABLED = NO avoids creating intermediary xml files.
    result = subprocess.run(["gdal_translate", "-of", output_format.upper(), image_name, outname, "--config", "GDAL_PAM_ENABLED", "NO"])
    print(result)

    return True

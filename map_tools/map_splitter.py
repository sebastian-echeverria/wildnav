import argparse
import os

from mapper.map import map
from mapper.gps import geotiff


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("IMAGE_PATH")
    parser.add_argument("--size")
    parser.add_argument("--if")
    parser.add_argument("--of")
    args = parser.parse_args()

    image_path = args.IMAGE_PATH
    size = int(args.size) if args.size else None
    out_format = args.of

    # Split the map into sub images, and extract GPS data for each new piece.
    sub_images_data = map.split_map(image_path, size)
    sub_images_paths = [image["file_path"] for image in sub_images_data]
    sub_images_info = geotiff.get_geotiff_gps_info(sub_images_paths)

    # Convert the sub images if needed, and create CSV file with GPS info.
    updated_sub_images_info = map.convert_images(sub_images_paths, sub_images_info, out_format)
    map.create_map_data_file(os.path.dirname(image_path), updated_sub_images_info)


if __name__ == "__main__":
    main()

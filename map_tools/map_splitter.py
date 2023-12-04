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

    out_images = map.split_map(image_path, size, out_format)
    info = geotiff.get_geotiff_gps_info(out_images)
    map.create_map_data_file(os.path.dirname(image_path), info)


if __name__ == "__main__":
    main()

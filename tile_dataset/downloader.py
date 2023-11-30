import argparse
import os

import csv_generator
import tile_downloader

DEFAULT_PHOTO_ZOOM = 19
MAP_CSV_FILE = "map.csv"
DRONE_CSV_FILE = "photo_metadata.csv"
DRONE_JSON_FILE = "dataset.json"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-z", type=int, default=DEFAULT_PHOTO_ZOOM, help="Zoom level to use for map, starting from 0")
    parser.add_argument("--lat", type=float, help="Latitud in degrees", required=True)
    parser.add_argument("--long", type=float, help="Longitude in degrees", required=True)
    parser.add_argument("-f", type=str, default="./tiles", help="Output folder")
    parser.add_argument("-r", type=int, default=0, help="How many additional tiles to get in a radius around the center one. 1 means all tiles 1 tile away (i.e., 8), 2, 2 tiles away, etc")
    parser.add_argument("-m", type=int, help="If present, merge all images, and how many images to merge them into.")
    arguments, _ = parser.parse_known_args()

    # Get all tiles.
    image_matrix, image_data = tile_downloader.get_tiles(arguments.z, arguments.lat, arguments.long, output_folder=arguments.f, radius=arguments.r)

    if arguments.m is not None:
        # Merge tiles, and generate CSV for map.
        map_data = tile_downloader.merge_tiles(image_matrix, arguments.z, arguments.lat, arguments.long, output_folder=arguments.f, radius=arguments.r, num_final_images=arguments.m)
        csv_generator.write_map_csv_coordinates(map_data, os.path.join(arguments.f, MAP_CSV_FILE))
    else:
        # Generate CSV and JSON for separate tiles.
        csv_generator.write_drone_csv_coordinates(image_data, os.path.join(arguments.f, DRONE_CSV_FILE))

import argparse
import os

from mapper.map import map
import mapper.io.csv_generator as csv_generator
import mapper.tiles.tile_handler as tile_handler

DEFAULT_PHOTO_ZOOM = 19
DRONE_CSV_FILE = "photo_metadata.csv"
DRONE_JSON_FILE = "dataset.json"
DEFAULT_OUTPUT_FOLDER = "./temp_io"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-z", type=int, default=DEFAULT_PHOTO_ZOOM, help="Zoom level to use for map, starting from 0")
    parser.add_argument("--lat", type=float, help="Latitud in degrees", required=True)
    parser.add_argument("--long", type=float, help="Longitude in degrees", required=True)
    parser.add_argument("-o", type=str, default=DEFAULT_OUTPUT_FOLDER, help="Output folder")
    parser.add_argument("-r", type=int, default=0, help="How many additional tiles to get in a radius around the center one. 1 means all tiles 1 tile away (i.e., 8), 2, 2 tiles away, etc")
    parser.add_argument("-m", action=argparse.BooleanOptionalAction, help="If present, merge all images.")
    parser.add_argument("-d", action=argparse.BooleanOptionalAction, help="If present, delete all files in output folder before generating data.")
    parser.add_argument("-s", type=int, default=DEFAULT_PHOTO_ZOOM, help="Max pixel width size for a map image, split into this size as needed.")
    arguments, _ = parser.parse_known_args()

    output_folder = arguments.o
    if output_folder is None:
        output_folder = DEFAULT_OUTPUT_FOLDER

    # Get all tiles.
    image_matrix, image_data = tile_handler.download_tiles(arguments.z, arguments.lat, arguments.long, output_folder=output_folder, radius=arguments.r, delete=arguments.d)

    if arguments.m is not None:
        # Merge tiles, and generate CSV for map.
        map_data = tile_handler.create_maps(image_matrix, arguments.z, arguments.lat, arguments.long, output_folder=output_folder, radius=arguments.r)
        map.create_map_data_file(output_folder, map_data)
    else:
        # Generate CSV  for separate tiles.
        csv_generator.write_drone_csv_coordinates(image_data, os.path.join(output_folder, DRONE_CSV_FILE))

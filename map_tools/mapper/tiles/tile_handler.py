
import os
from typing import Tuple

import requests
from PIL import Image

import mapper.gps.exif_gps as exif_gps
from mapper.tiles.tile_system import TileSystem
import mapper.image.image_merge as image_merge
from mapper.io import file_utils
from mapper.map import map


TILE_SOURCES = {
    "ARCGIS": {
        "url": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{}/{}/{}"
    }
}

IMAGE_TYPES = {"image/jpeg": "jpg", "image/png": "png"}


def download_tiles(zoom_level: int, lat: float, long: float, base_url: str = TILE_SOURCES["ARCGIS"]["url"], 
              output_folder: str = "./", radius: int = 0, merge: bool = True, delete : bool = True) -> Tuple[list[list[str]], list[dict]]:
    """Saves into a file the tile for the given zoom, lat and log, using the provided tile source and output folder."""
    # First obtain tile coordinates.
    center_tile_x, center_tile_y = TileSystem.lat_long_to_tile_xy(lat, long, zoom_level)
    print(f"Tile: ({center_tile_x}, {center_tile_y})")

    # Delete and create folder as needed.
    if delete:
        print(f"Deleting old folder data from {output_folder}")
        file_utils.delete_folder_data(output_folder)
    file_utils.create_folder(output_folder)

    # Iterate over all tiles we need.
    image_data: list[dict] = []
    all_images: list[list[str]] = []
    curr_row = -1
    for tile_y in range (center_tile_y - radius, center_tile_y + radius + 1):
        all_images.append([])
        curr_row += 1
        for tile_x in range(center_tile_x - radius, center_tile_x + radius + 1):
            # Construct proper URL.
            tile_url = base_url.format(zoom_level, tile_y, tile_x)
            
            # Get tile.
            response = requests.get(tile_url)
            if response:
                # Check image type.
                image_type = response.headers.get('content-type')
                print(f"Got image with format {image_type}")
                if image_type not in IMAGE_TYPES:
                    raise Exception(f"Image type not supported: {image_type}")
                
                # Prepare file name and folder to save image to.
                file_name = f"tile_z_{zoom_level}_tile_{tile_x}_{tile_y}.{IMAGE_TYPES[image_type]}"
                file_path = os.path.join(output_folder, file_name)
                
                print(f"Writing output file to: {file_path}")
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                all_images[curr_row].append(file_path)

                # Calculate coordinates of center of this tile.
                center_lat, center_long = TileSystem.tile_xy_to_lat_long_center(tile_x, tile_y, zoom_level)
                image_data.append({"filename": file_name, "path": file_path, "lat": center_lat, "lon": center_long})

                # Add coordinates as exif data.
                exif_gps.add_geolocation(file_path, center_lat, center_long)
            else:
                print(f"Error: {response.reason}")

    return all_images, image_data


def _calculate_tile_gps(image_name: str, image_path: str, zoom_level: int, tile_x: int, tile_y: int) -> dict:
    """Calculate GPS coordinates information for center and corners of the provided tile."""
    # Calculate coordinates of center of this tile.
    center_lat, center_long = TileSystem.tile_xy_to_lat_long_center(tile_x, tile_y, zoom_level)
    print(f"CLA, CLO: {center_lat}, {center_long}")
    top_left_lat, top_left_long = TileSystem.tile_xy_to_lat_long_top_left(tile_x, tile_y, zoom_level)
    print(f"TLA, TLO: {top_left_lat}, {top_left_long}")
    bottom_right_lat, bottom_right_long = TileSystem.tile_xy_to_lat_long_bottom_right(tile_x, tile_y, zoom_level)
    print(f"BRLA, BRLO: {bottom_right_lat}, {bottom_right_long}")

    # Put everything together in a dict.
    gps_info = {}
    gps_info["filename"] = image_name
    gps_info["file_path"] = image_path
    gps_info["center_lat"] = center_lat
    gps_info["center_long"] = center_long
    gps_info["top_left_lat"] = top_left_lat
    gps_info["top_left_long"] = top_left_long
    gps_info["bottom_right_lat"] = bottom_right_lat
    gps_info["bottom_right_long"] = bottom_right_long

    return gps_info


def _calculate_images_gps(images_info: list[dict], main_image_info: dict, zoom_level: int) -> list[dict]:
    """
    Calculates the GPS coordinates for each image, based on the main one.
    :return: a list of GPS dicts for each sub image.
    """
    all_info = []

    # Reference pixel from main image.
    main_top_left_x_pixel, main_top_left_y_pixel = TileSystem.lat_long_to_pixel_xy(main_image_info["top_left_lat"], main_image_info["top_left_long"], zoom_level)

    for image_info in images_info:
        # The lat and long for the top left can be obtained through the pixels, adding the offset to the base one.
        top_left_x_pixel = main_top_left_x_pixel + image_info["x_offset"]
        top_left_y_pixel = main_top_left_y_pixel + image_info["y_offset"]
        top_left_lat, top_left_long = TileSystem.pixel_xy_to_lat_long(top_left_x_pixel, top_left_y_pixel, zoom_level)

        # The lat and long for the bottom right can be obtained through the pixels, adding the offset and the size to the base one.
        bottom_left_x_pixel = top_left_x_pixel + image_info["x_size"]
        bottom_left_y_pixel = top_left_y_pixel + image_info["y_size"]
        bottom_right_lat, bottom_right_long = TileSystem.pixel_xy_to_lat_long(bottom_left_x_pixel, bottom_left_y_pixel, zoom_level)

        # The lat and long for the center can be obtained through the pixels, adding the offset and half the size.
        center_x_pixel = top_left_x_pixel + image_info["x_size"] // 2
        center_y_pixel = top_left_y_pixel + image_info["y_size"] // 2
        center_lat, center_long = TileSystem.pixel_xy_to_lat_long(center_x_pixel, center_y_pixel, zoom_level)

        image_info["center_lat"] = center_lat
        image_info["center_long"] = center_long
        image_info["top_left_lat"] = top_left_lat
        image_info["top_left_long"] = top_left_long
        image_info["bottom_right_lat"] = bottom_right_lat
        image_info["bottom_right_long"] = bottom_right_long        

        all_info.append(image_info)

    return all_info


def _create_map_from_tiles(all_images: list[list[str]], zoom_level: int, lat: float, long: float, 
                output_folder: str = "./", radius: int = 0) -> dict:
    """
    Creates a combined map from a set of images.
    :return: A dictionary with the map path, and GPS info about it.
    """
    center_tile_x, center_tile_y = TileSystem.lat_long_to_tile_xy(lat, long, zoom_level)
    combined_image_name = f"tile_z_{zoom_level}_tile_{center_tile_x}_{center_tile_y}_r_{radius}.{IMAGE_TYPES['image/png']}"
    combined_image_path = os.path.join(output_folder, combined_image_name)
    print(f"Combining images into output file: {combined_image_path}")
    image_merge.combine_images(all_images, combined_image_path)

    # Calculate coordinates of center of this tile.
    map_info = _calculate_tile_gps(combined_image_name, combined_image_path, zoom_level, center_tile_x, center_tile_y)

    # Add coordinates as exif data.
    exif_gps.add_geolocation(combined_image_path, map_info["center_lat"], map_info["center_long"])    

    return map_info


def create_maps(all_images: list[list[str]], zoom_level: int, lat: float, long: float, 
                output_folder: str = "./", radius: int = 0, remove_tiles: bool = True, max_size: int = map.DEFAULT_SUB_SIZE) -> list[dict]:
    """
    Saves into a file the tile for the given zoom, lat and log, using the provided tile source and output folder.
    :return: a list of dictionary with information about the map or its parts.
    """
    # Combine images.
    if len(all_images) > 1:
        # Create merged map and get its GPS info.
        all_maps_info = []
        map_info = _create_map_from_tiles(all_images, zoom_level, lat, long, output_folder, radius)
        all_maps_info.append(map_info)
        
        if remove_tiles:
            print("Removing individual tiles")
            for image_row in all_images:
                for image in image_row:
                    os.remove(image)

        # If width or height of resulting combined map is more than our max size, split.
        combined_image = Image.open(map_info["file_path"])
        width, height = combined_image.size
        if width > max_size or height > max_size:
            # Split map by size and calculate GPS data for each part.
            sub_images_data = map.split_map(map_info["file_path"], max_size)            
            all_maps_info = _calculate_images_gps(sub_images_data, map_info, zoom_level)

    return all_maps_info

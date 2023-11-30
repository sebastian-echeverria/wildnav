
import os
from pathlib import Path
from typing import Tuple

import requests

import exif_gps
from tile_system import TileSystem
import tile_combination


TILE_SOURCES = {
    "ARCGIS": {
        "url": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{}/{}/{}"
    }
}

IMAGE_TYPES = {"image/jpeg": "jpg", "image/png": "png"}


def create_folder_for_file(filepath: str):
    """Creates the folder tree for a given file path, if needed."""
    folder = Path(filepath).parent
    if not folder.exists():
        folder.mkdir(parents=True)


def get_tiles(zoom_level: int, lat: float, long: float, base_url: str = TILE_SOURCES["ARCGIS"]["url"], 
              output_folder: str = "./", radius: int = 0, merge: bool = True) -> Tuple[list[list[str]], list[dict]]:
    """Saves into a file the tile for the given zoom, lat and log, using the provided tile source and output folder."""
    # First obtain tile coordinates.
    center_tile_x, center_tile_y = TileSystem.lat_long_to_tile_xy(lat, long, zoom_level)
    print(f"Tile: ({center_tile_x}, {center_tile_y})")

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
                create_folder_for_file(file_path)
                
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


def merge_tiles(all_images: list[list[str]], zoom_level: int, lat: float, long: float, output_folder: str = "./", radius: int = 0, remove: bool = True, num_final_images: int = 1) -> list[dict]:
    """Saves into a file the tile for the given zoom, lat and log, using the provided tile source and output folder."""    
    # Combine images.
    if len(all_images) > 1:
        center_tile_x, center_tile_y = TileSystem.lat_long_to_tile_xy(lat, long, zoom_level)
        image_data: list[dict] = []
        combined_image_name = f"tile_z_{zoom_level}_tile_{center_tile_x}_{center_tile_y}_r_{radius}.{IMAGE_TYPES['image/png']}"
        combined_image_path = os.path.join(output_folder, combined_image_name)
        print(f"Combining images into output file: {combined_image_path}")
        tile_combination.combine_tiles(all_images, combined_image_path, num_final_images)

        # Calculate coordinates of center of this tile.
        top_left_lat, top_left_long = TileSystem.tile_xy_to_lat_long_top_left(center_tile_x, center_tile_y, zoom_level)
        print(f"TLA, TLO: {top_left_lat}, {top_left_long}")
        bottom_right_lat, bottom_right_long = TileSystem.tile_xy_to_lat_long_bottom_right(center_tile_x, center_tile_y, zoom_level)
        print(f"BRLA, BRLO: {bottom_right_lat}, {bottom_right_long}")
        image_data.append({"filename": combined_image_name, "top_left_lat": top_left_lat, "top_left_lon": top_left_long, "bottom_right_lat": bottom_right_lat, "bottom_right_long": bottom_right_long})        

        # Add coordinates as exif data.
        center_lat, center_long = TileSystem.tile_xy_to_lat_long_center(center_tile_x, center_tile_y, zoom_level)
        exif_gps.add_geolocation(combined_image_path, center_lat, center_long)
        
        if remove:
            print("Removing individual tiles")
            for image_row in all_images:
                for image in image_row:
                    os.remove(image)

    return image_data

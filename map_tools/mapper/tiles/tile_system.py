# based on sample code from https://learn.microsoft.com/en-us/bingmaps/articles/bing-maps-tile-system

import math

class TileSystem:

    EarthRadius = 6378137
    MinLatitude = -85.05112878
    MaxLatitude = 85.05112878
    MinLongitude = -180
    MaxLongitude = 180
    TileSideSize = 256

    @staticmethod
    def clip(n, minValue, maxValue):
        return min(max(n, minValue), maxValue)

    @staticmethod
    def map_size(level_of_detail):
        return TileSystem.TileSideSize << level_of_detail

    @staticmethod
    def ground_resolution(latitude, level_of_detail):
        latitude = TileSystem.clip(latitude, TileSystem.MinLatitude, TileSystem.MaxLatitude)
        return math.cos(latitude * math.pi / 180) * 2 * math.pi * TileSystem.EarthRadius / TileSystem.map_size(level_of_detail)

    @staticmethod
    def map_scale(latitude, level_of_detail, screen_dpi):
        return TileSystem.ground_resolution(latitude, level_of_detail) * screen_dpi / 0.0254

    @staticmethod
    def lat_long_to_pixel_xy(latitude, longitude, level_of_detail):
        latitude = TileSystem.clip(latitude, TileSystem.MinLatitude, TileSystem.MaxLatitude)
        longitude = TileSystem.clip(longitude, TileSystem.MinLongitude, TileSystem.MaxLongitude)

        x = (longitude + 180) / 360
        sin_latitude = math.sin(latitude * math.pi / 180)
        y = 0.5 - math.log((1 + sin_latitude) / (1 - sin_latitude)) / (4 * math.pi)

        map_size = TileSystem.map_size(level_of_detail)
        pixel_x = int(TileSystem.clip(x * map_size + 0.5, 0, map_size - 1))
        pixel_y = int(TileSystem.clip(y * map_size + 0.5, 0, map_size - 1))

        return pixel_x, pixel_y

    @staticmethod
    def pixel_xy_to_lat_long(pixel_x, pixel_y, level_of_detail):
        map_size = TileSystem.map_size(level_of_detail)
        x = (TileSystem.clip(pixel_x, 0, map_size - 1) / map_size) - 0.5
        y = 0.5 - (TileSystem.clip(pixel_y, 0, map_size - 1) / map_size)

        latitude = 90 - 360 * math.atan(math.exp(-y * 2 * math.pi)) / math.pi
        longitude = 360 * x

        return latitude, longitude

    @staticmethod
    def pixel_xy_to_tile_xy(pixel_x, pixel_y):
        tile_x = pixel_x // TileSystem.TileSideSize
        tile_y = pixel_y // TileSystem.TileSideSize

        return tile_x, tile_y

    @staticmethod
    def tile_xy_to_pixel_xy(tile_x, tile_y):
        pixel_x = tile_x * TileSystem.TileSideSize
        pixel_y = tile_y * TileSystem.TileSideSize

        return pixel_x, pixel_y

    @staticmethod
    def lat_long_to_tile_xy(latitude, longitude, level_of_detail):
        pixel_x, pixel_y = TileSystem.lat_long_to_pixel_xy(latitude, longitude, level_of_detail)
        print(pixel_x, pixel_y)
        return TileSystem.pixel_xy_to_tile_xy(pixel_x, pixel_y)
    
    @staticmethod
    def tile_xy_to_lat_long_center(tile_x, tile_y, level_of_detail):
        """Returns the lat and long of the center of the given tile."""
        origin_pixel_x, origin_pixel_y = TileSystem.tile_xy_to_pixel_xy(tile_x, tile_y)
        center_pixel_x = origin_pixel_x + TileSystem.TileSideSize/2
        center_pixel_y = origin_pixel_y + TileSystem.TileSideSize/2
        lat, long = TileSystem.pixel_xy_to_lat_long(center_pixel_x, center_pixel_y, level_of_detail)
        return lat, long

    @staticmethod
    def tile_xy_to_lat_long_top_left(tile_x, tile_y, level_of_detail):
        """Returns the lat and long of the center of the given tile."""
        origin_pixel_x, origin_pixel_y = TileSystem.tile_xy_to_pixel_xy(tile_x, tile_y)
        lat, long = TileSystem.pixel_xy_to_lat_long(origin_pixel_x, origin_pixel_y, level_of_detail)
        return lat, long
    
    @staticmethod
    def tile_xy_to_lat_long_bottom_right(tile_x, tile_y, level_of_detail):
        """Returns the lat and long of the center of the given tile."""
        origin_pixel_x, origin_pixel_y = TileSystem.tile_xy_to_pixel_xy(tile_x, tile_y)
        end_pixel_x = origin_pixel_x + TileSystem.TileSideSize
        end_pixel_y = origin_pixel_y + TileSystem.TileSideSize
        lat, long = TileSystem.pixel_xy_to_lat_long(end_pixel_x, end_pixel_y, level_of_detail)
        return lat, long    
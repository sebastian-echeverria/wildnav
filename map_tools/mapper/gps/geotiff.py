from typing import Tuple

from osgeo import osr
from osgeo import gdal


def get_geotiff_gps_info(geotiff_images: list[str]) -> list[dict]:
    """
    Gest coordinate info from the provided GeoTIFF images.
    :return: A dictionary with entries for the coordinates of the top left and bottom right corners.
    """
    info = {}
    try:
        # Now info for each image.
        for image_path in geotiff_images:
            # For each image, get the name and change ext to the final output.
            info["filename"] = image_path
            geotiff_image = GeoTIFFImage(image_path)
            info["top_left_long"], info["top_left_lat"], _ = geotiff_image.top_left_coords()
            info["bottom_right_long"], info["bottom_right_lat"], _ = geotiff_image.bottom_right_coords()
    except RuntimeError as ex:
        print(f"Could not generate metadata from images, they may not be GeoTIFF files: {ex}")
    
    return info


class GeoTIFFImage():
    """Converts coordinates from a GeoTIFF base image."""

    def __init__(self, image_path: str) -> None:
        self.gdal_image = gdal.Open(image_path)
        self.c, self.a, self.b, self.f, self.d, self.e = self.gdal_image.GetGeoTransform()

        projection_name = self.gdal_image.GetProjection()
        if projection_name == "":
            raise RuntimeError("Can't initiate conversor, image does not have GeoTIFF projection info.")

        srs = osr.SpatialReference()
        srs.ImportFromWkt(projection_name)
        srsLatLong = srs.CloneGeogCS()
        self.coord_transform = osr.CoordinateTransformation(srs, srsLatLong)

    def pixel_to_coord(self, col: float, row: float) -> Tuple[float, float, float]:
        """Returns global coordinates to pixel center using base-0 raster index"""
        xp = self.a * col + self.b * row + self.c
        yp = self.d * col + self.e * row + self.f
        coords = self.coord_transform.TransformPoint(xp, yp, 0)
        return coords
    
    def top_left_coords(self) -> Tuple[float, float, float]:
        return self.pixel_to_coord(0, 0)
    
    def bottom_right_coords(self) -> Tuple[float, float, float]:
        return self.pixel_to_coord(self.gdal_image.RasterXSize, self.gdal_image.RasterYSize)

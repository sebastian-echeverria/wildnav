from typing import Tuple

from osgeo import osr
from osgeo import gdal


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

    def pixel_to_coord(self, col: float, row: float) -> Tuple[float, float]:
        """Returns global coordinates to pixel center using base-0 raster index"""
        xp = self.a * col + self.b * row + self.c
        yp = self.d * col + self.e * row + self.f
        coords = self.coord_transform.TransformPoint(xp, yp, 0)
        return coords
    
    def top_left_coords(self) -> Tuple[float, float]:
        return self.pixel_to_coord(0, 0)
    
    def bottom_right_coords(self) -> Tuple[float, float]:
        return self.pixel_to_coord(self.gdal_image.RasterXSize, self.gdal_image.RasterYSize)

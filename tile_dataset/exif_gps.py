from typing import Tuple, Literal
from pathlib import Path

import piexif
from PIL import Image
from fractions import Fraction


def _deg_to_dms(decimal_coordinate: float, cardinal_directions: list[str]) -> Tuple[int, int, Fraction, str]:
    """
    This function converts decimal coordinates into the DMS (degrees, minutes and seconds) format.
    It also determines the cardinal direction of the coordinates.

    :param decimal_coordinate: the decimal coordinates, such as 34.0522
    :param cardinal_directions: the locations of the decimal coordinate, such as ["S", "N"] or ["W", "E"]
    :return: degrees, minutes, seconds and compass_direction
    :rtype: int, int, Fraction, string
    """
    if decimal_coordinate < 0:
        compass_direction = cardinal_directions[0]
    elif decimal_coordinate > 0:
        compass_direction = cardinal_directions[1]
    else:
        compass_direction = ""
    degrees = int(abs(decimal_coordinate))
    decimal_minutes = (abs(decimal_coordinate) - degrees) * 60
    minutes = int(decimal_minutes)
    seconds = Fraction((decimal_minutes - minutes) * 60).limit_denominator(100)
    return degrees, minutes, seconds, compass_direction


def _dms_to_exif_format(dms_degrees: int, dms_minutes: int, dms_seconds: Fraction) -> tuple[tuple[int, Literal[1]], tuple[int, Literal[1]], tuple[int, int]]:
    """
    This function converts DMS (degrees, minutes and seconds) to values that can
    be used with the EXIF (Exchangeable Image File Format).

    :param dms_degrees: int value for degrees
    :param dms_minutes: int value for minutes
    :param dms_seconds: fractions.Fraction value for seconds
    :return: EXIF values for the provided DMS values
    :rtype: nested tuple
    """
    exif_format = (
        (dms_degrees, 1),
        (dms_minutes, 1),
        (int(dms_seconds.limit_denominator(100).numerator), int(dms_seconds.limit_denominator(100).denominator))
    )
    return exif_format


def add_geolocation(image_path: str, latitude: float, longitude: float):
    """
    This function adds GPS values to an image using the EXIF format.
    This fumction calls the functions deg_to_dms and dms_to_exif_format.

    :param image_path: image to add the GPS data to
    :param latitude: the north–south position coordinate
    :param longitude: the east–west position coordinate
    """
    # converts the latitude and longitude coordinates to DMS
    latitude_dms = _deg_to_dms(latitude, ["S", "N"])
    longitude_dms = _deg_to_dms(longitude, ["W", "E"])

    # convert the DMS values to EXIF values
    exif_latitude = _dms_to_exif_format(latitude_dms[0], latitude_dms[1], latitude_dms[2])
    exif_longitude = _dms_to_exif_format(longitude_dms[0], longitude_dms[1], longitude_dms[2])

    try:
        # Load existing EXIF data
        img = Image.open(image_path)
        exif_data = img.getexif()

        # https://exiftool.org/TagNames/GPS.html
        # Create the GPS EXIF data
        coordinates = {
            piexif.GPSIFD.GPSVersionID: (2, 0, 0, 0),
            piexif.GPSIFD.GPSLatitude: exif_latitude,
            piexif.GPSIFD.GPSLatitudeRef: latitude_dms[3],
            piexif.GPSIFD.GPSLongitude: exif_longitude,
            piexif.GPSIFD.GPSLongitudeRef: longitude_dms[3]
        }

        # Update the EXIF data with the GPS information
        exif_data['GPS'] = coordinates

        # Dump the updated EXIF data and insert it into the image
        exif_bytes = piexif.dump(exif_data)
        if Path(image_path).suffix == ".png":
            img.save(image_path, exif=exif_bytes)
        else:
            piexif.insert(exif_bytes, image_path)
        print(f"EXIF data updated successfully for the image {image_path}.")
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc(e)

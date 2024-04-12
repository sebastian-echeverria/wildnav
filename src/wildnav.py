"""Core module. Contains the main functions for the project."""
from __future__ import annotations

import argparse
import os.path
from pathlib import Path
import os
import glob
import csv
import json

import cv2
import haversine as hs
from haversine import Unit
import numpy as np
from natsort import natsorted

import superglue_utils


############################################################################################################
# Important variables
############################################################################################################

DEFAULT_BASE_PATH = "../assets/"
DEFAULT_MAP_FOLDER = "map/"
DEFAULT_PHOTOS_FOLDER = "query/"
DEFAULT_RESULTS_FOLDER = "results/"
DEFAULT_ROTATIONS = 4

MAP_DATA_FILE = "map.csv" #  csv file with the sattelite geo tagged images
PHOTOS_DATA_FILE = "photo_metadata.csv" # csv file with the geo tagged drone images;
                                                            # the geo coordinates are only used to compare
                                                            # the calculated coordinates with the real ones
                                                            # after the feature matching


############################################################################################################
# Class definitions
############################################################################################################
class GeoPhotoDrone:
    """Stores a drone photo together with GNSS location
    and camera rotation parameters
    """
    def __init__(self,filename, photo=0, latitude=0, longitude = 0 ,\
         altitude = 0 ,gimball_roll = 0, gimball_yaw = 0, gimball_pitch = 0, flight_roll = 0, flight_yaw = 0, flight_pitch = 0):
        self.filename = filename
        self.photo = photo
        self.latitude = latitude
        self.longitude = longitude
        self.latitude_calculated = -1
        self.longitude_calculated = -1
        self.altitude = altitude
        self.gimball_roll = gimball_roll
        self.gimball_yaw = gimball_yaw
        self.gimball_pitch = gimball_pitch
        self.flight_roll = flight_roll
        self.flight_yaw = flight_yaw
        self.flight_pitch = flight_pitch
        self.corrected = False
        self.matched = False

        self.matches = []
        self.confidence = []
        self.matches_invalid = []
        self.confidence_invalid = []        

    def __str__(self):
        return "%s; \nlatitude: %f \nlongitude: %f \naltitude: %f \ngimball_roll: %f \ngimball_yaw: %f \ngimball_pitch: %f \nflight_roll: %f \nflight_yaw: %f \nflight_pitch: %f" % (self.filename, self.latitude, self.longitude, self.altitude, self.gimball_roll, self.gimball_yaw, self.gimball_pitch, self.flight_roll, self.flight_yaw, self.flight_pitch )
        
class GeoPhoto:
    """Stores a satellite photo together with (latitude, longitude) for top_left and bottom_right_corner
    """
    def __init__(self, filename, photo, geo_top_left, geo_bottom_right):
        self.filename = filename
        self.photo = photo
        self.top_left_coord = geo_top_left
        self.bottom_right_coord = geo_bottom_right

    def __lt__(self, other):
         return self.filename < other.filename

    def __str__(self):
        return "%s; \n\ttop_left_latitude: %f \n\ttop_left_lon: %f \n\tbottom_right_lat: %f \n\tbottom_right_lon %f " % (self.filename, self.top_left_coord[0], self.top_left_coord[1], self.bottom_right_coord[0], self.bottom_right_coord[1])


############################################################################################################
# Functions for data writing and reading csv files
############################################################################################################
def csv_read_drone_images(photo_path: str) -> list[GeoPhotoDrone]:
    """Builds a list with drone geo tagged photos by reading a csv file with this format:
    Filename, Top_left_lat,Top_left_lon,Bottom_right_lat,Bottom_right_long
    "photo_name.png",60.506787,22.311631,60.501037,22.324467
    """
    geo_list_drone = []
    print(f"Loading UAV images from {photo_path}")
    photos_data_filename = os.path.join(photo_path, PHOTOS_DATA_FILE)

    if os.path.isfile(photos_data_filename):
        # If there is a file with photo details, load info from there.
        print(f"Getting image info from {photos_data_filename}")
        with open(photos_data_filename) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0
            for row in csv_reader:
                if line_count == 0:
                    print(f'Column names are {", ".join(row)}')
                    line_count += 1
                else:                
                    #img = cv2.imread(photo_path + row[0],0)
                    print(f"Row: {row}")
                    full_image_path = os.path.join(photo_path, row[0])
                    geo_photo = GeoPhotoDrone(full_image_path, 0, float(row[1]), float(row[2]), float(row[3]), float(row[4]), float(row[5]), float(row[6]), float(row[7]), float(row[8]), float(row[9]))
                    geo_list_drone.append(geo_photo)
                    line_count += 1

            print(f'Processed {line_count} lines.')
    else:
        # If there isn't, just load all image files in the folder and set all data to 0.
        print(f"Getting all images at {photo_path}")
        file_paths = [os.path.join(photo_path, file) for file in natsorted(os.listdir(photo_path))]
        for full_image_path in file_paths:
            geo_photo = GeoPhotoDrone(full_image_path, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
            geo_list_drone.append(geo_photo)

    return geo_list_drone


def csv_read_sat_map(map_path):
    """Builds a list with satellite geo tagged photos by reading a csv file with this format:
    Filename, Top_left_lat,Top_left_lon,Bottom_right_lat,Bottom_right_long
    "photo_name.png",60.506787,22.311631,60.501037,22.324467
    """
    geo_list = []
    map_data_filename = os.path.join(map_path, MAP_DATA_FILE)
    print("opening: ", map_data_filename)
    with open(map_data_filename) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                print(f'Column names are {", ".join(row)}')
                line_count += 1
            else:
                full_image_path = os.path.join(map_path, row[0])
                img = cv2.imread(full_image_path,0)
                geo_photo = GeoPhoto(full_image_path, img, (float(row[1]),float(row[2])), (float(row[3]), float(row[4])))
                geo_list.append(geo_photo)
                line_count += 1

        print(f'Processed {line_count} lines.')
        geo_list.sort() # sort alphabetically by filename to ensure that the feature matcher return the right index of the matched sat image
        return geo_list


def csv_write_image_location(photos, results_path: str):
    header = ['Filename', 'Latitude', 'Longitude', 'Calculated_Latitude', 'Calculated_Longitude', 'Latitude_Error', 'Longitude_Error', 'Meters_Error', 'Corrected', 'Matched', 'Angle', 'Matches', 'Confidence', 'Matches Invalid', 'Confidence Invalid']
    with open(os.path.join(results_path, "calculated_coordinates.csv"), 'a', encoding='UTF8') as f:
        writer = csv.writer(f)
        writer.writerow(header)

        np.set_printoptions(threshold=np.inf)
        for photo in photos:
            photo_name = photo.filename.split("/")[-1]
            loc1 = ( photo.latitude, photo.longitude)
            loc2 = ( photo.latitude_calculated, photo.longitude_calculated)
            dist_error =  hs.haversine(loc1,loc2,unit=Unit.METERS)
            lat_error = photo.latitude - photo.latitude_calculated
            lon_error = photo.longitude - photo.longitude_calculated
            matches = f"{photo.matches}"
            confidence = f"{json.dumps(photo.confidence)}"
            matches_invalid = f"{photo.matches_invalid}"
            confidence_invalid = f"{json.dumps(photo.confidence_invalid)}"            
            line = [photo_name, str(photo.latitude), str(photo.longitude), str(photo.latitude_calculated), str(photo.longitude_calculated), \
                    str(lat_error), str(lon_error), str(dist_error), str(photo.corrected), str(photo.matched), str(photo.gimball_yaw + photo.flight_yaw - 15), \
                    matches, confidence, matches_invalid, confidence_invalid]
            writer.writerow(line)


def csv_write_simple_output(photos, results_path: str):
    # Writes a simplified output with just calculated coordinates, one per row.
    with open(os.path.join(results_path, "output.csv"), 'a', encoding='UTF8') as f:
        writer = csv.writer(f)
        for photo in photos:
            line = [str(photo.latitude_calculated), str(photo.longitude_calculated)]
            writer.writerow(line)            


def calculate_geo_pose(geo_photo, center, features_mean,  shape):
    """
    Calculates the geographical location of the drone image.
    Input: satellite geotagged image, relative pixel center of the drone image, 
    (center with x = 0.5 and y = 0.5 means the located features are in the middle of the sat image)
    pixel coordinatess (horizontal and vertical) of where the features are localted in the sat image, shape of the sat image
    """
    #use ratio here instead of pixels because image is reshaped in superglue    
    latitude = geo_photo.top_left_coord[0] + abs( center[1])  * ( geo_photo.bottom_right_coord[0] - geo_photo.top_left_coord[0])
    longitude = geo_photo.top_left_coord[1] + abs(center[0])  * ( geo_photo.bottom_right_coord[1] - geo_photo.top_left_coord[1])
    
    return latitude, longitude



#######################################
# MAIN
#######################################

def main(base_path: str, map_folder: str, photos_folder: str, results_folder: str, rotate: bool = True):
    print(f"Running in {os. getcwd()}")
    print(f"Using base path: {base_path}")

    map_path = os.path.join(base_path, map_folder)
    drone_photos_path = os.path.join(base_path, photos_folder)
    results_path = os.path.join(base_path, results_folder)

    #Read all the geo tagged images that make up the sattelite map used for reference
    geo_images_list = csv_read_sat_map(map_path)

    #Read all the geo tagged drone that will located in the map
    drone_images_list = csv_read_drone_images(drone_photos_path)

    latitude_calculated = []
    longitude_calculated = []

    print(str(len(drone_images_list)) + " drone photos were loaded.")

    print('==> Will write outputs to {}'.format(results_path))
    Path(results_path).mkdir(exist_ok=True)
    files = glob.glob(os.path.join(results_path, "*"))
    for f in files:
        os.remove(f)    

    # Iterate through all the drone images
    for drone_image in drone_images_list:
        print("***********************************")
        print(f"Opening image {drone_image}")
        photo = cv2.imread(drone_image.filename) # read the drone image
        if photo is None or photo.size == 0:
            print(f"Image {drone_image.filename} could not be opened; ignoring.")
            continue

        max_features = 0 # keep track of the best match, more features = better match
        located = False # flag to indicate if the drone image was located in the map
        center = None # center of the drone image in the map
        matches = [] # matches found
        confidence = [] # confidence for each match
        matches_invalid = []
        confidence_invalid = []

        if rotate:
            num_rotations = 1
        else:
            num_rotations = DEFAULT_ROTATIONS

        # Iterate through all the rotations, right now it just means to rotate it each time by 90 degrees.
        print(f"Num rotations: {num_rotations}")
        for i in range(0, num_rotations):
            # Rotate image.
            print("=================================")
            print(f"Rotation {i}")
            if i != 0:
                photo = cv2.rotate(photo, cv2.ROTATE_90_CLOCKWISE)
            
            # Write the query photo to the map folder
            cv2.imwrite(os.path.join(map_path, "1_query_image.png"), photo)

            #Call superglue wrapper function to match the query image to the map
            satellite_map_index_new, center_new, located_image_new, features_mean_new, query_image_new, feature_number, matches_new, confidence_new, matches_invalid_new, confidence_invalid_new = superglue_utils.match_image(map_path, results_path)            
            
            # If the drone image was located in the map and the number of features is greater than the previous best match, then update the best match
            # Sometimes the pixel center returned by the perspective transform exceeds 1, discard the resuls in that case
            if (feature_number > max_features and center_new[0] < 1 and center_new[1] < 1):
                satellite_map_index = satellite_map_index_new
                center = center_new
                located_image = located_image_new
                features_mean = features_mean_new
                query_image = query_image_new
                max_features = feature_number
                matches = matches_new.tolist()
                confidence = confidence_new.tolist()
                matches_invalid = matches_invalid_new.tolist()
                confidence_invalid = confidence_invalid_new.tolist()
                located = True
                print(f"Found better image match, {satellite_map_index}, with {max_features} matches, confidence {confidence}.")

        # If the drone image was located in the map, calculate the geographical location of the drone image
        photo_name = drone_image.filename.split("/")[-1]
        if center != None and located:        
            current_location = calculate_geo_pose(geo_images_list[satellite_map_index], center, features_mean, query_image.shape )
            
            # Write the results to the image result file with the best match
            cv2.putText(located_image, "Calculated: " + str(current_location), org = (10,625),fontFace =  cv2.FONT_HERSHEY_DUPLEX, fontScale = 0.8,  color = (0, 0, 0))
            cv2.putText(located_image, "Ground truth: " + str(drone_image.latitude) + ", " + str(drone_image.longitude), org = (10,655),fontFace =  cv2.FONT_HERSHEY_DUPLEX, fontScale = 0.8,  color = (0, 0, 0))
            cv2.imwrite(os.path.join(results_path, photo_name + "_located.png"), located_image)
            
            print("Image " + str(photo_name) + " was successfully located in the map")
            print("Calculated location: ", str(current_location[0:2]))
            print("Ground Truth: ", drone_image.latitude, drone_image.longitude)
            #print(f"Matches: {matches}")
            #print(f"Confidence: {confidence}")
            
            # Save the calculated location for later comparison with the ground truth
            drone_image.matched = True
            drone_image.latitude_calculated = current_location[0]
            drone_image.longitude_calculated = current_location[1]
            drone_image.matches = matches
            drone_image.confidence = confidence
            drone_image.matches_invalid = matches_invalid
            drone_image.confidence_invalid = confidence_invalid
            
            latitude_calculated.append(drone_image.latitude_calculated)
            longitude_calculated.append(drone_image.longitude_calculated)

        else:
            print("NOT MATCHED:", photo_name)

    # Write the results to the csv file    
    csv_write_image_location(drone_images_list, results_path)
    csv_write_simple_output(drone_images_list, results_path)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--path")
    parser.add_argument("--map")
    parser.add_argument("--photos")
    parser.add_argument("--results")
    parser.add_argument("--no_rotate", action='store_true')
    args = parser.parse_args()

    base_path = args.path if args.path is not None else DEFAULT_BASE_PATH
    map_folder = args.map if args.map is not None else DEFAULT_MAP_FOLDER
    photos_folder = args.photos if args.photos is not None else DEFAULT_PHOTOS_FOLDER
    results_folder = args.results if args.results is not None else DEFAULT_RESULTS_FOLDER
    rotate = True if args.no_rotate is None else False

    main(base_path, map_folder, photos_folder, results_folder, rotate)

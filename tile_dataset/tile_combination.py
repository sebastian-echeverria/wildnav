import cv2
import numpy as np
import numpy.typing as npt

TILE_WIDTH=256
TILE_HEIGHT=256
TILE_CHANNEL=3


def speed_block_2D(chops: list[npt.NDArray]):
    H = np.cumsum([x[0].shape[0] for x in chops])
    W = np.cumsum([x.shape[1] for x in chops[0]])
    D = chops[0][0]
    recon = np.empty((H[-1], W[-1], D.shape[2]), D.dtype)
    for rd, rs in zip(np.split(recon, H[:-1], 0), chops):
        for d, s in zip(np.split(rd, W[:-1], 1), rs):
            d[...] = s
    return recon


def combine_tiles_into_one(image_names: list[list[str]], final_name: str):
    """Gets a list of image paths from disk, creates a new combined one as a result."""
    images = np.zeros(shape=[len(image_names), len(image_names[0]), TILE_WIDTH, TILE_HEIGHT, TILE_CHANNEL])
    for x, image_row in enumerate(image_names):
        for y, image in enumerate(image_row):
            images[x][y] = cv2.imread(image)

    # Combine and store this image.
    combined_image = speed_block_2D(images)
    cv2.imwrite(final_name, combined_image)


def combine_tiles(image_names: list[list[str]], final_name: str, num_tiles_per_side: int):
    """Gets a list of image paths from disk, creates a new combined one as a result."""
    final_image_names = []

    final_images_list = []
    x_size = 0
    y_size = 0
    for x, image_row in enumerate(image_names):
        if x_size == num_tiles_per_side:
            curr_images = np.zeros(shape=[len(image_names), len(image_names[0]), TILE_WIDTH, TILE_HEIGHT, TILE_CHANNEL])            

        for y, image in enumerate(image_row):
            images[x][y] = cv2.imread(image)

        x_size += 1

        curr_image_name = final_name.replace(".", f"-{idx}.")
        combine_tiles_into_one(image_names, curr_image_name)
        final_image_names.append(curr_image_name)

    return final_images_list
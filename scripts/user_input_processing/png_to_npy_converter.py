import argparse

import numpy as np
from PIL import Image


def convert_png_to_npy(png_path):
    # sample.png is the name of the image
    # file and assuming that it is uploaded
    # in the current directory or we need
    # to give the path
    image = Image.open(png_path)
    
    # summarize some details about the image
    print(image.format)
    print(image.size)
    print(image.mode)

    # np.asarray() class is used to convert
    # PIL images into NumPy arrays
    npy_array = np.asarray(image)
    npy_array = np.float32(npy_array)

    return npy_array


def convert_depth_to_dexnet_format(npy_array):
    """
    The depth images need to be converted to meters with float32 dtype. 
    Technically it will run as you have found out, but the object looks extremely far away to GQ-CNN 
    when you give it the raw uint16 images. To the best of my knowledge, the depth image in uint16 
    format contains the depth in millimeters, so you can convert to the correct size by dividing by 
    1000.0.(from https://github.com/BerkeleyAutomation/gqcnn/issues/13)

    Convert to 640 x 480  px if necessary beforehand manually!
    """
    npy_array = np.float32(npy_array)
    npy_array = np.expand_dims(npy_array, axis=2) 
    npy_array = npy_array /1000 

    return npy_array


def show_npy_image(npy_array):
    return 0


def save_as_npy(npy_array, npy_path):
    #save 
    np.save(npy_path, npy_array)

if __name__ == "__main__":
    # Parse args
    parser = argparse.ArgumentParser(
        description="Convert a depth image from .png to .npy format that is required by dex-net")
    parser.add_argument("--png_image",
                        type=str,
                        default=None,
                        help="path to the .png image")
    args = parser.parse_args()
    png_path = args.png_image
    npy_path = png_path.strip('.png').strip('_raw') 

    # convert png to npy format of dexnet
    npy_array = convert_png_to_npy(png_path)
    npy_array = convert_depth_to_dexnet_format(npy_array)
    # show npy image 
    show_npy_image(npy_array)
    # save
    save_as_npy(npy_array, npy_path)

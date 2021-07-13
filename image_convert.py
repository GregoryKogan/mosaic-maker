import datetime
import pathlib
import json
from PIL import Image
from OctTree import get_image_using_lookup
from config import *


"""
Sample source image set: https://www.kaggle.com/splcher/animefacedataset
"""


def load_lookup_data():
    with open(LOOKUP_FILENAME, 'r') as lookup_file:
        lookup_data = json.load(lookup_file)
        return lookup_data


def get_input_matrix(path, size=(50, 50)):
    img = Image.open(path)
    img.thumbnail(size, Image.ANTIALIAS)
    data = list(img.getdata())
    width, height = img.size
    matrix = []
    counter = 0
    for i in range(height):
        line = []
        for j in range(width):
            line.append(data[counter])
            counter += 1
        matrix.append(line)
    return matrix


def build_image(color_matrix, size=(2000, 2000), random_score=10):
    m_height = len(color_matrix)
    m_width = len(color_matrix[0])
    pixel_size = int(min(size[0] / m_width, size[1] / m_height))
    background = Image.new('RGB', (m_width * pixel_size, m_height * pixel_size))

    lookup_data = load_lookup_data()
    for i in range(m_height):
        for j in range(m_width):
            print(f"{int((i*m_width+j)/(m_width * m_height)*100)}% Done")

            color = color_matrix[i][j]
            pixel_image_name = get_image_using_lookup(lookup_data, color, random_score)
            pixel_image = Image.open(f"{SOURCE_IMAGES}/{pixel_image_name}")
            pixel_image = pixel_image.resize((pixel_size, pixel_size))
            offset = (j * pixel_size, i * pixel_size)
            background.paste(pixel_image, offset)
    return background


def get_nice_timestamp():
    result = f"{datetime.datetime.now()}"
    result = result.replace(' ', '_at_')
    result = result.replace(':', '-')
    parts = result.split('.')
    result = parts[0]
    return result


def convert_image(path, matrix_size=(75, 75), image_size=(2000, 2000), random_score=50, save_path=None):
    color_matrix = get_input_matrix(path, size=matrix_size)
    result = build_image(color_matrix, size=image_size, random_score=random_score)
    if save_path is None:
        save_path = f'{OUTPUT}/{get_nice_timestamp()}.png'
    result.save(save_path)


if __name__ == '__main__':
    img_paths = list(pathlib.Path(IMAGE_INPUT).iterdir())
    for img_path in img_paths:
        print(img_path)
        convert_image(img_path)

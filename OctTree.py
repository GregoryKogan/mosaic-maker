import pathlib
import random
from PIL import Image
import json
from config import *


def boundary_contains(boundary, color):
    r, g, b = color
    return boundary['r'][0] <= r <= boundary['r'][1] and \
           boundary['g'][0] <= g <= boundary['g'][1] and \
           boundary['b'][0] <= b <= boundary['b'][1]


def get_total_item_count(oct_tree_data):
    if not oct_tree_data['divided']:
        return len(oct_tree_data['items'])
    else:
        total = 0
        for child_key in oct_tree_data['children']:
            total += get_total_item_count(oct_tree_data['children'][child_key])
        return total


def get_all_items(oct_tree_data):
    if not oct_tree_data['divided']:
        return oct_tree_data['items']
    else:
        result = []
        for child_key in oct_tree_data['children']:
            result.extend(get_all_items(oct_tree_data['children'][child_key]))
        return result


def get_image_using_lookup(lookup_data, color, random_score=50):
    current_root = lookup_data
    parent = None
    while current_root['divided']:
        for child_key in current_root['children']:
            if boundary_contains(current_root['children'][child_key]['boundary'], color):
                parent = current_root
                current_root = current_root['children'][child_key]
                break
    items = current_root['items']
    if len(items) == 0:
        if parent:
            for brother_key in parent['children']:
                items.extend(get_all_items(parent['children'][brother_key]))
        else:
            return None
    for i, item in enumerate(items):
        img_color = item['color']
        dist = ((color[0] - img_color[0]) ** 2 +
                (color[1] - img_color[1]) ** 2 +
                (color[2] - img_color[2]) ** 2) ** 0.5
        items[i]['dist'] = dist
    items.sort(key=lambda x: x['dist'])
    items = items[:min(random_score, len(items))]
    pick = random.choice(items)
    return pick['filename']


class OctTree:
    def __init__(self, capacity=30, parent=None, boundary=None):
        if boundary is None:
            boundary = {'r': [0, 255], 'g': [0, 255], 'b': [0, 255]}
        self.boundary = boundary
        self.parent = parent
        self.items = []
        self.divided = False
        self.capacity = capacity
        self.children = {}

    def get_json(self):
        children_json = {}
        if self.divided:
            for child_key in self.children:
                children_json[child_key] = self.children[child_key].get_json()

        return {
            "id": f"{random.randint(1, int(1e20))}",
            "boundary": self.boundary,
            "items": self.items,
            "divided": self.divided,
            "children": children_json,
        }

    def serialize(self):
        data = self.get_json()
        with open(LOOKUP_FILENAME, 'w', encoding='utf-8') as outfile:
            json.dump(data, outfile, indent=2)

    def contains(self, color):
        r, g, b = color
        return self.boundary['r'][0] <= r <= self.boundary['r'][1] and \
               self.boundary['g'][0] <= g <= self.boundary['g'][1] and \
               self.boundary['b'][0] <= b <= self.boundary['b'][1]

    def insert(self, img_item):
        if not self.divided and len(self.items) < self.capacity:
            self.items.append(img_item)
        elif self.divided:
            img_color = img_item['color']
            for child_key in self.children:
                if self.children[child_key].contains(img_color):
                    self.children[child_key].insert(img_item)
                    break
        else:
            self.divided = True
            r_l, r_r, = self.boundary['r']
            g_l, g_r, = self.boundary['g']
            b_l, b_r, = self.boundary['b']
            r_m = (r_l + r_r) / 2
            g_m = (g_l + g_r) / 2
            b_m = (b_l + b_r) / 2

            self.children['tlf'] = OctTree(capacity=self.capacity, parent=self, boundary={
                'r': [r_m, r_r], 'g': [g_l, g_m], 'b': [b_m, b_r]
            })
            self.children['trf'] = OctTree(capacity=self.capacity, parent=self, boundary={
                'r': [r_m, r_r], 'g': [g_m, g_r], 'b': [b_m, b_r]
            })
            self.children['blf'] = OctTree(capacity=self.capacity, parent=self, boundary={
                'r': [r_l, r_m], 'g': [g_l, g_m], 'b': [b_m, b_r]
            })
            self.children['brf'] = OctTree(capacity=self.capacity, parent=self, boundary={
                'r': [r_l, r_m], 'g': [g_m, g_r], 'b': [b_m, b_r]
            })
            self.children['tln'] = OctTree(capacity=self.capacity, parent=self, boundary={
                'r': [r_m, r_r], 'g': [g_l, g_m], 'b': [b_l, b_m]
            })
            self.children['trn'] = OctTree(capacity=self.capacity, parent=self, boundary={
                'r': [r_m, r_r], 'g': [g_m, g_r], 'b': [b_l, b_m]
            })
            self.children['bln'] = OctTree(capacity=self.capacity, parent=self, boundary={
                'r': [r_l, r_m], 'g': [g_l, g_m], 'b': [b_l, b_m]
            })
            self.children['brn'] = OctTree(capacity=self.capacity, parent=self, boundary={
                'r': [r_l, r_m], 'g': [g_m, g_r], 'b': [b_l, b_m]
            })

            for item in self.items:
                img_color = item['color']
                for child_key in self.children:
                    if self.children[child_key].contains(img_color):
                        self.children[child_key].insert(item)
                        break
            self.items = []

            img_color = img_item['color']
            for child_key in self.children:
                if self.children[child_key].contains(img_color):
                    self.children[child_key].insert(img_item)
                    break


def get_average_color(img):
    img_resized = img.resize((1, 1))
    color = img_resized.getpixel((0, 0))
    return color


def create_lookup(limit=100_000, oct_tree_capacity=30):
    oct_tree = OctTree(capacity=oct_tree_capacity)

    img_count = len(list(pathlib.Path("source").iterdir()))
    for img_i, path in enumerate(pathlib.Path("source").iterdir(), start=1):
        if img_i > limit:
            break
        print(f"Indexing... {img_i}/{img_count}")

        img = Image.open(path)
        color = get_average_color(img)
        img_item = {
            "filename": path.name,
            "color": color,
        }
        oct_tree.insert(img_item)

    oct_tree.serialize()


if __name__ == "__main__":
    create_lookup(limit=100_000, oct_tree_capacity=200)
    # with open(LOOKUP_FILENAME, 'r') as lookup_file:
    #     lookup_data = json.load(lookup_file)
    # img_file = get_image_using_lookup(lookup_data, (0, 0, 0))
    # print(img_file)
    # img = Image.open(f'source/{img_file}')
    # img.show()

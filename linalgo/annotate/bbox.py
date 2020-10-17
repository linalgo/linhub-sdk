from typing import List

from PIL import Image, ImageDraw


class Vertex:

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self):
        return f'({self.x}, {self.y})'


class BoundingBox:

    def __init__(self, left, right, top, bottom):
        self.left = left
        self.right = right
        self.top = top
        self.bottom = bottom

    @staticmethod
    def fromVertex(v: Vertex, height: float, width: float):
        left = min(v.x, v.x + width)  # width and height can be negative
        right = max(v.x, v.x + width)
        top = min(v.y, v.y + height)
        bottom = max(v.y, v.y + height)
        return BoundingBox(left, right, top, bottom)

    @staticmethod
    def fromVertices(vertices: List[Vertex]):
        left = min(p.x for p in vertices)
        right = max(p.x for p in vertices)
        top = min(p.y for p in vertices)
        bottom = max(p.y for p in vertices)
        return BoundingBox(left=left, right=right, bottom=bottom, top=top)

    @property
    def height(self):
        return self.bottom - self.top

    @property
    def width(self):
        return self.right - self.left

    @property
    def area(self):
        return self.height * self.width

    @property
    def vertices(self):
        return [
            Vertex(self.left, self.top), Vertex(self.right, self.top),
            Vertex(self.right, self.bottom), Vertex(self.left, self.bottom)
        ]

    def contains(self, bbox):
        return (self.top <= bbox.top and self.bottom >= bbox.bottom and
                self.left <= bbox.left and self.right >= bbox.right)

    def intersects(self, bbox):
        c1 = not ((self.top > bbox.bottom) or (bbox.top > self.bottom))
        c2 = not ((self.right < bbox.left) or (bbox.right < self.left))
        return c1 and c2

    def intersection(self, bbox):
        if not self.intersects(bbox):
            return BoundingBox(0, 0, 0, 0)
        left = max(self.left, bbox.left)
        bottom = min(self.bottom, bbox.bottom)
        right = min(self.right, bbox.right)
        top = max(self.top, bbox.top)
        return BoundingBox(left, right, top, bottom)

    def overlap(self, bbox):
        if self.area <= 0:
            return 0
        intersection = self.intersection(bbox)
        return intersection.area / self.area

    def __repr__(self):
        return f"{{{', '.join(f'{v}' for v in self.vertices)}}}"


def draw_bounding_boxes(image: Image, annotations: List):
    """
    Draw bounding boxes on an image

    :param image: Image to annotate
    :param annotations: A list of BoundingBox objects
    :param color: The color of the bounding box
    :return: The annotated image
    """
    draw = ImageDraw.Draw(image)
    for annotation in annotations:
        box = annotation.target.selectors[0]
        draw.polygon([
            box.vertices[0].x, box.vertices[0].y,
            box.vertices[1].x, box.vertices[1].y,
            box.vertices[2].x, box.vertices[2].y,
            box.vertices[3].x, box.vertices[3].y],
            None, f'#{annotation.entity.color}')
    return image


if __name__ == '__main__':
    a = BoundingBox(left=0, right=4, top=0, bottom=4)
    b = BoundingBox.fromVertex(Vertex(2, 3), height=1, width=1)
    c = BoundingBox(left=6, right=7, top=6, bottom=7)
    print(a, b)
    print(a.contains(b))
    print(a.intersection(b).area)
    print(a.area)
    print(a.overlap(b))
    print(a.intersects(b))
    print(a.intersects(c))
    print(a.intersection(b).area)
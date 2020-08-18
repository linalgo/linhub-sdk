from typing import Dict, List
from enum import Enum
from google.cloud.vision_v1.types import TextAnnotation

from bbox import BoundingBox, Vertex
from linalgo.annotate import Task


def get_google_boxes(document: TextAnnotation) -> List[Dict]:
    """
    Extract bounding boxes from a Google Vision annotated image

    :param document: The annotations made by Google Vision API
    :return:
    """
    bboxes = []
    for page in document.pages:
        for block in page.blocks:
            for paragraph in block.paragraphs:
                for word in paragraph.words:
                    text = ''
                    for symbol in word.symbols:
                        text += symbol.text
                    bbox = word.bounding_box
                    bbox = BoundingBox.fromVertices(bbox.vertices)
                    bboxes.append({
                        'text': text,
                        'bbox': bbox,
                        'color': 'yellow',
                        'type': 'google'
                    })
    return bboxes


def get_linalgo_boxes(task: Task, image: str) -> List[Dict]:
    """
    Extract bounding boxes from LinHub task

    :param task: A linhub task
    :return:
    """
    for doc in task.documents:
        if image in doc.content:
            doc_id = doc.id
    annotations = []
    for annotation in task.annotations:
        if annotation.document_id == doc_id:
            label = annotation.type_id
            for e in task.entities:
                if e['id'] == annotation.type_id:
                    color = f"#{e['color']}"
            box = annotation.target['selector'][0]
            box = BoundingBox.fromVertex(
                Vertex(box['x'], box['y']),
                height=box['height'],
                width=box['width']
            )
            annotations.append({
                'text': label,
                'bbox': box,
                'color': color,
                'type': task.get_name(annotation.type_id)
            })
    return annotations

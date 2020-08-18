from .bbox import BoundingBox


class Serializer:

    def __init__(self, instance):
        self.instance = instance
        self.many = hasattr(instance, '__len__')

    def serialize(self):
        if self.many:
            return [self._serialize(i) for i in self.instance]
        return self._serialize(self.instance)


class BoundingBoxSerializer(Serializer):

    @staticmethod
    def _serializer(instance):
        s = {
            'vertex': instance.vertex,
            'height': instance.height,
            'width': instance.width
        }
        return s


class SelectorSerializerFactory:

    @staticmethod
    def create(instance):
        if type(instance) == BoundingBox:
            return BoundingBoxSerializer(instance)
        else:
            return {}


class TargetSerializer(Serializer):

    @staticmethod
    def _serialize(target):
        selector_serializer = SelectorSerializerFactory(target.selectors)
        s = {
            'source': target.source,
            'selectors': selector_serializer.serialize()
        }
        return s


class AnnotationSerializer(Serializer):

    @staticmethod
    def _serialize(instance):
        annotator_id = None
        if instance.annotator is not None:
            annotator_id = instance.annotator.id
        target = None
        if instance.target is not None:
            target_serializer = TargetSerializer(instance.target)
            target = target_serializer.serialize()
        s = {
            'entity': instance.entity.id,
            'body': instance.body,
            'annotator': annotator_id,
            'document': instance.document.id,
            'created': getattr(instance, 'created', lambda: None),
            'target': target,
            'score': getattr(instance, 'score', lambda: None)
        }
        return s
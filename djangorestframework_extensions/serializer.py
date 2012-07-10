from djangorestframework.serializer import Serializer


class IDListSerializer(Serializer):
    def serialize(self, obj):
        return [x.id for x in obj.all()]

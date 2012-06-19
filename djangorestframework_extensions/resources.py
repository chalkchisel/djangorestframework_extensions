from django.db.models import Manager, Model
from django.db.models.base import ModelBase
from django.db.models.fields.files import FieldFile
from djangorestframework.resources import Resource as _OriginalResource
from djangorestframework.serializer import _RegisterSerializer, Serializer

_model_resources = {}


class _RegisterDefaultResource(_RegisterSerializer):
    """
    Metaclass to register default serializers for a model.
    """
    def __new__(cls, name, bases, attrs):
        ret = super(_RegisterDefaultResource, cls).__new__(
            cls, name, bases, attrs)

        # Prevent OnTheFlySerializers from displacing the default
        if ret.model and ret.model not in _model_resources:
            _model_resources[ret.model] = ret
        return ret


class FileFieldURLMixin(object):
    def serialize(self, obj):
        if isinstance(obj, FieldFile):
            return self.serialize_fallback(obj.url)
        else:
            return super(FileFieldURLMixin, self).serialize(obj)


class DynamicSerializerMixin(object):
    def get_related_serializer(self, info):
        serializer = super(DynamicSerializerMixin, self).get_related_serializer(info)
        if serializer == Serializer:
            return DynamicSerializer
        else:
            return serializer

    def serialize_val(self, key, obj, related_info):
        """
        Override the Serializer method serialize_val to pass the view to the
        related_serializer.
        """
        related_serializer = self.get_related_serializer(related_info)

        if self.depth is None:
            depth = None
        elif self.depth <= 0:
            return self.serialize_max_depth(obj)
        else:
            depth = self.depth - 1

        if any([obj is elem for elem in self.stack]):
            return self.serialize_recursion(obj)
        else:
            stack = self.stack[:]
            stack.append(obj)

        try:
            ser_obj = related_serializer(view=self.view, depth=depth, stack=stack)
        except TypeError:
            ser_obj = related_serializer(depth=depth, stack=stack)

        return ser_obj.serialize(obj)


class DynamicSerializer(DynamicSerializerMixin, FileFieldURLMixin, _OriginalResource):
    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs
        super(DynamicSerializer, self).__init__(*args, **kwargs)

    def serialize(self, obj):
        if type(obj) == ModelBase:
            key = obj
        elif isinstance(obj, Model):
            key = type(obj)
        elif isinstance(obj, Manager):
            key = obj.model
        else:
            key = None

        dynamic = _model_resources.get(key, None)

        if dynamic:
            dynamic = dynamic(*self._args, **self._kwargs)
        else:
            dynamic = super(DynamicSerializer, self)

        return dynamic.serialize(obj)

    def serialize_iter(self, obj):
        return [self.serialize(item) for item in obj]


class Resource(DynamicSerializerMixin, _OriginalResource):
    pass


class DefaultResource(Resource):
    __metaclass__ = _RegisterDefaultResource

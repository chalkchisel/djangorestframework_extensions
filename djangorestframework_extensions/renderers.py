import datetime
import decimal
import json
from django.utils import simplejson
from django.utils.timezone import is_aware
from djangorestframework.renderers import DefaultRenderers, BaseRenderer, \
    JSONRenderer, JSONPRenderer
from djangorestframework.utils.mediatypes import get_media_type_params

__all__ = ['NoMicrosecondsJSONEncoder', ]


class NoMicrosecondsJSONEncoder(simplejson.JSONEncoder):
    """
    JSONEncoder subclass that knows how to encode date/time and decimal types.
    """
    def default(self, o):
        # See "Date Time String Format" in the ECMA-262 specification.
        if isinstance(o, datetime.datetime):
            r = o.isoformat()
            if o.microsecond:
                r = r[:19] + r[26:]
            if r.endswith('+00:00'):
                r = r[:-6] + 'Z'
            return r
        elif isinstance(o, datetime.date):
            return o.isoformat()
        elif isinstance(o, datetime.time):
            if is_aware(o):
                raise ValueError("JSON can't represent timezone-aware times.")
            r = o.isoformat()
            if o.microsecond:
                r = r[:8]
            return r
        elif isinstance(o, decimal.Decimal):
            return str(o)
        else:
            return super(NoMicrosecondsJSONEncoder, self).default(o)


class NoMicrosecondsJSONRenderer(BaseRenderer):
    # THIS IS A FORK OF djangorestframework.renderers.JSONRenderer
    """
    Renderer which serializes to JSON
    """

    media_type = 'application/json'
    format = 'json'

    def render(self, obj=None, media_type=None):
        """
        Renders *obj* into serialized JSON.
        """
        if obj is None:
            return ''

        # If the media type looks like 'application/json; indent=4', then
        # pretty print the result.
        indent = get_media_type_params(media_type).get('indent', None)
        sort_keys = False
        try:
            indent = max(min(int(indent), 8), 0)
            sort_keys = True
        except (ValueError, TypeError):
            indent = None

        return json.dumps(obj, cls=NoMicrosecondsJSONEncoder, indent=indent,
            sort_keys=sort_keys)


class NoMicrosecondsJSONPRenderer(NoMicrosecondsJSONRenderer):
    # THIS IS A FORK OF djangorestframework.renderers.JSONPRenderer
    """
    Renderer which serializes to JSONP
    """

    media_type = 'application/json-p'
    format = 'json-p'
    renderer_class = JSONRenderer
    callback_parameter = 'callback'

    def _get_callback(self):
        return self.view.request.GET.get(self.callback_parameter,
            self.callback_parameter)

    def _get_renderer(self):
        return self.renderer_class(self.view)

    def render(self, obj=None, media_type=None):
        callback = self._get_callback()
        json = self._get_renderer().render(obj, media_type)
        return "%s(%s);" % (callback, json)

orig = DefaultRenderers.DEFAULT_VALUE
new = []
for r in orig:
    if r == JSONRenderer:
        new.append(NoMicrosecondsJSONRenderer)
    elif r == JSONPRenderer:
        new.append(NoMicrosecondsJSONPRenderer)
    else:
        new.append(r)

DefaultRenderers.DEFAULT_VALUE = tuple(new)

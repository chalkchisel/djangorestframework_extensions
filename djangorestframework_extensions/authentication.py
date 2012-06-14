from django.conf import settings
from django.utils.importlib import import_module

_AUTHENTICATION_DEFAULTS = (
    'djangorestframework.authentication.UserLoggedInAuthentication',
    'djangorestframework.authentication.BasicAuthentication',
)


class LazyDefaultAuthentication(object):
    cached = None

    def __iter__(self):
        if self.cached is None:
            self.fill_cache()
        return self.cached.__iter__()

    def __add__(self, b):
        if self.cached is None:
            self.fill_cache()
        return self.cached.__add__(b)

    def load_authenticator(self, importpath):
        try:
            mod_name, classname = importpath.rsplit('.', 1)
            mod = import_module(mod_name)
            return getattr(mod, classname)
        except ValueError:
            raise exceptions.ImproperlyConfigured("%s isn't an authenticator module" % importpath)
        except ImportError, e:
            raise exceptions.ImproperlyConfigured('Error importing authenticator %s: "%s"' % (mod_name, e))
        except AttributeError:
            raise exceptions.ImproperlyConfigured('Authenticator module "%s" does not define a "%s" class' % (mod_name, classname))

    def fill_cache(self):
        authenticators = []
        for authenticator in getattr(settings, "REST_DEFAULT_AUTHENTICATION",
                _AUTHENTICATION_DEFAULTS):
            authenticators.append(self.load_authenticator(authenticator))
        self.cached = tuple(authenticators)


DEFAULT_AUTHENTICATION = LazyDefaultAuthentication()

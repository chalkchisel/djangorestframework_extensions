from djangorestframework.mixins import ModelMixin, CreateModelMixin, \
    UpdateModelMixin
from djangorestframework_extensions.utils import user_passes_test

__all__ = ['RoleBasedExclusion', 'RestrictedModelMixin',
    'RestrictedCreateModelMixin', 'RestrictedUpdateModelMixin']


class RoleBasedExclusion(object):

    def role_based_exclusion(self):
        exclude = self.exclude
        if not isinstance(exclude, dict):
            return exclude or ()

        user = getattr(self.request, 'user', None)

        if user:
            if user.is_superuser:
                return exclude.get('superuser', ())
            elif user.is_staff:
                return exclude.get('staff', ())

            for test, exclusion in exclude.get('roles', ()):
                if user_passes_test(user, test):
                    return exclusion

        return exclude[None]

    def get_fields(self, obj):
        fields = self.fields

        # If `fields` is not set, we use the default fields and modify
        # them with `include` and `exclude`
        if not fields:
            default = self.get_default_fields(obj)
            include = self.include or ()
            exclude = self.role_based_exclusion() or ()
            fields = set(default + list(include)) - set(exclude)

        return fields


class RestrictedModelMixin(RoleBasedExclusion, ModelMixin):
    pass


class RestrictedCreateModelMixin(RestrictedModelMixin, CreateModelMixin):
    def post(self, request, *args, **kwargs):
        pass


class RestrictedUpdateModelMixin(RestrictedModelMixin, UpdateModelMixin):
    def put(self, request, *args, **kwargs):
        pass

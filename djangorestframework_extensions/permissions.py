from django.contrib.auth.models import User, Group
from djangorestframework import status
from djangorestframework.response import ErrorResponse
from djangorestframework.permissions import SAFE_METHODS, BasePermission
from djangorestframework_extensions.utils import user_passes_test

__all__ = (
    'IsStaffOrIsAnonReadOnly',
)


class InstancePermission(BasePermission):
    def get_instance(self):
        view = self.view
        if getattr(view, 'model_instance', None):
            return view.model_instance
        else:
            model = view.resource.model
            query_kwargs = view.get_query_kwargs(view.request, *view.args,
                **view.kwargs)

            try:
                # TODO: Update django-rest-framework to take advantage of
                #       the fact that model_instance already exists.
                view.model_instance = view.get_instance(**query_kwargs)
                return view.model_instance
            except model.DoesNotExist:
                raise ErrorResponse(status.HTTP_404_NOT_FOUND)


class BaseWhitelistPermission(BasePermission):
    whitelist = True


class PassesTestPermission(object):
    def __init__(self, test):

        class WrappedPassesTestPermission(BaseWhitelistPermission):
            pass

        self.wrapped = WrappedPassesTestPermission

    def __call__(self, *args, **kwargs):
        return self.wrapped(*args, **kwargs)


class WhitelistPermissions(BasePermission):
    DEFAULT_PERMISSIONS = (
        ('superuser', lambda x: x.is_superuser),
        ('staff', lambda x: x.is_staff),
    )

    DEFAULT_PERMISSION_KEYS = dict(DEFAULT_PERMISSIONS).keys()

    def check_permission(self, user):
        perms = getattr(self.view, 'whitelist_permissions', [])
        if isinstance(perms, dict):
            if self.check_permission_dict(user, perms):
                return True
        elif perms is True:
            return True
        else:
            if self.check_permission_list(user, perms):
                return True

        raise ErrorResponse(status.HTTP_403_FORBIDDEN, {'detail':
            'You do not have permission to access this resource.'})

    def check_permission_dict(self, user, permissions):
        # First check the staff-level permissions to see if they apply
        for key, test in self.DEFAULT_PERMISSIONS:
            if key in permissions and test(user):
                if self.check_permission_list(user, permissions[key]):
                    return True

        # Then test all other permissions
        for test, perms in permissions:
            if test not in self.DEFAULT_PERMISSION_KEYS and user_passes_test(user, test):
                if self.check_permission_list(user, perms):
                    return True

    def check_permission_list(self, user, permissions):
        view = self.view

        if permissions is True:
            return True

        for permission_cls in permissions:
            if callable(permission_cls):
                permission = permission_cls(view)
                if not permission.whitelist:
                    raise ErrorResponse(501, {'detail':
                        "Improper server permissions configuration. " +
                        "Please contact the site administrator."})
                if permission.check_permission(user):
                    return True
            elif isinstance(permission_cls, basestring):
                if view.method == permission_cls.upper():
                    return True


class StaffOrWhitelistPermissions(WhitelistPermissions):
    def check_permission(self, user):
        if user.is_staff:
            return True
        else:
            return super(StaffOrWhitelistPermissions, self).check_permission(user)


class IsStaffOrIsAnonReadOnly(BasePermission):
    """
    The request is authenticated as staff, or is a read-only request.
    """

    def check_permission(self, user):
        if (not user.is_staff and
            self.view.method not in SAFE_METHODS):
            raise ErrorResponse(status.HTTP_403_FORBIDDEN,
                {'detail':
                    'You do not have permission to access this resource. ' +
                    'Only staff members may perform the requested action.'})


class IsStaff(BaseWhitelistPermission):
    def check_permission(self, user):
        return user.is_staff


class IsSuperuser(BaseWhitelistPermission):
    def check_permission(self, user):
        return user.is_superuser


class IsOwner(InstancePermission, BaseWhitelistPermission):
    def check_permission(self, user):
        instance = self.get_instance()
        attr_field = getattr(self.view, 'owner_attr', 'user')
        if hasattr(instance, attr_field + "_id"):
            return getattr(instance, attr_field + "_id") == user.id
        else:
            return getattr(instance, attr_field) == user


class AllowRead(BaseWhitelistPermission):
    def check_permission(self, user):
        if self.view.method in SAFE_METHODS:
            return True

PERMISSION_LOOKUP = {
    'GET': 'view',
    'HEAD': 'view',
    'OPTIONS': 'view',
    'POST': 'add',
    'PUT': 'change',
    'DELETE': 'delete'
}


class DefaultPermissions(InstancePermission, BaseWhitelistPermission):
    def check_permission(self, user):
        action = PERMISSION_LOOKUP.get(self.view.method, "NONE")
        meta = self.view.resource.model._meta
        permission = "%s.%s_%s" % (meta.app_label, action, meta.object_name.lower())
        return user.has_perm(permission)

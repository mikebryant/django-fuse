from django_fuse import DirectoryResponse, FileResponse, SymlinkResponse, RelativeSymlinkResponse
from django.db.models import get_models, get_app, get_model, FileField, FilePathField, ForeignKey, ManyToManyField, OneToOneField
from django.contrib.contenttypes.generic import GenericForeignKey
from django.core.exceptions import ImproperlyConfigured
import errno
from django.core.urlresolvers import reverse
from fuse import FuseOSError

def index():
    return DirectoryResponse(["proc"])

def app_list():
    return DirectoryResponse(set([x._meta.app_label for x in get_models()]))

def model_list(app):
    try:
        return DirectoryResponse([model._meta.object_name for model in get_models(get_app(app))])
    except ImproperlyConfigured:
        raise FuseOSError(errno.ENOENT)

def model_index(app, model):
    if get_model(app, model):
        return DirectoryResponse(["by-pk"])
    else:
        raise FuseOSError(errno.ENOENT)

def all_instances(app, model):
    m = get_model(app, model)
    if m:
        def items():
            for x in m.objects.all():
                yield str(x.id)

        return DirectoryResponse(items, m.objects.all().count)
    else:
        raise FuseOSError(errno.ENOENT)

def fields_for_model(app, model, pk):
    m = get_model(app, model)
    if m:
        try:
            instance = m.objects.get(pk=pk)
            return DirectoryResponse([x.name for x in m._meta.fields])
        except (m.DoesNotExist, ValueError):
            raise FuseOSError(errno.ENOENT)
    else:
        raise FuseOSError(errno.ENOENT)

#FileField, FilePathField, ForeignKey, ManyToManyField, OneToOneField

def symlink_for_instance(instance):
    if instance is None:
        return SymlinkResponse("/dev/null")
    else:
        args = {
            'app': instance._meta.app_label,
            'model': instance._meta.object_name,
            'pk': instance.pk,
        }
        url = reverse(fields_for_model,kwargs=args,urlconf='fsapi.urls')
        return RelativeSymlinkResponse(url)

def modelfield_by_pk(app, model, pk, field):
    m = get_model(app, model)
    if m and field in [x.name for x in m._meta.fields]:
        try:
            instance = m.objects.get(pk=pk)
            fieldobj = instance._meta.get_field_by_name(field)[0]
            if isinstance(fieldobj, FileField):
                raise FuseOSError(errno.ENOSYS)
            elif isinstance(fieldobj, FilePathField):
                raise FuseOSError(errno.ENOSYS)
            elif isinstance(fieldobj, ForeignKey) or isinstance(fieldobj, GenericForeignKey) or isinstance(fieldobj, OneToOneField):
                return symlink_for_instance(getattr(instance, field))
            elif isinstance(fieldobj, ManyToManyField):
                raise FuseOSError(errno.ENOSYS)
            else:
                return FileResponse(str(getattr(instance, field)) + "\n")
        except (m.DoesNotExist, ValueError):
            raise FuseOSError(errno.ENOENT)
    else:
        raise FuseOSError(errno.ENOENT)

from django_fuse import DirectoryResponse, FileResponse, SymlinkResponse, RelativeSymlinkResponse
from django.db.models import get_models, get_app, get_model, FileField, FilePathField, ForeignKey, ManyToManyField, OneToOneField
from django.contrib.contenttypes.generic import GenericForeignKey
from django.core.exceptions import ImproperlyConfigured
import errno
from django.core.urlresolvers import reverse
from django.conf import settings

class NotFoundError(OSError):
    errno = errno.ENOENT

class OpNotImplemented(OSError):
    errno = errno.ENOSYS

def index():
    return DirectoryResponse(["proc"])

def app_list():
    return DirectoryResponse(set([x._meta.app_label for x in get_models()]))

def model_list(app):
    try:
        return DirectoryResponse([model._meta.object_name for model in get_models(get_app(app))])
    except ImproperlyConfigured:
        raise NotFoundError

def model_index(app, model):
    if get_model(app, model):
        return DirectoryResponse(["by-pk"])
    else:
        raise NotFoundError

def all_instances(app, model):
    m = get_model(app, model)
    if m:
        def items():
            for x in m.objects.all():
                yield str(x.id)

        return DirectoryResponse(items, m.objects.all().count)
    else:
        raise NotFoundError

def fields_for_model(app, model, pk):
    m = get_model(app, model)
    if m:
        try:
            instance = m.objects.get(pk=pk)
            return DirectoryResponse([x.name for x in m._meta.fields])
        except (m.DoesNotExist, ValueError):
            raise NotFoundError
    else:
        raise NotFoundError

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
        url = reverse(fields_for_model,kwargs=args,urlconf=settings.FUSE_URLCONF)
        return RelativeSymlinkResponse(url)

def modelfield_by_pk(app, model, pk, field):
    m = get_model(app, model)
    if m and field in [x.name for x in m._meta.fields]:
        try:
            instance = m.objects.get(pk=pk)
            fieldobj = instance._meta.get_field_by_name(field)[0]
            if isinstance(fieldobj, FileField):
                raise OpNotImplemented
            elif isinstance(fieldobj, FilePathField):
                raise OpNotImplemented
            elif isinstance(fieldobj, ForeignKey) or isinstance(fieldobj, GenericForeignKey) or isinstance(fieldobj, OneToOneField):
                return symlink_for_instance(getattr(instance, field))
            elif isinstance(fieldobj, ManyToManyField):
                raise OpNotImplemented
            else:
                return FileResponse(str(getattr(instance, field)) + "\n")
        except (m.DoesNotExist, ValueError):
            raise NotFoundError
    else:
        raise NotFoundError

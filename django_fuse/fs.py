# -*- coding: utf-8 -*-

# django-fuse -- FUSE adaptor for Django
# Copyright (C) 2008 Chris Lamb <chris@chris-lamb.co.uk>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import fuse
import errno

from django.conf import settings
from django.core.urlresolvers import resolve, Resolver404

from fuse import FUSE, FuseOSError, Operations, LoggingMixIn

__all__ = ('DjangoFs',)

def render(fn):
    def wrapped(self, path, *args, **kwargs):
        try:
            # Resolve requested URL to a view and "render" it.
            view_fn, view_args, view_kwargs = \
                resolve(path, urlconf=self.urlconf)
            response = view_fn(*view_args, **view_kwargs)

            # Pass the response as the first argument, replacing
            # 'path' from the callsite in fuse.py
            return fn(self, response, *args, **kwargs)

        except Resolver404:
            # Path does not exist
            raise FuseOSError(errno.ENOENT)

    return wrapped

class DjangoOperations(Operations):
    def __init__(self, mountpoint, urlconf):
        self.mountpoint = mountpoint
        self.urlconf = urlconf
        self.fd = 0
        self.fileobjs = {}

    @render
    def getattr(self, response, fh=None):
        return response.getattr(self)

    @render
    def readdir(self, response, fh=None):
        return response.readdir(self)

    @render
    def open(self, response, flags):
        obj = response.open(self, flags)
        self.fd += 1
        self.fileobjs[self.fd] = obj
        return self.fd

    @render
    def unlink(self, response):
        return response.unlink(self)

    @render
    def access(self, response, mode):
        return response.access(self, mode)

    @render
    def rename(self, response, target):
        return response.rename(self, target)

    @render
    def readlink(self, response):
        return response.readlink(self)

    # Stateful-file calls - no need to route them as we have already created
    # a stateful object fileobj for these.

    def read(self, path, length, offset, fh):
        fileobj = self.fileobjs[fh]
        return fileobj.read(length, offset)

    def release(self, path, fh):
        fileobj = self.fileobjs.pop(fh)
        return fileobj.release()

def runfs(mountpoint, urlconf, foreground=False, verbose=False):
    if verbose:
        class Operations(LoggingMixIn, DjangoOperations):
            pass
    else:
        Operations = DjangoOperations
    return FUSE(operations=Operations(mountpoint, urlconf), mountpoint=mountpoint, foreground=foreground) 

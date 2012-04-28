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

import sys
import fuse

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
from django.core.urlresolvers import resolve

from django_fuse.fs import runfs

class Command(BaseCommand):
    args = '<mountpoint>'
    option_list = BaseCommand.option_list + (
        make_option('--foreground','-f',
            action='store_true',
            dest='foreground',
            default=False,
            help='Keep in the foreground'),
        make_option('--urlconf','-u',
            action='store',
            type='string',
            dest='urlconf',
            default='',
            help='Urlconf to use'),
        )
    def handle(self, *args, **options):
        urlconf = options['urlconf'] or getattr(settings, 'FUSE_URLCONF', None)
        if not urlconf:
            raise CommandError("You need to pass a urlconf to this command or set FUSE_URLCONF to use django-fuse.")
        verbose = options['verbosity'] > 1

        if len(args) != 1:
            raise CommandError("You need to pass one argument, the mountpoint")

        try:
            resolve('/', urlconf=urlconf)
        except ImportError:
            raise CommandError("Couldn't find the given urlconf")

        try:
            runfs(args[0], urlconf, verbose=verbose, foreground=options['foreground'])
        except RuntimeError:
            raise CommandError("Fuse error, see above")

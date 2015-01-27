# -*- coding: utf-8 -*-
# This file is part of beets.
# Copyright 2015, Bruno Cauet
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

"""Create freedesktop.org-compliant thumnails for album folders"""

from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

from hashlib import md5
import os
import shutil
from pathlib import PurePosixPath

from xdg import BaseDirectory

from beets.plugins import BeetsPlugin
from beets.ui import Subcommand, decargs
from beets.util import syspath
from beets.util.artresizer import ArtResizer


BASE_DIR = os.path.join(BaseDirectory.xdg_cache_home, "thumbnails")
NORMAL_DIR = os.path.join(BASE_DIR, "normal")
LARGE_DIR = os.path.join(BASE_DIR, "large")


class ThumbnailsPlugin(BeetsPlugin):
    def __init__(self):
        super(ThumbnailsPlugin, self).__init__()
        if self._check_local_ok():
            self.register_listener('album_imported', self.imported)

    def commands(self):
        thumbnails_command = Subcommand("thumbnails",
                                        help="Create album thumbnails")
        thumbnails_command.func = self.process_query
        return [thumbnails_command]

    def imported(self, lib, album):
        self.process_album(album)

    def process_query(self, lib, opts, args):
        if self._check_local_ok():
            for album in lib.albums(decargs(args)):
                self.process_album(album)

    def _check_local_ok(self):
        if not ArtResizer.local:
            self._log.warning("No local image resizing capabilities, "
                              "cannot generate thumbnails")
            return False

        for dir in (NORMAL_DIR, LARGE_DIR):
            if not os.path.exists(dir):
                os.makedirs(dir)

        return True

    def process_album(self, album):
        """Produce thumbnails for the album folder.
        """
        if not album.artpath:
            self._log.info(u'album {0} has no art', album)
            return

        size = ArtResizer.shared.get_size(album.artpath)
        if not size:
            self._log.warning('Problem getting the picture size for {0}',
                              album.artpath)
            return

        if max(size):
            self.make_cover_thumbnail(album, 256, LARGE_DIR)
        self.make_cover_thumbnail(album, 128, NORMAL_DIR)

        self._log.info(u'wrote thumbnail for {0}', album)

    def make_cover_thumbnail(self, album, size, target_dir):
        """Make a thumbnail of given size for `album` and put it in
        `target_dir`.
        """
        self._log.debug("Building thumbnail to put on {0}", album.path)
        target = os.path.join(target_dir, self.thumbnail_file_name(album.path))
        resized = ArtResizer.shared.resize(size, album.artpath,
                                           syspath(target))

        # FIXME should add tags
        # see http://standards.freedesktop.org/thumbnail-spec/latest/x142.html

        shutil.move(resized, target)

    @staticmethod
    def thumbnail_file_name(path):
        # http://standards.freedesktop.org/thumbnail-spec/latest/x227.html
        uri = PurePosixPath(path).as_uri()
        hash = md5(uri).hexdigest()
        return "{0}.png".format(hash)

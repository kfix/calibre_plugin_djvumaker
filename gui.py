from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

import sys
from functools import partial
from calibre import prints
from cStringIO import StringIO
from calibre.utils.logging import ERROR, WARN, DEBUG, INFO

from calibre.gui2.actions import InterfaceAction
# http://manual.calibre-ebook.com/_modules/calibre/gui2/actions.html

from calibre.customize.ui import run_plugins_on_postimport, find_plugin
from calibre.gui2.threaded_jobs import ThreadedJob

# http://manual.calibre-ebook.com/creating_plugins.html#ui-py
class ConvertToDJVUAction(InterfaceAction):
    name = 'Convert to DJVU'

    action_spec = (_('Convert to DJVU'), 'mimetypes/djvu.png',
                   _('engage the djvumaker plugin on this book'), None)
    # (label, icon_path, tooltip, keyboard shortcut)

    action_type = 'global'

    # don't auto-add the button to any menus' top-level
    dont_add_to = frozenset(['toolbar', 'toolbar-device', 'context-menu', 'context-menu-device',
                             'toolbar-child', 'menubar', 'menubar-device',
                             'context-menu-cover-browser'])

    def genesis(self):
        self.qaction.triggered.connect(self.convert_book)

    # def gui_layout_complete(self):
    def initialization_complete(self):
        # append my top-level DJVU action to the built-in conversion menus
        # https://github.com/kovidgoyal/calibre/blob/master/src/calibre/gui2/actions/convert.py
        # https://github.com/kovidgoyal/calibre/blob/master/src/calibre/gui2/__init__.py#L26
        cb = self.gui.iactions['Convert Books']
        cm = partial(cb.create_menu_action, cb.qaction.menu())
        cm('convert-djvu-cvtm', _('Convert to DJVU'), icon=self.qaction.icon(),
           triggered=self.convert_book)
        cb.qaction.setMenu(cb.qaction.menu())

    def location_selected(self, loc):
        # Currently values for loc are: ``library, main, card and cardb``.
        enabled = loc == 'library'
        self.qaction.setEnabled(enabled)

    def convert_book(self, triggered):
        rows = self.gui.current_view().selectionModel().selectedRows()
        self._convert_books(rows)

    def _convert_books(self, rows):
        db = self.gui.current_db
        if not rows or len(rows) == 0:
            return error_dialog(self.gui, _('Cannot convert'),
                                _('No books selected'), show=True)

        if self.gui.current_view() is self.gui.library_view:
            ids = list(map(self.gui.library_view.model().id, rows))
            for book_id in ids:
                if db.has_format(book_id, 'DJVU', index_is_id=True):
                    continue
                if db.has_format(book_id, 'PDF', index_is_id=True):
                    path_to_ebook = db.format_abspath(book_id, 'pdf', index_is_id=True)
                    job = ThreadedJob('ConvertToDJVU',
                                      'Converting %s to DJVU' % path_to_ebook,
                                      func=self._tjob_djvu_convert,
                                      args=(db, book_id, None, 'pdf'), #by book_id!
                                      kwargs={},
                                      callback=self._tjob_refresh_books)
                    # there is an assumed log=GUILog() ! src/calibre/utils/logging.py
                    self.gui.job_manager.run_threaded_job(job)
                    # too bad console utils and filetype plugins can't start a jobmanager..fork_job is a wretch
        else: # !gui_library
        # looking at a device's flash contents or some other non-library store,
        # filepaths here are not to be tracked in the db
            fpaths = self.gui.current_view().model().paths(rows)
            for fpath in fpaths:
                job = ThreadedJob('ConvertToDJVU',
                                  'Converting %s to DJVU' % path_to_ebook,
                                  func=self._tjob_djvu_convert,
                                  args=(None, None, fpath, 'pdf'), #by fpath!
                                  kwargs={})
                self.gui.job_manager.run_threaded_job(job)

    def _tjob_djvu_convert(self, db, book_id, fpath, ftype, abort, log, notifications):
        if book_id:
            find_plugin('djvumaker').postimport(book_id, ftype, db, log, fork_job=False,
                                                abort=abort, notifications=notifications)
        elif fpath:
            # TODO: unknow keywords?
            raise NotImplementedError
            # find_plugin('djvumaker').djvudigital(path, flags, None)

    def _tjob_refresh_books(self, job):
        book_id = job.args[1]
        # self.gui.iactions['Edit Metadata'].refresh_gui([book_id], covers_changed=False)
        self.gui.library_view.model().refresh_ids([book_id])
        self.gui.library_view.model().current_changed(self.gui.library_view.currentIndex(),
                                                      self.gui.library_view.currentIndex())
        self.gui.tags_view.recount()

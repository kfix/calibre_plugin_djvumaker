#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
djvumaker Calibre plugin - easy method to convert PDF documents to DJVU

Plugin uses other tools (further called backends) to make user-friendly conversion
of PDF documents (like scanned books) to lightweight DJVU format inside Calibre (e-book manager).
Plugin makes easy to install and use two backends - djvudigital (for macOS) and pdf2djvu (for Windows).


Usage:
======
(after installation of plugin and dowloading a suitable backend - look at CLI)
* right click on PDF file inside calibre, conversion occures after clicking
    on `Convert to DJVU` in `Convert books` submenu
* (after turning on automatic postimport conversion - look at CLI) just add pdf file to Calibre library, conversion should automaticly start
* through CLI, with commends `calibre-debug -r djvumaker -- convert [-p PATH, -i ID, --all]`


CLI - Command-line interface:
=============================
usage: calibre-debug -r djvumaker --  [-h] [-V] command ...
positional arguments:
  command
    backend       Backends handling.
      {install,set}           installs or sets backend
      {pdf2djvu,djvudigital}  choosed backend

    convert       Convert file to djvu.
      -p PATH, --path PATH  convert file under PATH to djvu using default settings
      -i ID, --id ID        convert file with ID to djvu using default settings
      --all                 convert all pdf files in calibre's library, you have to turn on postimport
                                conversion first, works for every backend

    postimport    Change postimport settings
      -y, --yes     sets plugin to convert PDF files after import (sometimes do not work for pdf2djvu)
      -n, --no      sets plugin to do not convert PDF files after import (default)

    install_deps  (depreciated) alias for `calibre-debug -r djvumaker -- backend install djvudigital`
    convert_all   (depreciated) alias for `calibre-debug -r djvumaker -- convert --all`
    test          (only for debugging, first has to be turned on in utils.py:53) custom command

optional arguments:
  -h, --help     show help message and exit
  -V, --version  show plugin's version number and exit


Features:
=========
* downloading and installation two backend:
  * djvudigital (for macOS - through brew)
  * pdf2djvu (for Windows - through automated download from author's github)
* discover method - you can just add your existing tool to you PATH env
* easy-to-use right click menu item for conversion of single or many PDF documents
* postimport file conversion (curently works only for djvudigital backend)
* notification about current conversion progress for (curently works only for pdf2djvu backend)
* CLI support for setting changes, installations of backends and manual conversion of files


Technical details:
==================
(GitHub repo: https://github.com/kfix/calibre_plugin_djvumaker)
Main problems during development:
* has to work with only python2.7 builtins
* conversion can be started in 6 (7th NotImplemented) different ways, every method has to use custom
    conversion handling
* plugins are loaded to Calibre, not imported, problematic globals updating
* printing has to work for CLI, inside Calibre and inside ThreadedJob
* Calibre source (https://github.com/kovidgoyal/calibre) is mostly not documented

Conversion can be started through:
* right click in GUI menu in library:
           gui.py:052:ConvertToDJVUAction.initialization_complete ->
    ->     gui.py:069:ConvertToDJVUAction.convert_book ->
    ->     gui.py:074:ConvertToDJVUAction._convert_books ->
    ->     gui.py:110:ConvertToDJVUAction._tjob_djvu_convert ->
    ->__init__.py:612:DJVUPlugin._postimport ->
    ->__init__.py:356:DJVUPlugin.run_backend ->
    ->__init__.py:377:DJVUPlugin.REGISTERED_BACKENDS[use_backend] ->
    ->__init__.py:305:register_backend ->
    ->__init__.py:788:job_handler ->
    ->__init__.py:916:{pdf2djvu//djvudigital}
* right click in GUI menu in library-like view on device:
    (currently NotImplemented)
      ...->gui.py:#NODOC:ConvertToDJVUAction._tjob_djvu_convert||elif fpath -> ???
* through postimport conversion during GUI
    __init__.py:#NODOC:DJVUPlugin.postimport ->
    ->__init__.py:#NODOC:DJVUPlugin._postimport ->
    ->__init__.py:#NODOC:DJVUPlugin.worker_fork_job ->
    ->__init__.py:#NODOC:DJVUPlugin.plugin_prefs['use_backend'] ->
    ->__init__.py:#NODOC:job_handler -> ...
* through postimport conversion during CLI with --all: `calibre-debug -r djvumaker -- convert --all`
    __init__.py:#NODOC:DJVUPlugin.cli_main ->
    ->   utils.py:#NODOC:create_cli_parser ->
    ->__init__.py:#NODOC:DJVUPlugin.cli_convert ->
    ->calibre.customize.ui:#NODOC:run_plugins_on_postimport ->
    ->__init__.py:#NODOC:DJVUPlugin.postimport ->
    ->__init__.py:#NODOC:DJVUPlugin._postimport ->
    ->__init__.py:#NODOC:DJVUPlugin.run_backend -> ...
* through postimport conversion during CLI: `calibredb add [book]`
    __init__.py:#NODOC:DJVUPlugin.postimport ->
    ->__init__.py:#NODOC:DJVUPlugin._postimport ->
    ->__init__.py:#NODOC:DJVUPlugin.run_backend -> ...
* through ID conversion during CLI: `calibre-debug -r djvumaker -- convert -i ID`
    __init__.py:#NODOC:DJVUPlugin.cli_main ->
    ->   utils.py:#NODOC:create_cli_parser ->
    ->__init__.py:#NODOC:DJVUPlugin.cli_convert ->
    ->__init__.py:#NODOC:DJVUPlugin.run_backend -> ...
* through PATH conversion during CLI: `calibre-debug -r djvumaker -- convert -p PATH`
    __init__.py:#NODOC:DJVUPlugin.cli_main ->
    ->   utils.py:#NODOC:create_cli_parser ->
    ->__init__.py:#NODOC:DJVUPlugin.cli_convert ->
    ->__init__.py:#NODOC:DJVUPlugin._postimport ->
    ->__init__.py:#NODOC:DJVUPlugin.run_backend -> ...

Development tags:
# TODO: <PURPOSE>   -- Informs that following part of code could be modified in the described <PURPOSE>.
# DEBUG <TASK>  -- Informs that following part of code was modified for DEBUG purposes.
                   To change to undebug state, one has to perform specified <TASK>.
#NODOC  -- Informs that following part of code needs better documentation.

Additional info:
Look at comments troughout code.
#NODOC

Helpful informations about writing plugins for Calibre:
* https://manual.calibre-ebook.com/creating_plugins.html
* https://manual.calibre-ebook.com/plugins.html
* https://www.mobileread.com/forums/forumdisplay.php?f=237
*** StackOverflow is not helpful ***


References:
===========
--- Modules ---
gui.py      -- handles GUI connection
utils.py    -- utility methods, CLI generation, pdf2djvu installtion scripts

--- Globals ---
PLUGINNAME      -- name of the plugin, i.e.: 'djvumaker'
PLUGINVER       -- plugin version in tuple  form, i.e.: (1,0,2)
PLUGINVER_DOT   -- plugin version in string form, i.e.: '1.0.2'
prints          -- prints function from Calibre, prepanded with string: 'djvumaker: '
printsd         -- prints function from Calibre, prepanded with string: 'DEBUG: djvumaker: '

--- Meaningful imports ---
from calibre import force_unicode,  -- output from other tools should be one time(!) piped through
                    prints          -- #NODOC
from calibre.customize import FileTypePlugin, InterfaceActionBase -- plugin classes for inheritance
from calibre.customize.ui import run_plugins_on_postimport -- Calibre runs every filetypeplugin with
                                                              postimport settings turned on
from calibre.constants import isosx, iswindows, islinux, isbsd -- self explanatory bools
from calibre.utils.config import JSONConfig -- dict-like object for storing settings in JSON file
from calibre.utils.podofo import get_podofo -- #NODOC
from calibre.utils.ipc import RC    -- #NODOC
from calibre.utils.ipc.simple_worker import fork_job as worker_fork_job -- #NODOC
# and additional imports from plugin's utils module

--- Classes ---
DJVUmaker(FileTypePlugin, InterfaceActionBase)  -- basic plugin class
  .__init__(self, *args, **kwargs)    -- mainly setting up JSONConfig object
  --- CLI handling methods ---
  .cli_main(self, args)               -- #NODOC
  .cli_test(self, args)               -- #NODOC
  .cli_backend(self, args)            -- #NODOC
  .cli_install_backend(self, args)    -- #NODOC
  .cli_set_backend(self, args)        -- #NODOC
  .cli_set_postimport(self, args)     -- #NODOC
  .cli_convert(self, args)            -- #NODOC
  --- Methods required by Calibre ---
  .customization_help(self, gui=True) -- return message inside "Customize plugin" menu
  .run(self, path_to_ebook)   -- #NODOC
  .postimport(self, book_id, book_format, db) -- start when PDF is added to library and `convert --all`
  --- Conversion handling methods ---
  @classmethod
  .register_backend(cls, fun) -- adds backend to plugin
  ._postimport(self, book_id, book_format=None, db=None, log=None, fork_job=True, abort=None,
      notifications=None)     -- starting jobs method
  .site_customization_parser(self, use_backend) -- parse user setting from "Customize plugin" menu
  .run_backend(self, *args, **kwargs) -- choose backend to run

NotSupportedFiletype(Exception) -- #NODOC

--- Functions ---

is_rasterbook(path, basic_return=True) -- #NODOC
raise_if_not_supported(srcdoc, supported_extensions) -- #NODOC
job_handler(fun) -- #NODOC

    --- Implemented backends ---
@DJVUmaker.register_backend
@job_handler
@add_method_dec(pdf2djvu_custom_printing, 'printing')
pdf2djvu(srcdoc, cmdflags, djvu, preferences)   -- #NODOC
    .printing = pdf2djvu_custom_printing(readout, pages, images) -- custom printing and notifications

@DJVUmaker.register_backend
@job_handler
djvudigital(srcdoc, cmdflags, djvu, preferences) -- #NODOC

    --- Non working backends ---
c44	    (srcdoc, cmdflags=[], log=None)
cjb2	(srcdoc, cmdflags=[], log=None)
minidjvu(srcdoc, cmdflags=[], log=None)
k2pdfopt(srcdoc, cmdflags=[], log=None)
mupdf	(srcdoc, cmdflags=[], log=None)


History of development:
=======================
(https://github.com/pirtim/calibre_plugin_djvumaker/releases)
v1.1.0 - 01 Apr 2017 - Przemysław Kowalczyk - General code overhaul; pdf2djvu support; documentation
v1.0.2 - 22 Mar 2015 - Joey Korkames - podofo.image_count in is_rasterbook
v1.0.1 - 19 Oct 2014 - Joey Korkames - Small bug fixes
v1.0.0 - 25 Jul 2014 - Joey Korkames - First relase


Main TODOs:
===========
(TODOs are also placed troughout the files)
* (E) substitute #NODOC with documentation
* (E) installation scripts for pdf2djvu for not Windows
* (E) proper english
* (M) add better Notifications (conversion progress reporting) support
* (M) inside gui.py -> _tjob_djvu_convert -> elif fpath -- conversion for devices
* (M) custom printing for djvudigital with notification support
* (M) pdf2djvu installation with GitHub API v3
* (M) cross import __init__.py inside utils for PLUGINNAME
* (M-H) custom scripts for conversion
* (M-H) installation scripts for djvudigital for not macOS
* (M-H) add other backend support
* (M-H) pdf2djvu sometimes doesn't work for postimport
* (H) plugin settings QT widget
* (H) make general overhaul of starting conversion logic
* (H) add support for conversion from other formats
#NODOC - more todos
"""
from __future__ import unicode_literals, division, absolute_import, print_function

__license__ = 'GPL 3'
__copyright__ = '2015, Joey Korkames <http://github.com/kfix>'
__docformat__ = 'restructuredtext en'

PLUGINNAME = 'djvumaker'
PLUGINVER = (1, 1, 0)
PLUGINVER_DOT = ".".join(str(i) for i in PLUGINVER)

if __name__ == '__main__':
    import sys
    sys.stdout.write(PLUGINVER_DOT) #Makefile needs this to do releases
    sys.exit()

import errno, os, sys, shutil, traceback, subprocess, collections
from functools import partial, wraps

from calibre import force_unicode, prints
from calibre.ebooks import ConversionError
from calibre.ptempfile import PersistentTemporaryFile
from calibre.customize import FileTypePlugin, InterfaceActionBase
from calibre.constants import isosx, iswindows, islinux, isbsd
from calibre.utils.config import JSONConfig
from calibre.utils.podofo import get_podofo
from calibre.utils.ipc.simple_worker import fork_job as worker_fork_job, WorkerError
from calibre_plugins.djvumaker.utils import (create_backend_link, create_cli_parser, install_pdf2djvu,
                                             discover_backend, ask_yesno_input, empty_function,
                                             EmptyClass, add_method_dec, plugin_dir)

# if iswindows and hasattr(sys, 'frozen'):
#     # CREATE_NO_WINDOW=0x08 so that no ugly console is popped up
#     subprocess.Popen = partial(subprocess.Popen, creationflags=0x08)
    # with this code, subprocess.check_output doesn't returns output

if (islinux or isbsd or isosx) and getattr(sys, 'frozen', False):
    pass
    # shell messes up escaping of spaced filenames to the script
    # popen = partial(subprocess.Popen, shell=True)
prints = partial(prints, '{}:'.format(PLUGINNAME)) # for easy printing

# DEBUG UNCOMMENT
DEBUG = False # calibre.constants.DEBUG also runs for CLI

if DEBUG:
    printsd = partial(prints, '{}:'.format('DEBUG')) # for DEBUG msgs
else:
    printsd = empty_function

# -- Calibre Plugin class --
class DJVUmaker(FileTypePlugin, InterfaceActionBase): # multiple inheritance for gui hooks!
    #NODOC
    name                = PLUGINNAME # Name of the plugin
    description         = ('Convert raster-based document files (Postscript, PDF) to DJVU with GUI'
                          ' button and on-import')
    supported_platforms = ['linux', 'osx', 'windows'] # Platforms this plugin will run on
    author              = 'Joey Korkames' # The author of this plugin
    version             = PLUGINVER   # The version number of this plugin
    # The file types that this plugin will be automatically applied to
    file_types          = set(['pdf','ps', 'eps'])
    on_postimport       = True # Run this plugin after books are addded to the database
    # needs the new db api w/id() bugfix, and podofo.image_count()
    minimum_calibre_version = (2, 22, 0)
    # InterfaceAction plugin location
    actual_plugin = 'calibre_plugins.djvumaker.gui:ConvertToDJVUAction'
    REGISTERED_BACKENDS = collections.OrderedDict()

    @classmethod
    def register_backend(cls, fun):
        """Register backend for future use."""
        cls.REGISTERED_BACKENDS[fun.__name__] = fun
        return fun

    def __init__(self, *args, **kwargs):
        super(DJVUmaker, self).__init__(*args, **kwargs)
        self.prints = prints # Easer access because of Calibre load plugins instead of importing
        # Set default preferences for JSONConfig
        DEFAULT_STORE_VALUES = {}
        DEFAULT_STORE_VALUES['plugin_version'] = PLUGINVER
        DEFAULT_STORE_VALUES['postimport'] = False
        for item in self.REGISTERED_BACKENDS:
            DEFAULT_STORE_VALUES[item] = {
                'flags' : [], 'installed' : False, 'version' : None}
        if 'djvudigital' in self.REGISTERED_BACKENDS:
            DEFAULT_STORE_VALUES['use_backend'] = 'djvudigital'
        else:
            raise Exception('No djvudigital backend.')

        # JSONConfig is a dict-like object,
        # if coresponding .json file has not a specific key, it's got from .defaults
        self.plugin_prefs = JSONConfig(os.path.join('plugins', PLUGINNAME))
        self.plugin_prefs.defaults = DEFAULT_STORE_VALUES

        # make sure to create plugins/djvumaker.json
        # self.plugin_prefs.values() doesn't use self.plugin_prefs.__getitem__()
        # and returns real json, not defaults
        if not self.plugin_prefs.values():
            for key, val in DEFAULT_STORE_VALUES.iteritems():
                self.plugin_prefs[key] = val

    def site_customization_parser(self, use_backend):
        """Parse user input from "Customize plugin" menu. Return backend and cmd flags to use."""
        backend, cmdflags = use_backend, self.plugin_prefs[use_backend]['flags']
        # site_customization is problematic, cannot assume about its content
        try:
            if self.site_customization is not None:
                site_customization = self.site_customization.split()
                if site_customization[0] in self.REGISTERED_BACKENDS:
                    backend = site_customization[0]
                    cmdflags = site_customization[1:]
                elif site_customization[0][0] == '-':
                    backend = use_backend
                    cmdflags = site_customization
                    #`--gsarg=-dFirstPage=1,-dLastPage=1` how to limit page range
                    #more gsargs: https://leanpub.com/pdfkungfoo
                else:
                    # TODO: Custom command implementation
                    #   some template engine with %djvu, %src or sth
                    raise NotImplementedError('Custom commands are not implemented')
        except NotImplementedError:
            raise
        except:
            pass
        return backend, cmdflags

    def run_backend(self, *args, **kwargs):
        """
        Choose proper backend. Check saved settings and overriden from "Customize plugin" menu.

        Possible kwargs:
            cmd_creation_only:bool -- if True, return only command creation function result
        """
        use_backend = self.plugin_prefs['use_backend']
        kwargs['preferences'] = self.plugin_prefs
        try:
            use_backend, kwargs['cmdflags'] = self.site_customization_parser(use_backend)
        except NotImplementedError as err:
            prints('Error: '+ str(err))
            prints('Back to not overriden backend settings...')
            kwargs['cmdflags'] = []

        if 'cmd_creation_only' in kwargs and kwargs['cmd_creation_only']:
            kwargs.pop('cmd_creation_only')
            return self.REGISTERED_BACKENDS[use_backend].__wrapped__(*args, **kwargs)
                #srcdoc, cmdflags, djvu, preferences
        kwargs.pop('cmd_creation_only', None)
        return self.REGISTERED_BACKENDS[use_backend](*args, **kwargs)

    def customization_help(self, gui=True):
        """Method required by calibre. Shows user info in "Customize plugin" menu."""
        # TODO: add info about current JSON settings
        # TODO: proper english
        current_backend = self.plugin_prefs['use_backend']
        flags = ''.join(self.plugin_prefs[current_backend]['flags'])
        command = current_backend + ' ' + flags

        try:
            overr_backend, overr_flags = self.site_customization_parser(current_backend)
        except NotImplementedError as err:
             overriden_info = 'Overriding command is not recognized. {}<br><br>'.format(err.message)
        else:
            overr_flags = ''.join(overr_flags)
            overr_command = overr_backend + ' ' + overr_flags
            if overr_backend != current_backend or overr_flags != flags:
                overriden_info = ('This command is overriden by this plugin customization command:'
                                ' <b>{}</b><br><br>').format(overr_command)
            else:
                overriden_info = '<br><br>'

        help_command = 'calibre-debug -r djvumaker -- --help'
        info = ('<p>You can enter overwritting command and flags to create djvu files.'
                'eg: `pdf2djvu -v`. You have to restart calibre before changes can take effect.<br>'
                'Currently set command is: <b>{}</b><br>'
                '{}'
                'You can read more about plugin customization running "{}" from command line.</p>').format(command, overriden_info, help_command)
        return info

        # return 'Enter additional `djvudigital --help` command-flags here:'

        # os.system('MANPAGER=cat djvudigital --help')
        # TODO: make custom config widget so we can have attrs for each of the wrappers:
        #       djvudigital minidjvu, c44, etc.
        # TODO: `man2html djvumaker` and gui=True for comprehensive help?

    def cli_main(self, args):
        """Handles plugin CLI interface"""
        args = args[1:] # args[0] = PLUGINNAME
        printsd('cli_main enter: args: ', args) # DEBUG
        parser = create_cli_parser(self, PLUGINNAME, PLUGINVER_DOT,
            self.REGISTERED_BACKENDS.keys())
        if len(args) == 0:
            parser.print_help()
            return sys.exit()
        options = parser.parse_args(args)
        options.func(options)

    def cli_test(self, args):
        """Debug method."""
        from calibre.utils.config import config_dir
        prints(config_dir)
        prints(os.path.join(config_dir, 'plugins', 'djvumaker'))
        prints(plugin_dir(PLUGINNAME))
        # prints(subprocess.check_output(['pwd']))

    def cli_backend(self, args):
        #NODOC
        printsd('cli_backend enter: plugin_prefs:', self.plugin_prefs)
        if args.command == 'install':
            self.cli_install_backend(args)
        elif args.command == 'set':
            self.cli_set_backend(args)
        else:
            raise Exception('Command not recognized.')

    def cli_install_backend(self, args):
        #NODOC
        # def brew_install(args, name):
        #     #NODOC
        #     joined = ' '.join(args)
        #     if os.system("which brew >/dev/null") == 0:
        #             if ask_yesno_input("Install {} from brew with args: '{}'?".format(name, joined)):
        #             os.system("brew {}".format(joined))
        #         else:
        #             raise Exception("Homebrew required."
        #                             "Please visit http://github.com/Homebrew/homebrew")

        printsd('cli_install_backend enter: args.backend:', args.backend)
        if not args.backend: # Report currently installed backends if without args
            installed_backend = [k for k, v in {
                    item : self.plugin_prefs[item]['installed'] for item in self.REGISTERED_BACKENDS
                    }.iteritems() if v]
            prints('Currently installed backends: {}'.format(
                ', '.join(installed_backend) if installed_backend else 'None'))
            sys.exit()

        if args.backend == 'djvudigital':
            if isosx:
                # brew_install(["install", "--with-djvu", "ghostscript"], "ghostscript")
                # brew_install(["install", "caskroom/cask/brew-cask"], "brew-cask")
                # brew_install(["cask", "install", "djview"], "DjView.app")

                if os.system("which brew >/dev/null") == 0:
                    os.system("brew install --with-djvu ghostscript")
                else:
                    raise Exception("Homebrew required."
                                    "Please visit http://github.com/Homebrew/homebrew")
                if raw_input("Install DjView.app? (y/n): ").lower() == 'y':
                    os.system("brew install caskroom/cask/brew-cask;"
                              " brew cask install djview")
                else:
                    sys.exit()
            # need a cask for the caminova finder/safari plugin too
            # TODO: make more install scripts
            #       for linux it should be relatively easy
            #       for plain windows probably impossible, only through cygwin
            elif islinux: raise Exception('Only macOS supported')
            elif iswindows: raise Exception('Only macOS supported. Check pdf2djvu backend for solution.')
            elif isbsd: raise Exception('Only macOS supported')
            else: raise Exception('Only macOS supported')
            self.plugin_prefs['djvudigital']['installed'] = True
            self.plugin_prefs.commit() # always use commit if uses nested dict
            # TODO: inherit from JSONConfig and make better implementation for defaults
        elif args.backend == 'pdf2djvu':
            # TODO: neat "Not supported" messages for every backend from function
            err_info = 'Only Windows supported. Try manual installation and add pdf2djvu to PATH env'
            if iswindows:
                success, version = install_pdf2djvu(PLUGINNAME, self.plugin_prefs, log=prints)
            elif isosx: raise Exception(err_info + ' Check djvudigital backend for solution.')
            elif islinux: raise Exception(err_info + ' Can work: `sudo apt-get install pdf2djvu` or your distro equivalent.')
            elif isbsd: raise Exception(err_info)
            else: raise Exception(err_info)
            # TODO: very easy: add support for macOS and linux, just add `make` after download source

            # path?
            # TODO: give flag where to installed_backend
            # TODO: ask if add to path?
            # TODO: should use github api v3
            #       https://developer.github.com/v3/repos/releases/
            #       https://developer.github.com/libraries/
            if success:
                self.plugin_prefs['pdf2djvu']['installed'] = True
                self.plugin_prefs['pdf2djvu']['version'] = version
                self.plugin_prefs.commit() # always use commit if uses nested dict
                prints('Installation of pdf2djvu was succesfull or unrequired.')
            else:
                prints('Installation of pdf2djvu was not succesfull.')
        else:
            raise Exception('Backend not recognized.')

    def cli_set_backend(self, args):
        #NODOC
        if not args.backend:
            prints('Currently set backend: {}'.format(self.plugin_prefs['use_backend']))
            return None
            # sys.exit()

        if args.backend in self.REGISTERED_BACKENDS:
            self.plugin_prefs['use_backend'] = args.backend
            prints('{} successfully set as current backend.'.format(args.backend))
        else:
            raise Exception('Backend not recognized.')
        return None

    def cli_set_postimport(self, args):
        #NODOC
        if args.yes:
            prints('Will try to convert files after import')
            self.plugin_prefs['postimport'] = True
        elif args.no:
            prints('Will not try to convert files after import')
            self.plugin_prefs['postimport'] = False
        else:
            if self.plugin_prefs['postimport']:
                prints('Currently {} tries to convert PDF files after import'.format(PLUGINNAME))
            else:
                prints("Currently {} doesn't do convertion of PDF's after import".format(PLUGINNAME))

    def cli_convert(self, args):
        #NODOC
        printsd(args)
        if args.all:
            # `calibre-debug -r djvumaker -- convert --all`
            printsd('in cli convert_all')
            # TODO: make work `djvumaker -- convert --all`
            # raise NotImplementedError('Convert all is not implemented.')

            user_input = ask_yesno_input('Do you wany to copy-convert all PDFs to DJVU?')
            if not user_input:
                return None

            from calibre.library import db
            from calibre.customize.ui import run_plugins_on_postimport
            db = db() # initialize calibre library database
            for book_id in list(db.all_ids()):
                if db.has_format(book_id, 'DJVU', index_is_id=True):
                    continue
                # TODO: shouldn't work with this code, db has not atributte run_plugins_on_postimport
                #       https://github.com/kovidgoyal/calibre/blob/master/src/calibre/customize/ui.py
                if db.has_format(book_id, 'PDF', index_is_id=True):
                    run_plugins_on_postimport(db, book_id, 'pdf')
                    continue
        elif args.path is not None:
            # `calibre-debug -r djvumaker -- convert -p test.pdf` -> tempfile(test.djvu)
            printsd('in path')
            if is_rasterbook(args.path):
                djvu = self.run_backend(args.path, log=self.prints.func)
                if djvu:
                    input_filename, _ = os.path.splitext(args.path)
                    shutil.copy2(djvu, input_filename + '.djvu')
                    prints("Finished DJVU outputed to: {}.".format(input_filename + '.djvu'))

                    user_input = ask_yesno_input('Do you want to open djvused in subshell?'
                                                 ' (may not work on not macOS)')
                    if not user_input:
                        return None
                    # de-munge the tty
                    sys.stdin = sys.__stdin__
                    sys.stdout = sys.__stdout__
                    sys.stderr = sys.__stderr__
                    os.system("stat '%s'" % djvu)
                    # TODO: doesn't work on Windows, why is it here?
                    os.system("djvused -e dump '%s'" % djvu)
                    os.system("djvused -v '%s'" % djvu)

        elif args.id is not None:
            # `calibre-debug -r djvumaker -- convert -i 123 #id(123).pdf` -> tempfile(id(123).djvu)
            printsd('in convert by id')
            self._postimport(args.id)

    # -- calibre filetype plugin mandatory methods --
    def run(self, path_to_ebook):
        #NODOC
        return path_to_ebook # noop

    def postimport(self, book_id, book_format, db):
        """Run postimport conversion if it's turned on"""
        if self.plugin_prefs['postimport']:
            return self._postimport(book_id, book_format, db)
        else:
            return None

    def _postimport(self, book_id, book_format=None, db=None, log=None, fork_job=True, abort=None,
                   notifications=None):
        #NODOC IMPORTANT
        # TODO: make general overhaul of starting conversion logic
        if log: # divert our printing to the caller's logger
            prints = log # Log object has __call__ dunder method with INFO level
            prints = partial(prints, '{}:'.format(PLUGINNAME))
        else:
            log = self.prints.func
        try:
            prints
        except NameError:
            prints = self.prints

        if sys.__stdin__.isatty():
            # if run by cli, i.e.:
            #    calibredb add
            #    calibredebug -r djvumaker -- convert -i #id
            # runs also for GUI if run trough `calibredebug -g`
            fork_job = False # DEBUG UNCOMMENT
            rpc_refresh = True # use the calibre RPC to signal a GUI refresh

        if db is None:
            from calibre.library import db # TODO: probably legacy db import, change for new_api
            db = db() # initialize calibre library database

        if book_format == None:
            if not db.has_format(book_id, 'PDF', index_is_id=True):
                raise Exception('Book with id #{} has not a PDF format.'.format(book_id))
            else:
                book_format='pdf'

        if db.has_format(book_id, 'DJVU', index_is_id=True):
            prints("already have 'DJVU' format document for book ID #{}".format(book_id))
            return None # don't auto convert, we already have a DJVU for this document

        path_to_ebook = db.format_abspath(book_id, book_format, index_is_id=True)
        if book_format == 'pdf':
            is_rasterbook_val, pages, images = is_rasterbook(path_to_ebook, basic_return=False)
            if is_rasterbook_val:
                pass # TODO: should add a 'scanned' or 'djvumaker' tag
            else:
            # this is a marked-up/vector-based pdf,
            # no advantages to having another copy in DJVU format
                prints(("{} document from book ID #{} determined to be a markup-based ebook,"
                        " not converting to DJVU").format(book_format, book_id))
                return None #no-error in job panel
            # TODO: test the DPI to determine if a document is from a broad-sheeted book.
            #       if so, queue up k2pdfopt to try and chunk the content appropriately to letter size

            prints(("scheduling new {} document from book ID #{} for post-import DJVU"
                    " conversion: {}").format(book_format, book_id, path_to_ebook))

        if fork_job:
            #useful for not blocking calibre GUI when large PDFs
            # are dropped into the automatic-import-folder
            try:
            # https://github.com/kovidgoyal/calibre/blob/master/src/calibre/utils/ipc/simple_worker.py
            # dispatch API for Worker()
            # src/calibre/utils/ipc/launch.py
            # Worker() uses sbp.Popen to
            # run a second Python to a logfile
            # note that Calibre bungs the python loader to check the plugin directory when
            # modules with calibre_plugin. prefixed are passed
            # https://github.com/kovidgoyal/calibre/blob/master/src/calibre/customize/zipplugin.py#L192
                func_name = self.plugin_prefs['use_backend']
                args = [path_to_ebook, log, abort, notifications, pages, images]
                jobret = worker_fork_job('calibre_plugins.{}'.format(PLUGINNAME), func_name,
                            args= args,
                            kwargs={'preferences' : self.plugin_prefs},
                            env={'PATH': os.environ['PATH'] + ':/usr/local/bin'},
                            # djvu and poppler-utils on osx
                            timeout=600)
                            # TODO: determine a resonable timeout= based on filesize or
                            # make a heartbeat= check
                            # TODO: doesn't work for pdf2djvu, why?

            except WorkerError as e:
                prints('djvudigital background conversion failed: \n{}'.format(force_unicode(e.orig_tb)))
                raise # ConversionError
            except:
                prints(traceback.format_exc())
                raise

        # dump djvudigital output logged in file by the Worker to
        # calibre proc's (gui or console) log/stdout
            with open(jobret['stdout_stderr'], 'rb') as f:
                raw = f.read().strip()
                prints(raw)

            if jobret['result']:
                djvu = jobret['result']
            else:
                WorkerError("djvu conversion error: %s" % jobret['result'])
        # elif hasattr(self, gui): #if we have the calibre gui running,
        # we can give it a threadedjob and not use fork_job
        else: #!fork_job & !gui
            prints("Starts backend")
            djvu = self.run_backend(path_to_ebook, log, abort, notifications, pages,
                                    images)

        if djvu:
            db.new_api.add_format(book_id, 'DJVU', djvu, run_hooks=True)
            prints("added new 'DJVU' document to book ID #{}".format(book_id))
            if sys.__stdin__.isatty():
            # update calibre gui Out-Of-Band. Like if we were run as a command-line scripted import
            # this resets current gui views/selections, no cleaner way to do it :-(
                from calibre.utils.ipc import RC
                t = RC(print_error=False)
                t.start()
                t.join(3)
                if t.done: # GUI is running
                    t.conn.send('refreshdb:')
                    t.conn.close()
                    prints("signalled Calibre GUI refresh")
        else:
            # TODO: normal Exception propagation instead of passing errors as return values
            raise Exception(('ConversionError, djvu: {}. Did you install any backend according to the'
                             ' documentation?').format(djvu))

def is_rasterbook(path, basic_return=True):
    """
    Identify whether this is a raster doc (ie. a scan) or a digitally authored text+graphic doc.
    Skip conversion if source doc is not mostly raster-image based.
    Ascertain this by checking whether there are as many image objects in the PDF
    as there are pages +/- 5 (google books and other scanners add pure-text preambles to their pdfs)

    If basic_return is True:
        return:
            aforementioned bool value
    otherwise:
        return:
            aforementioned bool value, number of pages, number of images
    """
    def fun_basic_return(result, pages, images):
        if basic_return:
            return result
        else:
            return result, pages, images

    printsd('enter is_rasterbook: {}'.format(path))
    podofo = get_podofo()
    pdf = podofo.PDFDoc()
    printsd('opens file')
    pdf.open(path)
    printsd('\n starts counting pages')
    pages = pdf.page_count()
    printsd('\n number of pages: {}'.format(pages))
    try:
        # without try statement, a lot of PDFs causes podofo.Error:
        # Error: A NULL handle was passed, but initialized data was expected.
        # It's probably a bug in calibre podofo image_count method:
        # https://github.com/kovidgoyal/calibre/blob/master/src/calibre/utils/podofo/doc.cpp#L146
        # or PDF file created with errors.
        #
        # This is not a big concern because raises mostly for heavy image PDFs
        images = pdf.image_count()
    except:
        import inspect
        error_info = sys.exc_info()
        prints("Unexpected error: {}".format(error_info))
        prints("from module: {}".format(inspect.getmodule(error_info[0])))

        # reraise exception if other exception than podofo.Error
        # str comparison because of problems with importing cpp Error
        # TODO: error type in except statement
        if object.__str__(error_info[0]) != "<class 'podofo.Error'>":
            raise
        else:
            # TODO: WARN or ASK user what to do, image count is unknown
            return fun_basic_return(True, pages, None)
    else:
        prints("pages(%s) : images(%s) > %s" % (pages, images, path))
        if pages > 0:
            return fun_basic_return(abs(pages - images) <= 5, pages, images)
        return fun_basic_return(False, pages, images)

def job_handler(fun):
    """Decorator for backend functions."""
    #NODOC
    @wraps(fun)
    def wrapper(srcdoc, log=None, abort=None, notifications=None, pages=None,
                images=None, cmdflags=None, *args, **kwargs):
        """Wrap around every backend."""
        # TODO: better notifications
        if notifications is None:
            notifications = EmptyClass()
            notifications.put = lambda x : None
        pages = 1 if pages is None else pages
        images = 1 if images is None else images # sometimes it can be None passed as arg, not default
        notifications.put((1/(pages+3),'Launching backend...'))

        if cmdflags is None:
            cmdflags = []

        if 'CALIBRE_WORKER' in os.environ:
            # running as a fork_job, all process output piped to logfile, so don't buffer
            cmdbuf = 0
        else:
            cmdbuf = 1 # line-buffered

        # TODO: and what with log in postimport?
        def merge_prints(*args, **kwargs):
            """Joins args to one string and prepands it with PLUGINNAME.
            Reason: sys.stdout.write accepts only one argument."""
            if 'force_unicode' not in kwargs or kwargs['force_unicode']:
                args = map(lambda x: force_unicode(str(x)), args)
            else:
                args = map(lambda x: str(x), args)
            kwargs.pop('force_unicode', None)
            if kwargs:
                raise Exception('Passed **kwargs: {} to prints which uses sys.stdout.write'.format(kwargs))

            line = ' '.join(['{}:'.format(PLUGINNAME)] + args)
            return line

        if log: # divert our streaming output printing to the caller's logger
            def prints(*args, **kwargs):
                return log(merge_prints(*args, **kwargs))
        else:
            def prints(*args, **kwargs):
                return sys.stdout.write(merge_prints(*args, **kwargs))

            # prints = sys.__stdout__.write #unredirectable original fd
            # `pip sarge` makes streaming subprocesses easier than sbp.Popen

        bookname = os.path.splitext(os.path.basename(srcdoc))[0]
        with PersistentTemporaryFile(bookname + '.djvu') as djvu: # note, PTF() is from calibre
            try:
                env = os.environ
                cmd = fun(srcdoc, cmdflags, djvu, *args, **kwargs)
                if isosx:
                    env['PATH'] = "/usr/local/bin:" + env['PATH'] # Homebrew
                prints('subprocess: {}'.format(cmd))

                proc = subprocess.Popen(cmd, env=env, bufsize=cmdbuf, stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT)
                # stderr: csepdjvu, stdout: ghostscript & djvudigital
                if cmdbuf > 0: #stream the output
                    while proc.poll() is None:
                        # TODO: piping print through backend util method, to add custom output handling
                        #       + notifications about job progress
                        readout = proc.stdout.readline()
                        if force_unicode(readout).strip() != '':
                            # TODO: better custom pringing
                            if hasattr(fun, 'printing'):
                                readout, progress, msg = fun.printing(readout, pages, images)
                                if progress is not None:
                                    notifications.put((progress, msg))
                                prints(readout, force_unicode=False)
                            else:
                                prints(readout)
                        if abort is not None and abort.is_set():
                            proc.kill() # aborts if msg from GUI is send

                    for line in proc.stdout.read().split('\n'):
                        prints(line)
                else:
                    proc.communicate()
                # TODO: better notifications
                notifications.put(((pages+2)/(pages+3), 'Cleaning...'))
                prints('subprocess returned {}'.format(proc.returncode))
            except OSError as err:
                if err.errno == errno.ENOENT:
                    prints(
                        ('$PATH[{}]\n/{} script not available to perform conversion:'
                         '{} must be installed').format(os.environ['PATH'], cmd[0],
                                                        fun.__name__))
                return False
            if proc.returncode != 0:
                return False # 10 djvudigital shell/usage error
            return djvu.name
    wrapper.__wrapped__ = fun # backporting python3 feature
    return wrapper

# -- DJVU conversion utilities wrapper functions -- see
# http://en.wikisource.org/wiki/User:Doug/DjVu_Files

class NotSupportedFiletype(Exception):
    """Exception to handle not supported filetypes by backend."""
    pass

def raise_if_not_supported(srcdoc, supported_extensions):
    """Checks if file extension is on supported extensions list"""
    file_ext = os.path.splitext(srcdoc)[1].lower().lstrip('.')
    if file_ext not in supported_extensions:
        raise NotSupportedFiletype('This backend supports only {} files, but get {}.'.format(
            ', '.join(['.' + item for item in supported_extensions]), '.'+file_ext))


# TODO: class implementation of backend
def pdf2djvu_custom_printing(readout, pages, images):
    """Get output from backend, clean it, and return with progress info."""
    readout = force_unicode(readout)
    readout = 'pdf2djvu: ' + readout.strip()
    splitted = readout.split('#')
    if len(splitted) == 3:
        page = int(splitted[2])
        # TODO: better notifications
        return readout, (page+1)/(pages+3), 'Converting....'
    return readout, None, None

@DJVUmaker.register_backend
@job_handler
@add_method_dec(pdf2djvu_custom_printing, 'printing') # TODO: class implementation of backend
def pdf2djvu(srcdoc, cmdflags, djvu, preferences):
    """pdf2djvu backend shell command generation"""
    raise_if_not_supported(srcdoc, ['pdf'])
    pdf2djvu_path, _, _, _ = discover_backend('pdf2djvu', preferences, plugin_dir(PLUGINNAME))
    if pdf2djvu_path is None:
        raise OSError('pdf2djvu not found')
    if djvu is None:
        djvu = EmptyClass()
        djvu.name, _ = os.path.splitext(srcdoc)
        djvu.name += '.djvu'
    # DEBUG COMMENT:
    # return [pdf2djvu_path, '-v', '-o', djvu.name, srcdoc] # verbose
    return [pdf2djvu_path] + cmdflags + ['-o', djvu.name, srcdoc]

@DJVUmaker.register_backend
@job_handler
def djvudigital(srcdoc, cmdflags, djvu, preferences):
    """djvudigital backend shell command generation"""
    raise_if_not_supported(srcdoc, ['pdf', 'ps'])

    # DEBUG UNCOMMENT
    return ['djvudigital'] + cmdflags + [srcdoc, djvu.name] # command passed to subprocess

    #DEBUG COMMENT
    # return ['XCOPY', r"C:\tools\bin\test.djvu", str(djvu.name)+'*', r'/Y'] # command passed to subprocess

def c44(srcdoc, cmdflags=[], log=None):
    # part of djvulibre, converts jpegs to djvu
    #  then combine with djvm -c book.djvu pageN.djvu pageN+1.djvu ..
    # files end up being huge
    raise NotImplementedError

def cjb2(srcdoc, cmdflags=[], log=None):
    # part of djvulibre, converts tiff to djvu
    #  need to bitone/greyscale the tiff beforehand
    #    gs -sDEVICE=pdfwrite -sColorConversionStrategy=Gray -dProcessColorModel=DeviceGray -dOverrideICC -f input.pdf -o output.pdf
    # osx has Quartz and a little cocoa app can break down a pdf into tiffs:
    #  http://lists.apple.com/archives/cocoa-dev/2002/Jun/msg00729.html
    #  http://scraplab.net/print-production-with-quartz-and-cocoa/
    #  then combine with djvm -c book.djvu pageN.djvu pageN+1.djvu ..
    raise NotImplementedError

def minidjvu(srcdoc, cmdflags=[], log=None):
    #http://minidjvu.sourceforge.net/
    #^foss license, supports raw TIFF images
    #https://code.google.com/p/mupdf-converter/source/browse/trunk/MuPDF/MuPDFConverter.cs
    raise NotImplementedError

def k2pdfopt(srcdoc, cmdflags=[], log=None):
    #brilliant, if quirky, app for reflowing a raster doc to layout suitable on e-readers,
    #reads DJVUs but only writes PDFs
    raise NotImplementedError

def mupdf(srcdoc, cmdflags=[], log=None):
    #https://github.com/Ernest0x/mupdf
    #can dump pdfs into tiffs and vice versa
    #mutool extract
    raise NotImplementedError

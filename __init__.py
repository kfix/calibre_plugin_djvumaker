#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

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

import errno, os, sys, traceback, argparse, subprocess, collections
from functools import partial, wraps

from calibre import force_unicode, prints
from calibre.ebooks import ConversionError
from calibre.ptempfile import PersistentTemporaryFile
from calibre.customize import FileTypePlugin, InterfaceActionBase
from calibre.constants import (isosx, iswindows, islinux, isbsd)
from calibre.utils.config import JSONConfig
from calibre.utils.podofo import get_podofo
from calibre.utils.ipc.simple_worker import fork_job as worker_fork_job, WorkerError
from calibre_plugins.djvumaker.utils import create_backend_link, create_cli_parser, install_pdf2djvu, discover_backend

# if iswindows and hasattr(sys, 'frozen'):
#     # CREATE_NO_WINDOW=0x08 so that no ugly console is popped up
#     subprocess.Popen = partial(subprocess.Popen, creationflags=0x08)
    # with this code, subprocess.check_output doesn't returns output
    # sbp.Popen = partial(sbp.Popen, creationflags=0x08)
if (islinux or isbsd or isosx) and getattr(sys, 'frozen', False):
    pass
    #shell messes up escaping of spaced filenames to the script
    # popen = partial(subprocess.Popen, shell=True)
prints = partial(prints, '{}:'.format(PLUGINNAME)) # for easy printing

DEBUG = True # set True for debugging
def empty_function(*args, **kwargs):
    pass
if DEBUG:
    printsd = partial(prints, '{}:'.format('DEBUG')) # for DEBUG msgs
else:
    printsd = empty_function

# -- Calibre Plugin class --
class DJVUmaker(FileTypePlugin, InterfaceActionBase): #multiple inheritance for gui hooks!
    name                = PLUGINNAME # Name of the plugin
    description         = 'Convert raster-based document files (Postscript, PDF) to DJVU with GUI button and on-import'
    # TODO: ON IMPORT?!?!
    supported_platforms = ['linux', 'osx', 'windows'] # Platforms this plugin will run on
    author              = 'Joey Korkames' # The author of this plugin
    version             = PLUGINVER   # The version number of this plugin
    file_types          = set(['pdf','ps', 'eps']) # The file types that this plugin will be automatically applied to
    on_postimport       = True # Run this plugin after books are addded to the database
    minimum_calibre_version = (2, 22, 0) #needs the new db api w/id() bugfix, and podofo.image_count()
    actual_plugin = 'calibre_plugins.djvumaker.gui:ConvertToDJVUAction' #InterfaceAction plugin location
    REGISTERED_BACKENDS = collections.OrderedDict()

    @classmethod
    def register_backend(cls, fun):
        cls.REGISTERED_BACKENDS[fun.__name__] = fun
        return fun

    def __init__(self, *args, **kwargs):
        super(DJVUmaker, self).__init__(*args, **kwargs)
        # Set default preferences
        DEFAULT_STORE_VALUES = {}
        DEFAULT_STORE_VALUES['plugin_version'] = PLUGINVER
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

    def run_backend(self, *args, **kwargs):
        use_backend = self.plugin_prefs['use_backend']
        kwargs['preferences'] = self.plugin_prefs
        return self.REGISTERED_BACKENDS[use_backend](*args, **kwargs)

    def customization_help(self, gui=True):
        # method required by calibre
        # TODO: add info about current JSON settings
        current_backend = self.plugin_prefs['use_backend']
        flags = ''.join(self.plugin_prefs[current_backend]['flags'])
        command = current_backend + flags
        help_command = 'calibre-debug -r djvumaker -- --help'
        info = ('<p>You can enter overwritting command and flags to create djvu files.<br>'
                'Currently set command is: {}<br><br>'
                'You can read more about plugin customization running "{}" from command line.</p>').format(command, help_command) # TODO: tab
        return info

        # return 'Enter additional `djvudigital --help` command-flags here:'

        # os.system('MANPAGER=cat djvudigital --help')
        #TODO: make custom config widget so we can have attrs for each of the wrappers:
        # djvudigital minidjvu, c44, etc.
        #TODO: `man2html djvumaker` and gui=True for comprehensive help?

    def cli_main(self, args):
        '''Handles plugin cli interface'''
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
        prints(subprocess.check_output(['pwd']))

    def cli_backend(self, args):
        printsd('cli_backend enter: plugin_prefs:', self.plugin_prefs)
        if args.command == 'install':
            self.cli_install_backend(args)
        elif args.command == 'set':
            self.cli_set_backend(args)
        else:
            raise Exception('Command not recognized.')

    def cli_install_backend(self, args):
        printsd('cli_install_backend enter: args.backend:', args.backend)
        if not args.backend:
            installed_backend = [k for k, v in {
                    item : self.plugin_prefs[item]['installed'] for item in self.REGISTERED_BACKENDS
                    }.iteritems() if v]
            prints('Currently installed backends: {}'.format(
                ', '.join(installed_backend) if installed_backend else 'None'))
            sys.exit()

        if args.backend == 'djvudigital':
            if isosx:
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
            #need a cask for the caminova finder/safari plugin too
            #todo: make more install scripts
            elif islinux: raise Exception('Only macOS supported')
            elif iswindows: raise Exception('Only macOS supported')
            elif isbsd: raise Exception('Only macOS supported')
            self.plugin_prefs['djvudigital']['installed'] = True
            self.plugin_prefs.commit() # always use commit if uses nested dict
            # TODO: inherit from JSONConfig and make better implementation for defaults
        elif args.backend == 'pdf2djvu':
            success, version = install_pdf2djvu(PLUGINNAME, self.plugin_prefs, log=prints)
            # path?
            # TODO: give flag where to installed_backend
            # TODO: ask if add to path?
            # TODO: should use github api v3
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
        if not args.backend:
            prints('Currently set backend: {}'.format(self.plugin_prefs['use_backend']))
            sys.exit()

        if args.backend in self.REGISTERED_BACKENDS:
            self.plugin_prefs['use_backend'] = args.backend
            prints('{} successfully set as current backend.'.format(args.backend))
        else:
            raise Exception('Backend not recognized.')
        return None

    def cli_convert(self, args):
        printsd(args)
        if args.all:
            printsd('in cli convert_all')
            # `calibre-debug -r djvumaker convert_all`
            prints("Press Enter to copy-convert all PDFs to DJVU, or CTRL+C to abort...")
            raw_input('')
            from calibre.library import db
            db = db() # initialize calibre library database
            for book_id in list(db.all_ids()):
                if db.has_format(book_id, 'DJVU', index_is_id=True):
                    continue
                if db.has_format(book_id, 'PDF', index_is_id=True):
                    db.run_plugins_on_postimport(book_id, 'pdf')
                    continue
        elif args.path is not None:
            printsd('path')
            return NotImplemented
            if is_rasterbook(args.path):
                # `calibre-debug -r djvumaker test.pdf` -> tempfile(test.djvu)
                djvu = self.run_backend(args.path)

                if djvu:
                    prints(("\n\nopening djvused in subshell, press Ctrl+D to exit and"
                           "delete '%s'\n\n") % djvu)
                    #de-munge the tty
                    sys.stdin = sys.__stdin__
                    sys.stdout = sys.__stdout__
                    sys.stderr = sys.__stderr__
                    os.system("stat '%s'" % djvu)
                    os.system("djvused -e dump '%s'" % djvu)
                    os.system("djvused -v '%s'" % djvu)
        elif args.id is not None:
            printsd('in convert by id')
            # `calibre-debug -r djvumaker 123 #id(123).pdf` -> tempfile(id(123).djvu)
            self.postimport(args.id, 'pdf') # bookid and book_format, can go really wrong

    # -- calibre filetype plugin mandatory methods --
    def run(self, path_to_ebook):
        return path_to_ebook #noop

    def postimport(self, book_id, book_format, db=None, log=None, fork_job=True):
        if log: #divert our printing to the caller's logger
            prints = partial(log.prints, 1) #log.print(INFO, yaddayadda)
        else:
            def prints(p): prints(p+'\n')

        if sys.__stdin__.isatty():
            fork_job = False #probably being run as `calibredb add`, do all conversions in main loop
            rpc_refresh = True #use the calibre RPC to signal a GUI refresh

        if db is None:
            from calibre.library import db
            db = db() # initialize calibre library database

        if db.has_format(book_id, 'DJVU', index_is_id=True):
            prints("{}: already have 'DJVU' format document for book ID #{}".format(PLUGINNAME,
                                                                                    book_id))
            return None #don't auto convert, we already have a DJVU for this document

        path_to_ebook = db.format_abspath(book_id, book_format, index_is_id=True)
        if book_format == 'pdf':
            if is_rasterbook(path_to_ebook):
                pass #should add a 'scanned' or 'djvumaker' tag
            else:
            #this is a marked-up/vector-based pdf,
            # no advantages to having another copy in DJVU format
                prints(("{}: {} document from book ID #{} determined to be a markup-based ebook,"
                        " not converting to DJVU").format(self.name, book_format, book_id))
                return None #no-error in job panel
            #TODO: test the DPI to determine if a document is from a broad-sheeted book.
            # if so, queue up k2pdfopt to try and chunk the content appropriately to letter size

            prints(("{}: scheduling new {} document from book ID #{} for post-import DJVU"
                    " conversion: {}").format(self.name, book_format, book_id, path_to_ebook))

            cmdflags = []
            if self.site_customization is not None: cmdflags.extend(self.site_customization.split())
            # TODO: change site_customization

            #`--gsarg=-dFirstPage=1,-dLastPage=1` how to limit page range
            #more gsargs: https://leanpub.com/pdfkungfoo

        if fork_job:
            #useful for not blocking calibre GUI when large PDFs
            # are dropped into the automatic-import-folder
            try:
            #https://github.com/kovidgoyal/calibre/blob/master/src/calibre/utils/ipc/simple_worker.py #dispatch API for Worker()
            #src/calibre/utils/ipc/launch.py #Worker() uses sbp.Popen to
            # run a second Python to a logfile
            # note that Calibre bungs the python loader to check the plugin directory when
            # modules with calibre_plugin. prefixed are passed
            #https://github.com/kovidgoyal/calibre/blob/master/src/calibre/customize/zipplugin.py#L192
                func_name = self.plugin_prefs['Options']['use_backend']
                jobret = worker_fork_job('calibre_plugins.%s' % self.name, func_name,
                                  args=[path_to_ebook, cmdflags, log],
                                  kwargs={},
                                  env={'PATH': os.environ['PATH'] + ':/usr/local/bin'},
                                  #djvu and poppler-utils on osx
                                  timeout=600)
                                  #todo: determine a resonable timeout= based on filesize or
                                  # make a heartbeat= check

            except WorkerError as e:
                prints('{}: djvudigital background conversion failed: \n{}'.format(
                    self.name, force_unicode(e.orig_tb)))
                raise #ConversionError
            except:
                prints(traceback.format_exc())
                raise

        #dump djvudigital output logged in file by the Worker to
        # calibre proc's (gui or console) log/stdout
            with open(jobret['stdout_stderr'], 'rb') as f:
                raw = f.read().strip()
                prints(raw)

            if jobret['result']:
                djvu = jobret['result']
            else:
                WorkerError("djvu conversion error: %s" % jobret['result'])
    #elif hasattr(self, gui): #if we have the calibre gui running,
    # we can give it a threadedjob and not use fork_job
        else: #!fork_job & !gui
            prints("Starts backend")
            djvu = self.run_backend(path_to_ebook, cmdflags, log)
            # if self.plugin_prefs['Options']['use_backend'] == 'djvudigital':
            #     djvu = djvudigital(path_to_ebook, cmdflags, log)
            # elif self.plugin_prefs['Options']['use_backend'] == 'pdf2djvu':
            #     djvu = pdf2djvu(path_to_ebook, cmdflags, log)

        if djvu:
            db.new_api.add_format(book_id, 'DJVU', djvu, run_hooks=True)
            prints("%s: added new 'DJVU' document to book ID #%s" % (PLUGINNAME, book_id))
            if sys.__stdin__.isatty():
            #update calibre gui Out-Of-Band. Like if we were run as a command-line scripted import
            #this resets current gui views/selections, no cleaner way to do it :-(
                from calibre.utils.ipc import RC
                t = RC(print_error=False)
                t.start()
                t.join(3)
                if t.done: #GUI is running
                    t.conn.send('refreshdb:')
                    t.conn.close()
                    prints("%s: signalled Calibre GUI refresh" % PLUGINNAME)
        else:
            raise Exception('ConversionError 3, djvu: {}'.format(djvu))

def is_rasterbook(path):
    '''
    Identify whether this is a raster doc (ie. a scan) or a digitally authored text+graphic doc.
    Skip conversion if source doc is not mostly raster-image based.
    Ascertain this by checking whether there are as many image objects in the PDF
    as there are pages +/- 5 (google books and other scanners add pure-text preambles to their pdfs)
    '''
    printsd('enter is_rasterbook: {}'.format(path))
    podofo = get_podofo()
    pdf = podofo.PDFDoc()
    printsd('opens file')
    pdf.open(path)
    printsd('\n starts counting pages')
    pages = pdf.page_count()
    printsd('\n number of pages: {}'.format(pages))
    try:
        # without try statment, a lot of PDFs causes podofo.Error:
        # Error: A NULL handle was passed, but initialized data was expected.
        # It's probably a bug in calibre podofo image_count method:
        # https://github.com/kovidgoyal/calibre/blob/master/src/calibre/utils/podofo/doc.cpp#L146
        images = pdf.image_count()
    except:
        import inspect
        error_info = sys.exc_info()
        prints("Unexpected error: {}".format(error_info))
        prints("from module: {}".format(inspect.getmodule(error_info[0])))

        # reraise exception if other exception than podofo.Error
        # str comparison because of problems with importing cpp Error
        if object.__str__(error_info[0]) != "<class 'podofo.Error'>":
            raise
        else:
            # TODO: WARN or ASK user what to do, image count is unknown
            return True
    else:
        prints("pages(%s) : images(%s) > %s" % (pages, images, path))
        if pages > 0:
            return abs(pages - images) <= 5
        return False

def job_handler(fun):
    @wraps(fun)
    def wrapper(srcdoc, cmdflags=None, log=None, *args, **kwargs):
        '''Wraps around every backend.'''
        if cmdflags is None:
            cmdflags = []

        if 'CALIBRE_WORKER' in os.environ:
            #running as a fork_job, all process output piped to logfile, so don't buffer
            cmdbuf = 0
        else:
            cmdbuf = 1 #line-buffered

        # TODO: and what with log in postimport?
        def merge_prints(*args, **kwargs):
            if kwargs:
                raise Exception('Passed **kwargs: {} to prints which uses sys.stdout.write'.format(kwargs))

            # log('starting logging')
            # log(str(args))
            # log('end logging')
            # log('stdout encoding: ' + sys.stdout.encoding)

            args = map(force_unicode, args)
            line = ' '.join(['{}: '.format(PLUGINNAME)] + args)
            return line

        if log: #divert our streaming output printing to the caller's logger
            def prints(*args, **kwargs):
                log_prints = partial(log.prints, 1) #log.print(INFO, yaddayadda)
                return log_prints(merge_prints(*args, **kwargs))
        else:
            #def prints(p): print p
            # prints = sys.stdout.write
            def prints(*args, **kwargs):
                return sys.stdout.write(merge_prints(*args, **kwargs))

            #prints = sys.__stdout__.write #unredirectable original fd
            #`pip sarge` makes streaming subprocesses easier than sbp.Popen

        bookname = os.path.splitext(os.path.basename(srcdoc))[0]
        with PersistentTemporaryFile(bookname + '.djvu') as djvu: #note, PTF() is from calibre
            try:
                prints("with PersistentTemporaryFile")
                env = os.environ
                cmd = fun(srcdoc, cmdflags, djvu, *args, **kwargs)
                if isosx:
                    env['PATH'] = "/usr/local/bin:" + env['PATH'] # Homebrew
                prints('%s: subprocess: %s' % (PLUGINNAME, cmd))

                proc = subprocess.Popen(cmd, env=env, bufsize=cmdbuf, stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT)
                # TODO: aborting doesn't work
                #stderr:csepdjvu, stdout: ghostscript & djvudigital
                if cmdbuf > 0: #stream the output
                    while proc.poll() is None:
                        prints(proc.stdout.readline())
                    #remainder of post-polled buffer
                    for line in proc.stdout.read().split('\n'):
                        prints(line)
                else:
                    proc.communicate()
                prints('%s: subprocess returned %s' % (PLUGINNAME, proc.returncode))
            except OSError as err:
                if err.errno == errno.ENOENT:
                    prints(
                        ('$PATH[{}]\n/{} script not available to perform conversion:'
                         '{} must be installed').format(os.environ['PATH'], cmd[0],
                                                           fun.__name__))
                return False
            if proc.returncode != 0:
                return False #10 djvudigital shell/usage error
            return djvu.name
    return wrapper

# -- DJVU conversion utilities wrapper functions -- see
# http://en.wikisource.org/wiki/User:Doug/DjVu_Files

class NotSupportedFiletype(Exception):
    '''Exception to handle not supported filetypes by backend.'''
    pass

def raise_if_not_supported(srcdoc, supported_extensions):
    '''Checks if file extension is on supported extensions list'''
    file_ext = os.path.splitext(srcdoc)[1].lower().lstrip('.')
    if file_ext not in supported_extensions:
        raise NotSupportedFiletype('This backend supports only {} files, but get {}.'.format(
            ', '.join(['.' + item for item in supported_extensions]), '.'+file_ext))

@DJVUmaker.register_backend
@job_handler
def pdf2djvu(srcdoc, cmdflags, djvu, preferences):
    '''pdf2djvu backend shell command generation'''
    raise_if_not_supported(srcdoc, ['pdf'])
    pdf2djvu_path, _, _, _ = discover_backend('pdf2djvu', preferences, PLUGINNAME)
    if pdf2djvu_path is None:
        raise OSError('pdf2djvu not found')
    # command passed to subprocess
    return [pdf2djvu_path, '-o', djvu.name, srcdoc]

@DJVUmaker.register_backend
@job_handler
def djvudigital(srcdoc, cmdflags, djvu, preferences):
    '''djvudigital backend shell command generation'''
    raise_if_not_supported(srcdoc, ['pdf', 'ps'])
    return ['djvudigital'] + cmdflags + [srcdoc, djvu.name] # command passed to subprocess

def c44(srcdoc, cmdflags=[], log=None):
    #part of djvulibre, converts jpegs to djvu
    #  then combine with djvm -c book.djvu pageN.djvu pageN+1.djvu ..
    #files end up being huge
    raise NotImplementedError

def cjb2(srcdoc, cmdflags=[], log=None):
    #part of djvulibre, converts tiff to djvu
    #  need to bitone/greyscale the tiff beforehand
    #    gs -sDEVICE=pdfwrite -sColorConversionStrategy=Gray -dProcessColorModel=DeviceGray -dOverrideICC -f input.pdf -o output.pdf
    #osx has Quartz and a little cocoa app can break down a pdf into tiffs:
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

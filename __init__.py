#!/usr/bin/env python
# -*- coding: utf-8 -*-

__license__ = 'GPL 3'
__copyright__ = '2015, Joey Korkames <http://github.com/kfix>'
__docformat__ = 'restructuredtext en'

PLUGINNAME = 'djvumaker'
PLUGINVER = (1,0,2)

if __name__ == '__main__':
    import sys
    sys.stdout.write(".".join(str(i) for i in PLUGINVER)) #Makefile needs this to do releases
    sys.exit()

import errno, os, sys, subprocess, traceback
from functools import partial
from calibre.ebooks import ConversionError
from calibre.constants import (isosx, iswindows, islinux, isbsd)
from calibre.utils.ipc.simple_worker import fork_job, WorkerError
from calibre import force_unicode, prints
from calibre.ptempfile import PersistentTemporaryFile
from calibre.utils.podofo import get_podofo

from calibre.customize import FileTypePlugin, InterfaceActionBase

if iswindows and hasattr(sys, 'frozen'):
    subprocess.Popen = partial(subprocess.Popen, creationflags=0x08) # CREATE_NO_WINDOW=0x08 so that no ugly console is popped up
if (islinux or isbsd or isosx) and getattr(sys, 'frozen', False):
    pass #shell messes up escaping of spaced filenames to the script #popen = partial(subprocess.Popen, shell=True)

# -- DJVU conversion utilities wrapper functions -- see http://en.wikisource.org/wiki/User:Doug/DjVu_Files

def c44(srcdoc, cmdflags=[], log=None):
    #part of djvulibre, converts jpegs to djvu
    #  then combine with djvm -c book.djvu pageN.djvu pageN+1.djvu ..
    #files end up being huge
    pass

def cjb2(srcdoc, cmdflags=[], log=None):
    #part of djvulibre, converts tiff to djvu
    #  need to bitone/greyscale the tiff beforehand
    #    gs -sDEVICE=pdfwrite -sColorConversionStrategy=Gray -dProcessColorModel=DeviceGray -dOverrideICC -f input.pdf -o output.pdf
    #osx has Quartz and a little cocoa app can break down a pdf into tiffs: http://lists.apple.com/archives/cocoa-dev/2002/Jun/msg00729.html
    #  http://scraplab.net/print-production-with-quartz-and-cocoa/
    #  then combine with djvm -c book.djvu pageN.djvu pageN+1.djvu ..
    pass

def minidjvu(srcdoc, cmdflags=[], log=None):
    #http://minidjvu.sourceforge.net/
    #^foss license, supports raw TIFF images
    #https://code.google.com/p/mupdf-converter/source/browse/trunk/MuPDF/MuPDFConverter.cs
    pass

def k2pdfopt(srcdoc, cmdflags=[], log=None):
    #brilliant, if quirky, app for reflowing a raster doc to layout suitable on e-readers,
    #reads DJVUs but only writes PDFs
    pass

def pdf2djvu(srcdoc, cmdflags=[], log=None):
    #https://code.google.com/p/pdf2djvu/
    #pdf2djvu -o output_file input_file
    pass

def mupdf(srcdoc, cmdflags=[], log=None):
    #https://github.com/Ernest0x/mupdf
    #can dump pdfs into tiffs and vice versa
    #mutool extract
    pass

def djvudigital(srcdoc, cmdflags=[], log=None):
    #only supports pdf and ps, tricky to get compiled and installed, but is the fastest converter
    #win32: http://code.google.com/p/osspack32/downloads/detail?name=ghostscript8.71_gsdjvu1.5_src.7z
    #gentoo: emerge ghostscript-gpl --use-djvu
    #osx: brew install --build-from-source --with-djvu ghostscript
   
    if 'CALIBRE_WORKER' in os.environ:
        cmdbuf=0 #running as a fork_job, all process output piped to logfile, so don't buffer
    else:
        cmdbuf=1 #line-buffered
    
    if log: #divert our streaming output printing to the caller's logger
	prints = partial(log.prints, 1) #log.print(INFO, yaddayadda)
    else:
	#def prints(p): print p
        prints = sys.stdout.write
        #prints = sys.__stdout__.write #unredirectable original fd
    #`pip sarge` makes streaming subprocesses easier than sbp.Popen

    bookname = os.path.splitext(os.path.basename(srcdoc))[0]
    with PersistentTemporaryFile(bookname + '.djvu') as djvu: #note, PTF() is from calibre
         try:
             env = os.environ
             cmd = ['djvudigital'] + cmdflags + [srcdoc, djvu.name]
             if isosx: env['PATH'] = "/usr/local/bin:" + env['PATH'] # Homebrew
             prints('%s: subprocess: %s' % (PLUGINNAME, cmd))
	     proc = subprocess.Popen(cmd, env=env, bufsize=cmdbuf, stdout=subprocess.PIPE, stderr=subprocess.STDOUT) #stderr:csepdjvu, stdout: ghostscript & djvudigital
	     if cmdbuf > 0: #stream the output
	        while proc.poll() is None: prints(proc.stdout.readline())
	        for line in proc.stdout.read().split('\n'): prints(line) #remainder of post-polled buffer 
	     else:
                proc.communicate()
	     prints('%s: subprocess returned %s' % (PLUGINNAME, proc.returncode))
         except OSError as e:
             if e.errno == errno.ENOENT:
                 prints('%s: $PATH[%s]/djvudigital script not available to perform conversion: djvulibre must be installed' % (PLUGINNAME, os.environ['PATH']))
             return False
     
         if proc.returncode != 0: return False #10 djvudigital shell/usage error

         return djvu.name

def is_rasterbook(path):
    '''identify whether this is a raster doc (ie. a scan) or a digitally authored text+graphic doc. skip conversion if source doc is not mostly raster-image based
    ascertain this by checking whether there are as many image objects in the PDF as there are pages +/- 5 (google books and other scanners add pure-text preambles to their pdfs)'''
    podofo = get_podofo()
    pdf = podofo.PDFDoc()
    pdf.open(path)
    pages = pdf.page_count()
    images = pdf.image_count()
    prints("%s: pages(%s) : images(%s) > %s" % (PLUGINNAME, pages, images, path))
    if pages > 0: return abs(pages - images) <= 5
    return False

# -- Calibre Plugin class --

class DJVUmaker(FileTypePlugin, InterfaceActionBase): #multiple inheritance for gui hooks!
    name                = PLUGINNAME # Name of the plugin
    description         = 'Convert raster-based document files (Postscript, PDF) to DJVU with GUI button and on-import'
    supported_platforms = ['linux', 'osx', 'windows'] # Platforms this plugin will run on
    author              = 'Joey Korkames' # The author of this plugin
    version             = PLUGINVER   # The version number of this plugin
    file_types          = set(['pdf','ps', 'eps']) # The file types that this plugin will be automatically applied to
    on_postimport       = True # Run this plugin after books are addded to the database
    minimum_calibre_version = (2, 22, 0) #needs the new db api w/id() bugfix, and podofo.image_count()
    actual_plugin = 'calibre_plugins.djvumaker.gui:ConvertToDJVUAction' #InterfaceAction plugin location

    def customization_help(self, gui=False):
        return 'Enter additional `djvudigital --help` command-flags here:' # os.system('MANPAGER=cat djvudigital --help')
	#todo: make custom config widget so we can have attrs for each of the wrappers: djvudigital minidjvu, c44, etc.
	#todo: `man2html djvumaker` and gui=True for comprehensive help?

    def cli_main(self, args):
	def prints(p): print p
        id_or_path = args[1]

        if id_or_path.isdigit():
	   '`calibre-debug -r 123 #id(123).pdf` -> tempfile(id(123).djvu)'
	   self.postimport(id_or_path, fmt)
	elif id_or_path == "convert_all":
	   '`calibre-debug -r djvumaker convert_all`'
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
	elif id_or_path == "install_deps":
	   if isosx:
	      if os.system("which brew >/dev/null") == 0:
                 os.system("brew install --with-djvu ghostscript; brew install poppler")
	      else:
	         print "Homebrew required. Please visit http://github.com/Homebrew/homebrew"
		 return False
              if raw_input("Install DjView.app? (y/n): ") == 'y':
                 os.system("brew install caskroom/cask/brew-cask; brew cask install djview")
   	         #need a cask for the caminova finder/safari plugin too
	   #todo: make more install scripts
	   elif islinux: raise
	   elif iswindows: raise
	   elif isbsd: raise
        else: 
	   '`calibre-debug -r djvumaker test.pdf` -> tempfile(test.djvu)'
	   if is_rasterbook(id_or_path):
	      djvu = djvudigital(id_or_path)
	      if djvu:
  	        prints("\n\nopening djvused in subshell, press Ctrl+D to exit and delete '%s'\n\n" % djvu)
	        #de-munge the tty
	        sys.stdin = sys.__stdin__ 
	        sys.stdout = sys.__stdout__
	        sys.stderr = sys.__stderr__
	        os.system("stat '%s'" % djvu)
	        os.system("djvused -e dump '%s'" % djvu)
	        os.system("djvused -v '%s'" % djvu)

    # -- calibre filetype plugin mandatory methods --

    def run(self, path_to_ebook):
        return path_to_ebook #noop

    def postimport(self, book_id, book_format, db=None, log=None, fork_job=True):
        if log: #divert our printing to the caller's logger
	    prints = partial(log.prints, 1) #log.print(INFO, yaddayadda)
	else:
	    def prints(p): print p+'\n'

        if sys.__stdin__.isatty():
	   fork_job = False #probably being run as `calibredb add`, do all conversions in main loop
	   rpc_refresh = True #use the calibre RPC to signal a GUI refresh

	if db is None:
  	    from calibre.library import db
	    db = db() # initialize calibre library database

	if db.has_format(book_id, 'DJVU', index_is_id=True):
           prints("%s: already have 'DJVU' format document for book ID #%s" % (PLUGINNAME, book_id))
	   return None #don't auto convert, we already have a DJVU for this document

	path_to_ebook = db.format_abspath(book_id, book_format, index_is_id=True)
	
	if book_format == 'pdf':
           if is_rasterbook(path_to_ebook):
	        pass #should add a 'scanned' or 'djvumaker' tag
	   else:
		#this is a marked-up/vector-based pdf, no advantages to having another copy in DJVU format
	        prints("%s: %s document from book ID #%s determined to be a markup-based ebook, not converting to DJVU" % (self.name, book_format, book_id))
	        return None #no-error in job panel
           #todo: test the DPI to determine if a document is from a broad-sheeted book. if so, queue up k2pdfopt to try and chunk the content appropriately to letter size

	prints("%s: scheduling new %s document from book ID #%s for post-import DJVU conversion: %s" % (self.name, book_format, book_id, path_to_ebook))

        cmdflags = []
        if self.site_customization is not None: cmdflags.extend(self.site_customization.split())
	#`--gsarg=-dFirstPage=1,-dLastPage=1` how to limit page range
	#more gsargs: https://leanpub.com/pdfkungfoo

	if fork_job: #useful for not blocking calibre GUI when large PDFs are dropped into the automatic-import-folder
            try:
	        #https://github.com/kovidgoyal/calibre/blob/master/src/calibre/utils/ipc/simple_worker.py #dispatch API for Worker()
	        #src/calibre/utils/ipc/launch.py #Worker() uses sbp.Popen to run a second Python to a logfile
	        #note that Calibre bungs the python loader to check the plugin directory when modules with calibre_plugin. prefixed are passed
	        #  https://github.com/kovidgoyal/calibre/blob/master/src/calibre/customize/zipplugin.py#L192
                jobret = fork_job('calibre_plugins.%s' % self.name, 'djvudigital',
		   args=[path_to_ebook, cmdflags, log],
		   kwargs={},
		   env={'PATH': os.environ['PATH'] + ':/usr/local/bin'}, #djvu and poppler-utils on osx
		   timeout=600)  #todo: determine a resonable timeout= based on filesize or make a heartbeat= check

            except WorkerError as e:
                prints('%s: djvudigital background conversion failed: \n%s' % (self.name,force_unicode(e.orig_tb)))
	        raise #ConversionError
	    except:
                prints(traceback.format_exc())
	        raise

	    #dump djvudigital output logged in file by the Worker to calibre proc's (gui or console) log/stdout
	    with open(jobret['stdout_stderr'], 'rb') as f:
                raw = f.read().strip()
	        prints(raw)

	    if jobret['result']:
	       djvu = jobret['result']
	    else:
	       WorkerError("djvu conversion error: %s" % jobret['result'])
	#elif hasattr(self, gui): #if we have the calibre gui running, we can give it a threadedjob and not use fork_job
        else: #!fork_job & !gui
	    djvu = djvudigital(path_to_ebook, cmdflags, log)

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
	    raise #ConversionError

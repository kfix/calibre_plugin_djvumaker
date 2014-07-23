DjVuMaker Plugin for Calibre
---
This plugin adds DJVU output conversion for Postscript documents (*.pdf, .ps).
Files can be converted through a GUI menu and optionally as FileType hook for automatically converting imports of all Postscript documents.

![GUI menu](/screenshot_menu.png?raw=true)
![Job log](/screenshot_job.png?raw=true)

DjVU files are best for rendering large image-based documents (100+ pg. black-and-white-scaned archive-books) on markup-ebook readers with sub-300MiB memory and sub-2GiB storage capacities.  
The community-made Kindle readers kindlepdfviewer & koreader support DjVu files and can deliver noticable speed increase over PDF originals of such documents.  
Some massive 1000+ page books can only be read unsplit on these devices in DjVu format.  

PDF is still better for vector/markup based "ebooks" so this plugin will not try to convert documents it detects having less than 1 raster image per page.  

Installation
---
1. Right click the preferences button in calibre, select get new plugins, scroll down the list and choose the DjVuMaker plugin to install
   * Or, download the zip and install it from the shell

     ````bash
   wget https://github.com/kfix/calibre_plugin_djvumaker/archive/master.zip
   calibre-customize -b master.zip
     ````
   * Or++, clone this repo and install from source

     ````bash
   git clone github.com/kfix/calibre-plugin-djvumaker
   cd calibre-plugin-djvumaker
   ./__init__.py
     ````
2. [Required] Build the conversion programs (**fixme: works only on OSX**)  
```calibre-debug -R djvumaker install_deps``` 
3. [Optional] run a test conversion out-of-GUI against the included PDF.  
```calibre-debug -R djvumaker test.pdf```
4. (Re)start Calibre and start converting your PDF books!  

Under the Hood
---
There are a few implementations of DjVU tools in the wild, but the fastest and most robust free one is the DjVuLibre suite and its Ghostscript plugin "GsDjvu".  
GsDjvu was witlessly licensed by AT&T with a "free" but GPL-incompatible license which makes pre-compiled packages impossible to publically distribute.  
Therefore both packages must be built by the user in a complicated procedure, which the plugin tries to facilitate when installed into Calibre.  


Q: Why not write a "standard" Conversion Plugin for DjVU?
---
Calibre's conversion API currently supports two pipelines:  
1) markup-based ebooks (book.xfmt > book.OEB > book.yfmt): useless for working on image-based scans.
2) comic books (*.cbz): unusably slow for library books due to its over-reliance on Python for its transform pipeline.  

Only ghostscript+gsdjvu delivers usable conversion times for large scanned books.  
Patching Calibre's conversion API to add a 3rd pipeline to support them would be far more involved than this sub-500-line plugin (excluding these explanations :-).  

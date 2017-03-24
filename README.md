DjVuMaker Plugin for Calibre
---
This plugin adds DJVU output conversion for Postscript documents (*.pdf, .ps).
Files can be converted through a GUI menu and optionally as FileType hook for automatically converting imports of all Postscript documents.

![GUI menu](/screenshot_menu.png?raw=true)
![Job log](/screenshot_job.png?raw=true)

DjVU format is ideal for reading large black & white scanned Google Books on E-Readers with >300MB RAM and >2GB flash.
Big 100+ page books scanned into PDF format usually slow these devices' built-in software to a halt.

To read DJVU files on the Kindle, I suggest koreader/koreader.

PDF is still better for vector/markup based "ebooks" so this plugin will not try to convert documents it detects having less than 1 raster image per page.

Installation
---
1. Right click the preferences button in calibre, select get new plugins, scroll down the list and choose the DjVuMaker plugin to install
   * Or clone this repo and install from source
   ```bash
   git clone https://github.com/kfix/calibre_plugin_djvumaker
   cd calibre_plugin_djvumaker
   calibre-customize -b ./
   ```
2. [Required] Build the conversion programs (**fixme: works only on macOS**, check next section for solution for other systems)\
    ```calibre-debug -r djvumaker -- backend install djvudigital```
3. (Re)start Calibre and start converting your PDF books!

4. [Optional] go to Preferences -> Interface::Toolbars so you can place the DJVU menu where you see fit.

Installation of secondary backend
---
For all having troubles with building GsDjvu there is possibility to install secondary backend - [pdf2djvu](http://jwilk.net/software/pdf2djvu).
The *pdf2djvu* is a pdf to djvu converter developed by Jakub Wilk ([GitHub](https://github.com/jwilk/pdf2djvu)).
Although produces less compresed files than djvudigital it's installation is much simplier. For Windows (**fixme: works only on Windows**) there is also a posibility to install it through *this* plugin:
```bash
calibre-debug -r djvumaker -- backend install pdf2djvu
calibre-debug -r djvumaker -- backend set pdf2djvu
```

Also you can just add pdf2djvu to your path and:
```calibre-debug -r djvumaker -- backend set pdf2djvu```

The main diferences betwent pdf2djvu and djvudigital are listed [here](https://github.com/jwilk/pdf2djvu/blob/master/doc/djvudigital.txt).

Under the Hood
---
There are a few implementations of DjVU tools in the wild, but the fastest and most robust free one is the DjVuLibre suite and its Ghostscript plugin "GsDjvu".
GsDjvu was witlessly licensed by AT&T with a "free" but GPL-incompatible license which makes pre-compiled packages impossible to publically distribute.
Therefore both packages must be built by the user in a complicated procedure, which the plugin tries to facilitate when installed into Calibre.


Q: Why not write a "standard" Conversion Plugin for DjVU?
---
Calibre's conversion API currently supports two pipelines:
1. markup-based ebooks (book.xfmt > book.OEB > book.yfmt): useless for working on image-based scans.
2. comic books (*.cbz): unusably slow for library books due to its over-reliance on Python for its transform pipeline.

Only ghostscript+gsdjvu delivers usable conversion times for large scanned books.
Patching Calibre's conversion API to add a 3rd pipeline to support them would be far more involved than this sub-500-line plugin (excluding these explanations :-).

CLI
---
```
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
      -y, --yes     sets plugin to convert PDF files after import (do not work for pdf2djvu)
      -n, --no      sets plugin to do not convert PDF files after import (default)

    install_deps  (depreciated) alias for `calibre-debug -r djvumaker -- backend install djvudigital`
    convert_all   (depreciated) alias for `calibre-debug -r djvumaker -- convert --all`

optional arguments:
  -h, --help     show help message and exit
  -V, --version  show plugin's version number and exit
```
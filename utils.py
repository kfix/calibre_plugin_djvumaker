#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)
import argparse
import urllib
import urllib2
import urlparse
import os.path
import subprocess

from calibre.constants import (isosx, iswindows, islinux, isbsd)
    
def create_cli_parser(self_DJVUmaker, PLUGINNAME, PLUGINVER_DOT):
    parser = argparse.ArgumentParser(prog="calibre-debug -r {} -- ".format(PLUGINNAME))
    parser.add_argument('-V', '--version', action='version', version='v{}'.format(PLUGINVER_DOT),
                        help="show plugin's version number and exit")
    subparsers = parser.add_subparsers(metavar='command')       
    
    parser_backend = subparsers.add_parser('backend', help='Backends handling. See '
                                            '`{}backend --help`'.format(parser.prog))
    parser_backend.set_defaults(func=self_DJVUmaker.cli_backend)
    parser_backend.add_argument('command', choices=['install', 'set'],
                                help='installs or sets backend')
    parser_backend.add_argument('backend', choices=['djvudigital', 'pdf2djvu'],
                                        help='choosed backend', nargs="?")

    parser_convert = subparsers.add_parser('convert', help='Convert file to djvu')
    parser_convert.set_defaults(func=self_DJVUmaker.cli_convert)
    group_convert = parser_convert.add_mutually_exclusive_group(required=True)
    group_convert.add_argument('-p', "--path", 
                                help="convert file under PATH to djvu using default settings",
                                action="store", type=str)
    group_convert.add_argument('-i', "--id", 
                                help="convert file with ID to djvu using default settings", 
                                action="store", type=int)
    group_convert.add_argument("--all", help="convert all pdf files in calibre's library", 
                                action="store_true")

    parser_install_deps = subparsers.add_parser('install_deps', 
        help='(depreciated) alias for `{}backend install djvudigital`'.format(parser.prog))
    parser_install_deps.set_defaults(func=self_DJVUmaker.cli_backend, command='install',
                                     backend='djvudigital')
    parser_convert_all  = subparsers.add_parser('convert_all', 
        help='(depreciated) alias for `{}convert --all`'.format(parser.prog))
    parser_convert_all.set_defaults(func=self_DJVUmaker.cli_convert, all=True)
    return parser

def install_pdf2djvu(log=print):
    try:        
        # on python 3.3 exist os.which
        sbp_out = subprocess.check_output(['pdf2djvu', '--version'],
                                            stderr= subprocess.STDOUT)
        curr_version = sbp_out.splitlines()[0].split()[1]
        log('Version {} of pdf2djvu is found locally.'.format(curr_version))
    except OSError:
        curr_version = None
        log('pdf2djvu is not found locally.')
    except:
        log('Output:' + sbp_out)
        raise    

    # github_latest_url = r'https://github.com/jwilk/pdf2djvu/releases/latest'
    # github_page = urllib2.urlopen(github_latest_url)
    # new_version = get_url_basename(github_page.geturl())
    new_version = '0.9.5'
    log('Version {} of pdf2djvu is available on program\'s GitHub page.'.format(new_version))

    def version_str_to_intlist(verstr):
        return [int(x) for x in verstr.split('.')]

    if curr_version is None:
        log('Do you want to dowload current version of pdf2djvu?')
        if raw_input('y/n') != 'y':
            raise Exception('bad input')
        fpath = download_pdf2djvu(new_version, log)
        unpack_pdf2djvu(fpath, log)

    curr_ver_intlist = version_str_to_intlist(curr_version)
    new_ver_intlist  = version_str_to_intlist(new_version)    
    if new_ver_intlist == curr_ver_intlist:                   
        log('You have already current version of pdf2djvu.')
    elif new_ver_intlist > curr_ver_intlist:
        log('Do you want to download newer version of pdf2djvu?')
        if raw_input('y/n') != 'y':
            raise Exception('bad input')
        fpath = download_pdf2djvu(new_version, log)
        unpack_pdf2djvu(fpath, log)  
    
    else: #new_ver_intlist < curr_ver_intlist
        raise Exception("Newer version than current pdf2djvu found.")

def get_url_basename(url):
    return os.path.basename(urlparse.urlsplit(url).path)

def download_pdf2djvu(new_version, log):
    def gen_zip_url(code):
        return r'https://github.com/jwilk/pdf2djvu/releases/download/{}/pdf2djvu-win32-{}.zip'.format(code, code) 
    def gen_tar_url(code):
        return r'https://github.com/jwilk/pdf2djvu/releases/download/{}/pdf2djvu-{}.tar.xz'.format(code, code)

    fallback_version = '0.9.5'
    if iswindows:                   
        fallback_arch_url = gen_zip_url(fallback_version)
        arch_url = gen_zip_url(new_version)
    else:
        fallback_arch_url = gen_tar_url(fallback_version)
        arch_url = gen_tar_url(new_version)                
    
    log('Downloading current version of pdf2djvu...')
    fpath, msg = urllib.urlretrieve(arch_url, os.path.join('plugins', get_url_basename(arch_url)))
    if msg['Status'].split()[0] not in ['200', '302']:
        log('Cannot download current version {} from GitHub.'.format(new_version))
        if new_version != fallback_version:
            log('Trying download version {}...'.format(fallback_version))
            fpath, msg_fallback = urllib.urlretrieve(fallback_arch_url, os.path.join('plugins', 
                                                        get_url_basename(fallback_arch_url)))
            if msg_fallback.split()[0] not in ['200', '302']:
                raise Exception('Cannot download pdf2djvu.')
    return fpath

def unpack_pdf2djvu(fpath, log):        
    if iswindows:
        from zipfile import ZipFile
        with ZipFile(fpath, 'r') as myzip:
            myzip.extractall()
    else:
        raise Exception('Python 2.7 Standard Library cannot unpack tar.xz archive, do this manualy')
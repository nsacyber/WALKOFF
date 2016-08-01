#!/usr/bin/python -B
# -*- mode: Python; tab-width: 4; indent-tabs-mode: nil; -*-
# ex: set tabstop=4
# Please do not change the two lines above. See PEP 8, PEP 263.
'''Run tests, create markdown and HTML documentation from the test output

Last validated to work with:
- Python 2.7.5
'''
__author__ = 'Jim Olsen (jim@lifehack.com)'
__version__ = '2.1.0'

'''
N.B. I go through great lengths to keep this a single monolithic script.
     It's a thing.
'''
import os
import sys
import time
import argparse
import subprocess
import logging
import inspect
import json
import collections
import getpass
import fnmatch
import glob
from ConfigParser import SafeConfigParser
from argparse import ArgumentDefaultsHelpFormatter as A1  # noqa
from argparse import RawDescriptionHelpFormatter as A2  # noqa
from urllib2 import Request, urlopen, HTTPError, URLError

reload(sys)
sys.setdefaultencoding("utf-8")
sys.dont_write_bytecode = True

my_file = os.path.abspath(sys.argv[0])
my_dir = os.path.dirname(my_file)

pname = os.path.splitext(os.path.basename(sys.argv[0]))[0]

print(
    '{} v{} by {}'
).format(pname, __version__, __author__)


'''
# console support for debugging
import rlcompleter
import readline
import atexit
import pprint


def debug_list(debuglist):
    for x in debuglist:
        debug_obj(x)


def debug_obj(debugobj):
    pprint.pprint(vars(debugobj))


def introspect(object, depth=0):
    import types
    print "%s%s: %s\n" % (depth * "\t", object, [
        x for x in dir(object) if x[:2] != "__"])
    depth = depth + 1
    for x in dir(object):
        if x[:2] == "__":
            continue
        subobj = getattr(object, x)
        print "%s%s: %s" % (depth * "\t", x, subobj)
        if isinstance(subobj, types.InstanceType) and dir(subobj) != []:
            introspect(subobj, depth=depth + 1)
            print


def save_history():
    readline.write_history_file()

readline.read_history_file()
atexit.register(save_history)
del rlcompleter
'''

# I know this is nasty. I don't care.
github_css = u'''body\n{\n  font-size:15px;\n  line-height:1.7;\n  overflow-x:hidden;\n\n    background-color: white;\n    border-radius: 3px;\n    border: 3px solid #EEE;\n    box-shadow: inset 0 0 0 1px #CECECE;\n    font-family: Helvetica, arial, freesans, clean, sans-serif;\n    max-width: 912px;\n    padding: 30px;\n    margin: 2em auto;\n\n    color:#333333;\n}\n\n\n.body-classic{\n  color:#444;\n  font-family:Georgia, Palatino, \'Palatino Linotype\', Times, \'Times New Roman\', "Hiragino Sans GB", "STXihei", "\u5fae\u8f6f\u96c5\u9ed1", serif;\n  font-size:16px;\n  line-height:1.5em;\n  background:#fefefe;\n  width: 65em;\n  margin: 10px auto;\n  padding: 1em;\n  outline: 1300px solid #FAFAFA;\n}\n\nbody>:first-child\n{\n  margin-top:0!important;\n}\n\nbody>:last-child\n{\n  margin-bottom:0!important;\n}\n\nblockquote,dl,ol,p,pre,table,ul {\n  border: 0;\n  margin: 15px 0;\n  padding: 0;\n}\n\nbody a {\n  color: #4183c4;\n  text-decoration: none;\n}\n\nbody a:hover {\n  text-decoration: underline;\n}\n\nbody a.absent\n{\n  color:#c00;\n}\n\nbody a.anchor\n{\n  display:block;\n  padding-left:30px;\n  margin-left:-30px;\n  cursor:pointer;\n  position:absolute;\n  top:0;\n  left:0;\n  bottom:0\n}\n\n/*h4,h5,h6{ font-weight: bold; }*/\n\n.octicon{\n  font:normal normal 16px sans-serif;\n  width: 1em;\n  height: 1em;\n  line-height:1;\n  display:inline-block;\n  text-decoration:none;\n  -webkit-font-smoothing:antialiased\n}\n\n.octicon-link {\n  background: url("data:image/svg+xml;utf8,<?xml version=\'1.0\' standalone=\'no\'?> <!DOCTYPE svg PUBLIC \'-//W3C//DTD SVG 1.1//EN\' \'http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd\'> <svg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 1024 832\'> <metadata>Copyright (C) 2013 by GitHub</metadata> <!-- scale(0.01565557729941) --> <path transform=\'\' d=\'M768 64h-192s-254 0-256 256c0 22 3 43 8 64h137c-11-19-18-41-18-64 0-128 128-128 128-128h192s128 0 128 128-128 128-128 128 0 64-64 128h64s256 0 256-256-256-256-256-256z m-72 192h-137c11 19 18 41 18 64 0 128-128 128-128 128h-192s-128 0-128-128 128-128 128-128-4-65 66-128h-66s-256 0-256 256 256 256 256 256h192s256 0 256-256c0-22-4-44-8-64z\'/> </svg>");\n  background-size: contain;\n  background-repeat: no-repeat;\n  background-position: bottom;\n}\n\n.octicon-link:before{\n  content:\'\\a0\';\n}\n\nbody h1,body h2,body h3,body h4,body h5,body h6{\n  margin:1em 0 15px;\n  padding:0;\n  font-weight:bold;\n  line-height:1.7;\n  cursor:text;\n  position:relative\n}\n\nbody h1 .octicon-link,body h2 .octicon-link,body h3 .octicon-link,body h4 .octicon-link,body h5 .octicon-link,body h6 .octicon-link{\n  display:none;\n  color:#000\n}\n\nbody h1:hover a.anchor,body h2:hover a.anchor,body h3:hover a.anchor,body h4:hover a.anchor,body h5:hover a.anchor,body h6:hover a.anchor{\n  text-decoration:none;\n  line-height:1;\n  padding-left:0;\n  margin-left:-22px;\n  top:15%\n}\n\nbody h1:hover a.anchor .octicon-link,body h2:hover a.anchor .octicon-link,body h3:hover a.anchor .octicon-link,body h4:hover a.anchor .octicon-link,body h5:hover a.anchor .octicon-link,body h6:hover a.anchor .octicon-link{\n  display:inline-block\n}\n\nbody h1 tt,body h1 code,body h2 tt,body h2 code,body h3 tt,body h3 code,body h4 tt,body h4 code,body h5 tt,body h5 code,body h6 tt,body h6 code{\n  font-size:inherit\n}\n\nbody h1{\n  font-size:2.5em;\n  border-bottom:1px solid #ddd\n}\n\nbody h2{\n  font-size:2em;\n  border-bottom:1px solid #eee\n}\n\nbody h3{\n  font-size:1.5em\n}\n\nbody h4{\n  font-size:1.2em\n}\n\nbody h5{\n  font-size:1em\n}\n\nbody h6{\n  color:#777;\n  font-size:1em\n}\n\nbody p,body blockquote,body ul,body ol,body dl,body table,body pre{\n  margin:15px 0\n}\n\nbody h1 tt,body h1 code,body h2 tt,body h2 code,body h3 tt,body h3 code,body h4 tt,body h4 code,body h5 tt,body h5 code,body h6 tt,body h6 code\n{\n  font-size:inherit;\n}\n\n\nbody hr\n{\n  background-image: url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAYAAAAECAYAAACtBE5DAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAyJpVFh0WE1MOmNvbS5hZG9iZS54bXAAAAAAADw/eHBhY2tldCBiZWdpbj0i77u/IiBpZD0iVzVNME1wQ2VoaUh6cmVTek5UY3prYzlkIj8+IDx4OnhtcG1ldGEgeG1sbnM6eD0iYWRvYmU6bnM6bWV0YS8iIHg6eG1wdGs9IkFkb2JlIFhNUCBDb3JlIDUuMC1jMDYwIDYxLjEzNDc3NywgMjAxMC8wMi8xMi0xNzozMjowMCAgICAgICAgIj4gPHJkZjpSREYgeG1sbnM6cmRmPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5LzAyLzIyLXJkZi1zeW50YXgtbnMjIj4gPHJkZjpEZXNjcmlwdGlvbiByZGY6YWJvdXQ9IiIgeG1sbnM6eG1wPSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvIiB4bWxuczp4bXBNTT0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL21tLyIgeG1sbnM6c3RSZWY9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9zVHlwZS9SZXNvdXJjZVJlZiMiIHhtcDpDcmVhdG9yVG9vbD0iQWRvYmUgUGhvdG9zaG9wIENTNSBNYWNpbnRvc2giIHhtcE1NOkluc3RhbmNlSUQ9InhtcC5paWQ6OENDRjNBN0E2NTZBMTFFMEI3QjRBODM4NzJDMjlGNDgiIHhtcE1NOkRvY3VtZW50SUQ9InhtcC5kaWQ6OENDRjNBN0I2NTZBMTFFMEI3QjRBODM4NzJDMjlGNDgiPiA8eG1wTU06RGVyaXZlZEZyb20gc3RSZWY6aW5zdGFuY2VJRD0ieG1wLmlpZDo4Q0NGM0E3ODY1NkExMUUwQjdCNEE4Mzg3MkMyOUY0OCIgc3RSZWY6ZG9jdW1lbnRJRD0ieG1wLmRpZDo4Q0NGM0E3OTY1NkExMUUwQjdCNEE4Mzg3MkMyOUY0OCIvPiA8L3JkZjpEZXNjcmlwdGlvbj4gPC9yZGY6UkRGPiA8L3g6eG1wbWV0YT4gPD94cGFja2V0IGVuZD0iciI/PqqezsUAAAAfSURBVHjaYmRABcYwBiM2QSA4y4hNEKYDQxAEAAIMAHNGAzhkPOlYAAAAAElFTkSuQmCC);\n  background-repeat: repeat-x;\n  /*background:transparent url(http://overblown.net/files/markdown/dirty-shade.png) repeat-x 0 0;*/\n  background-color: transparent;\n  background-position: 0;\n  border:0 none;\n  color:#ccc;\n  height:4px;\n  margin:15px 0;\n  padding:0;\n}\n\nbody li p.first\n{\n  display:inline-block;\n}\n\nbody ul,body ol\n{\n  padding-left:30px;\n}\n\nbody ul.no-list,body ol.no-list\n{\n  list-style-type:none;\n  padding:0;\n}\n\nbody ul ul,body ul ol,body ol ol,body ol ul\n{\n  margin-bottom:0;\n  margin-top:0;\n}\n\nbody dl\n{\n  padding:0;\n}\n\nbody dl dt\n{\n  font-size:14px;\n  font-style:italic;\n  font-weight:700;\n  margin-top:15px;\n  padding:0;\n}\n\nbody dl dd\n{\n  margin-bottom:15px;\n  padding:0 15px;\n}\n\nbody blockquote\n{\n  border-left:4px solid #DDD;\n  color:#777;\n  padding:0 15px;\n}\n\nbody blockquote>:first-child\n{\n  margin-top:0;\n}\n\nbody blockquote>:last-child\n{\n  margin-bottom:0;\n}\n\nbody table\n{\n  display:block;\n  overflow:auto;\n  width:100%;\n  border-collapse: collapse;\n  border-spacing: 0;\n  padding: 0;\n}\n\nbody table th\n{\n  font-weight:700;\n}\n\nbody table th,body table td\n{\n  border:1px solid #ddd;\n  padding:6px 13px;\n}\n\nbody table tr\n{\n  background-color:#fff;\n  border-top:1px solid #ccc;\n}\n\nbody table tr:nth-child(2n)\n{\n  background-color:#f8f8f8;\n}\n\nbody img\n{\n  -moz-box-sizing:border-box;\n  box-sizing:border-box;\n  max-width:100%;\n}\n\nbody span.frame\n{\n  display:block;\n  overflow:hidden;\n}\n\nbody span.frame>span\n{\n  border:1px solid #ddd;\n  display:block;\n  float:left;\n  margin:13px 0 0;\n  overflow:hidden;\n  padding:7px;\n  width:auto;\n}\n\nbody span.frame span img\n{\n  display:block;\n  float:left;\n}\n\nbody span.frame span span\n{\n  clear:both;\n  color:#333;\n  display:block;\n  padding:5px 0 0;\n}\n\nbody span.align-center\n{\n  clear:both;\n  display:block;\n  overflow:hidden;\n}\n\nbody span.align-center>span\n{\n  display:block;\n  margin:13px auto 0;\n  overflow:hidden;\n  text-align:center;\n}\n\nbody span.align-center span img\n{\n  margin:0 auto;\n  text-align:center;\n}\n\nbody span.align-right\n{\n  clear:both;\n  display:block;\n  overflow:hidden;\n}\n\nbody span.align-right>span\n{\n  display:block;\n  margin:13px 0 0;\n  overflow:hidden;\n  text-align:right;\n}\n\nbody span.align-right span img\n{\n  margin:0;\n  text-align:right;\n}\n\nbody span.float-left\n{\n  display:block;\n  float:left;\n  margin-right:13px;\n  overflow:hidden;\n}\n\nbody span.float-left span\n{\n  margin:13px 0 0;\n}\n\nbody span.float-right\n{\n  display:block;\n  float:right;\n  margin-left:13px;\n  overflow:hidden;\n}\n\nbody span.float-right>span\n{\n  display:block;\n  margin:13px auto 0;\n  overflow:hidden;\n  text-align:right;\n}\n\nbody code,body tt\n{\n  background-color:#f8f8f8;\n  border:1px solid #ddd;\n  border-radius:3px;\n  margin:0 2px;\n  padding:0 5px;\n}\n\nbody code\n{\n  white-space:nowrap;\n}\n\n\ncode,pre{\n  font-family:Consolas, "Liberation Mono", Courier, monospace;\n  font-size:12px\n}\n\nbody pre>code\n{\n  background:transparent;\n  border:none;\n  margin:0;\n  padding:0;\n  white-space:pre;\n}\n\nbody .highlight pre,body pre\n{\n  background-color:#f8f8f8;\n  border:1px solid #ddd;\n  font-size:13px;\n  line-height:19px;\n  overflow:auto;\n  padding:6px 10px;\n  border-radius:3px\n}\n\nbody pre code,body pre tt\n{\n  background-color:transparent;\n  border:none;\n  margin:0;\n  padding:0;\n}\n\nbody .task-list{\n  list-style-type:none;\n  padding-left:10px\n}\n\n.task-list-item{\n  padding-left:20px\n}\n\n.task-list-item label{\n  font-weight:normal\n}\n\n.task-list-item.enabled label{\n  cursor:pointer\n}\n\n.task-list-item+.task-list-item{\n  margin-top:5px\n}\n\n.task-list-item-checkbox{\n  float:left;\n  margin-left:-20px;\n  margin-top:7px\n}\n\n\n.highlight{\n  background:#ffffff\n}\n\n.highlight .c{\n  color:#999988;\n  font-style:italic\n}\n\n.highlight .err{\n  color:#a61717;\n  background-color:#e3d2d2\n}\n\n.highlight .k{\n  font-weight:bold\n}\n\n.highlight .o{\n  font-weight:bold\n}\n\n.highlight .cm{\n  color:#999988;\n  font-style:italic\n}\n\n.highlight .cp{\n  color:#999999;\n  font-weight:bold\n}\n\n.highlight .c1{\n  color:#999988;\n  font-style:italic\n}\n\n.highlight .cs{\n  color:#999999;\n  font-weight:bold;\n  font-style:italic\n}\n\n.highlight .gd{\n  color:#000000;\n  background-color:#ffdddd\n}\n\n.highlight .gd .x{\n  color:#000000;\n  background-color:#ffaaaa\n}\n\n.highlight .ge{\n  font-style:italic\n}\n\n.highlight .gr{\n  color:#aa0000\n}\n\n.highlight .gh{\n  color:#999999\n}\n\n.highlight .gi{\n  color:#000000;\n  background-color:#ddffdd\n}\n\n.highlight .gi .x{\n  color:#000000;\n  background-color:#aaffaa\n}\n\n.highlight .go{\n  color:#888888\n}\n\n.highlight .gp{\n  color:#555555\n}\n\n.highlight .gs{\n  font-weight:bold\n}\n\n.highlight .gu{\n  color:#800080;\n  font-weight:bold\n}\n\n.highlight .gt{\n  color:#aa0000\n}\n\n.highlight .kc{\n  font-weight:bold\n}\n\n.highlight .kd{\n  font-weight:bold\n}\n\n.highlight .kn{\n  font-weight:bold\n}\n\n.highlight .kp{\n  font-weight:bold\n}\n\n.highlight .kr{\n  font-weight:bold\n}\n\n.highlight .kt{\n  color:#445588;\n  font-weight:bold\n}\n\n.highlight .m{\n  color:#009999\n}\n\n.highlight .s{\n  color:#d14\n}\n\n.highlight .n{\n  color:#333333\n}\n\n.highlight .na{\n  color:#008080\n}\n\n.highlight .nb{\n  color:#0086B3\n}\n\n.highlight .nc{\n  color:#445588;\n  font-weight:bold\n}\n\n.highlight .no{\n  color:#008080\n}\n\n.highlight .ni{\n  color:#800080\n}\n\n.highlight .ne{\n  color:#990000;\n  font-weight:bold\n}\n\n.highlight .nf{\n  color:#990000;\n  font-weight:bold\n}\n\n.highlight .nn{\n  color:#555555\n}\n\n.highlight .nt{\n  color:#000080\n}\n\n.highlight .nv{\n  color:#008080\n}\n\n.highlight .ow{\n  font-weight:bold\n}\n\n.highlight .w{\n  color:#bbbbbb\n}\n\n.highlight .mf{\n  color:#009999\n}\n\n.highlight .mh{\n  color:#009999\n}\n\n.highlight .mi{\n  color:#009999\n}\n\n.highlight .mo{\n  color:#009999\n}\n\n.highlight .sb{\n  color:#d14\n}\n\n.highlight .sc{\n  color:#d14\n}\n\n.highlight .sd{\n  color:#d14\n}\n\n.highlight .s2{\n  color:#d14\n}\n\n.highlight .se{\n  color:#d14\n}\n\n.highlight .sh{\n  color:#d14\n}\n\n.highlight .si{\n  color:#d14\n}\n\n.highlight .sx{\n  color:#d14\n}\n\n.highlight .sr{\n  color:#009926\n}\n\n.highlight .s1{\n  color:#d14\n}\n\n.highlight .ss{\n  color:#990073\n}\n\n.highlight .bp{\n  color:#999999\n}\n\n.highlight .vc{\n  color:#008080\n}\n\n.highlight .vg{\n  color:#008080\n}\n\n.highlight .vi{\n  color:#008080\n}\n\n.highlight .il{\n  color:#009999\n}\n\n.highlight .gc{\n  color:#999;\n  background-color:#EAF2F5\n}\n\n.type-csharp .highlight .k{\n  color:#0000FF\n}\n\n.type-csharp .highlight .kt{\n  color:#0000FF\n}\n\n.type-csharp .highlight .nf{\n  color:#000000;\n  font-weight:normal\n}\n\n.type-csharp .highlight .nc{\n  color:#2B91AF\n}\n\n.type-csharp .highlight .nn{\n  color:#000000\n}\n\n.type-csharp .highlight .s{\n  color:#A31515\n}\n\n.type-csharp .highlight .sc{\n  color:#A31515\n}\n
'''


def jsonify(obj):
    return json.dumps(obj, sort_keys=True, indent=4)


def get_now():
    return time.strftime('%Y_%m_%d-%H_%M_%S', time.localtime())


def fn_gen(ext):
    fn = "{}_{}.{}".format(get_now(), pname, ext)
    return fn


def pathfix(p):
    return os.path.abspath(os.path.expanduser(p))


def search_dir(path, filematch, recurse=True):
    items = []
    if os.path.isdir(path):
        if recurse:
            for root, dirnames, filenames in os.walk(path):
                for filename in fnmatch.filter(filenames, filematch):
                    items.append(os.path.join(root, filename))
        else:
            items = glob.glob('%s/%s' % (path, filematch))
    return items


def save_utf8(filename, text):
    f = open(filename, 'w')
    f.write(text.encode('utf-8'))
    f.close()


def load_utf8(filename):
    return open(filename, 'r').read().decode('utf-8')


def run_command(cmdline, envvars={}, shell=True):
    '''
    Execute a command and return it's return code, stdout, and stderr.
    '''
    # split up the command string into an array (using space as delim)
    # (only needed if shell=False)
    if not shell:
        cmdline = cmdline.split()

    # if a non empty envvars dictionary is supplied, pass that to the shell
    if envvars:
        p = subprocess.Popen(
            cmdline,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            env=envvars)
    else:
        # run the process, capturing stdout and stderr pipes
        p = subprocess.Popen(
            cmdline,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True)

    # communicate() returns stdout and stderr in a tuple,
    # store that in ph_stdout and ph_stderr
    ph = {}
    ph['stdout'], ph['stderr'] = p.communicate()

    ph['exitcode'] = p.returncode

    # return the return code, stdout, and stderr
    return ph


class CustomFormatter(A1, A2):
    pass


class MyParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        if 'formatter_class' not in kwargs:
            kwargs['formatter_class'] = CustomFormatter
        argparse.ArgumentParser.__init__(self, *args, **kwargs)

    def error(self, message):
        self.print_help()
        print('ERROR:{}:{}\n'.format(pname, message))
        sys.exit(2)


class MDTest():

    C_SECT = 'CONFIG'
    VALMSG = 'valid_msg'
    VALTESTS = 'validtests'
    DEPTH = 'headerdepth'
    DEPTHDEF = 1
    CMD = 'cmd'
    CMDOUTTYPE = 'bash'
    MH = 'mainheader'
    MHDEF = ''
    OUTBOOL = 'output_blocks'
    OUTBOOLDEF = True
    VALBOOL = 'valid_blocks'
    VALBOOLDEF = True
    OUTDIR = 'outdir'
    OUTDIRDEF = '/tmp/{}'.format(get_now())
    OUTTYPE = 'output_type'
    BASENAME = 'basename'
    BASENAMEDEF = ''
    PRERUN = 'precleanup'
    NORUN = 'norun'
    NOTES = 'notes'
    CI = 'contact'
    CIDEF = "Username: **{}**".format(getpass.getuser())
    TITLE = 'title'
    TITLEDEF = ''
    CONTENTFN = 'contentfilename'
    CONTENTTYPE = 'contenttype'
    CONTENTTEXT = 'contenttext'
    AFTERFN = 'afterfilename'
    AFTERTYPE = 'aftertype'
    TOCBOOL = 'TOC'
    TOCBOOLDEF = True

    # default config constant
    DEFAULT_CONF = {
        MH: MHDEF,
        OUTBOOL: OUTBOOLDEF,
        VALBOOL: VALBOOLDEF,
        OUTDIR: OUTDIRDEF,
        BASENAME: BASENAMEDEF,
        TOCBOOL: TOCBOOLDEF,
        CI: CIDEF,
    }

    # github oauth token
    github_token = ''

    # extensions used by save_files()
    MDEXT = 'md'
    HTMLEXT = 'html'

    def __init__(self, filehandle, **kwargs):
        # where we store this instances config
        self.conf = {}

        # this instances tracker
        self.t = collections.OrderedDict()

        # where we store the markdown strings for this instance
        self.md = []
        self.mdtext = ''

        # where we store the html converted markdown for this instance
        self.htmltext = ''

        self.fh = filehandle
        self.filename = self.fh.name
        self.conf.update(self.DEFAULT_CONF)

        self.github_token = kwargs.get('github_token', '')
        skipconvert = kwargs.get('skipconvert', False)
        convertonly = kwargs.get('convertonly', False)
        title = kwargs.get(self.TITLE, '')
        basename = kwargs.get(self.BASENAME, '')
        outdir = kwargs.get(self.OUTDIR, '')

        self.conf[self.TITLE] = title or self.get_basename()
        self.conf[self.BASENAME] = basename or self.get_basename()
        self.conf[self.OUTDIR] = pathfix(outdir or self.OUTDIRDEF)

        if convertonly:
            self.mdtext = filehandle.read()
            self.htmltext = self.convert_md()
            if self.htmltext:
                self.save_file(self.HTMLEXT, self.htmltext)
            return

        logging.info("Parsing {0.name}".format(filehandle))
        self.cp = SafeConfigParser()
        self.cp.readfp(filehandle)
        self.sections = self.cp.sections()
        logging.info("Sections Found: {}".format(self.sections))

        self.loadconfig()
        self.vtmethods = [x for x in dir(self) if 'val_test' in x]

        self.run_sections()
        self.create_md()

        if not skipconvert:
            self.htmltext = self.convert_md()

        self.save_files()

    def get_basename(self):
        return os.path.basename(self.filename).split('.')[:1][0]

    def loadconfig(self):
        if self.C_SECT in self.sections:
            logging.debug("Updating config from ini..")
            self.setoptbool(self.C_SECT, self.OUTBOOL, self.conf)
            self.setoptbool(self.C_SECT, self.VALBOOL, self.conf)
            self.setoptbool(self.C_SECT, self.TOCBOOL, self.conf)
            self.setoptstr(self.C_SECT, self.MH, self.conf)
            self.setoptstr(self.C_SECT, self.TITLE, self.conf)
            self.setoptstr(self.C_SECT, self.BASENAME, self.conf)
            self.setoptstr(self.C_SECT, self.OUTDIR, self.conf)
            self.setoptstr(self.C_SECT, self.CI, self.conf)
            self.conf[self.OUTDIR] = pathfix(self.conf[self.OUTDIR])
            logging.info("Loaded section: '{}'".format(self.C_SECT))
        logging.debug(jsonify(self.conf))

    def setoptbool(self, section, item, d):
        try:
            d[item] = self.cp.getboolean(section, item)
        except:
            pass

    def setoptstr(self, section, item, d):
        try:
            d[item] = self.cp.get(section, item)
        except:
            pass

    def run_sections(self):
        if not self.sections:
            m = (
                "No sections found in: {}, unable to run!"
            ).format(self.filename)
            raise Exception(m)
        for sectname in self.sections:
            if sectname == self.C_SECT:
                continue
            self.gather_section(sectname)
            self.run_section(sectname)
            self.val_section(sectname)

    def gather_section(self, sectname):
        try:
            s = self.cp.items(sectname)
        except:
            logging.error((
                "Problem gathering section: {}"
            ).format(sectname), exc_info=True)
            raise

        s = dict(s)
        self.t[sectname] = {}
        self.t[sectname]['SECTION'] = s
        logging.debug(jsonify(s))
        logging.info("Loaded section: '{}'".format(sectname))

    def run_section(self, sectname):
        s = self.t[sectname]

        cmd = s['SECTION'].get(self.CMD, '')
        norun = s['SECTION'].get(self.NORUN, '')
        if norun:
            return

        if not cmd and not norun:
            m = (
                "No {} specified in section: {}, unable to run! "
                "(supply norun: true if you don't want to run a command)"
            ).format(self.CMD, sectname)
            raise Exception(m)

        precleanup = s['SECTION'].get(self.PRERUN, '')
        if precleanup:
            logging.info("Running {}: {}".format(self.PRERUN, precleanup))
            pre_ret = run_command(precleanup)
            logging.info("Exit code: {}".format(pre_ret['exitcode']))

        self.gather_content(sectname)
        self.create_content(sectname)

        logging.info("Running command: {}".format(cmd))
        ret = run_command(cmd)
        s['RETURN'] = ret
        logging.debug(jsonify(ret))
        logging.info("Exit code: {}".format(ret['exitcode']))

    def gather_content(self, sectname):
        s = self.t[sectname]
        content = {}
        for k in sorted(s['SECTION']):
            if not k.startswith(self.CONTENTFN):
                continue
            fn = s['SECTION'][k]
            contentid = k.replace(self.CONTENTFN, '')
            typekey = '{}{}'.format(self.CONTENTTYPE, contentid)
            textkey = '{}{}'.format(self.CONTENTTEXT, contentid)
            ctype = s['SECTION'].get(typekey, '')
            ctext = s['SECTION'].get(textkey, '')
            ctext = ctext.decode('string_escape')
            logging.debug((
                "Found content in section {}: filename {}, type {}, text {}"
            ).format(sectname, fn, ctype, ctext))
            content[contentid] = {
                'cname': fn,
                'ctype': ctype,
                'ctext': ctext,
            }
        s['CONTENT'] = content

    def create_content(self, sectname):
        s = self.t[sectname]
        content = s.get('CONTENT', {})
        if not content:
            logging.debug("No content to create in {}".format(sectname))
            return
        for k, v in content.iteritems():
            fn = v.get('cname', '')
            ftext = v.get('ctext', '')
            if not fn:
                logging.warn((
                    "No filename supplied for content ID {}, unable to create!"
                ).format(k))
                continue
            logging.info(("Creating content ID {}, file {}").format(k, fn))
            fdir = os.path.dirname(fn)
            self.mk_dir(fdir)
            save_utf8(fn, ftext)

    def val_section(self, sectname):
        s = self.t[sectname]

        norun = s['SECTION'].get(self.NORUN, '')
        if norun:
            return

        valtests = s['SECTION'].get(self.VALTESTS, '')
        if not valtests:
            logging.warn((
                "No {} specified in section: {}, unable to validate!"
            ).format(self.VALTESTS, sectname))
            return

        valtests = [x.strip() for x in valtests.split(',')]
        s['VALRESULTS'] = {
            k: {'valid': None, 'msgs': []} for k in valtests
        }
        for vt in valtests:
            vtmeth = [x for x in self.vtmethods if x.endswith(vt)]
            if not vtmeth:
                logging.warn((
                    "Unable to find a validation method ending with '{}', "
                    "Unable to validate! List of validation methods: {}"
                ).format(vt, self.vtmethods))
                continue
            vtmeth = vtmeth[0]
            logging.debug((
                "Found validation method '{}'' from validtests entry '{}' "
                "in section: {}"
            ).format(vtmeth, vt, sectname))
            vtmeth = getattr(self, vtmeth)
            vtmeth(sectname, vt)

    def val_test_exitcode(self, sectname, vt):
        s = self.t[sectname]
        sect = s['SECTION']
        exitcode = int(sect.get('exitcode', 0))
        vt = s['VALRESULTS'][vt]
        ret = s.get('RETURN', {})
        if not ret:
            self.set_invalid(vt, 'No command was run')
            return
        if int(ret['exitcode']) == exitcode:
            self.set_valid(vt, 'Exit Code is {}'.format(exitcode))
        else:
            self.set_invalid(vt, 'Exit Code is not {}'.format(exitcode))

    def val_test_notexitcode(self, sectname, vt):
        s = self.t[sectname]
        sect = s['SECTION']
        exitcode = int(sect.get('exitcode', 0))
        vt = s['VALRESULTS'][vt]
        ret = s.get('RETURN', {})
        if not ret:
            self.set_invalid(vt, 'No command was run')
            return
        if int(ret['exitcode']) != exitcode:
            self.set_valid(vt, 'Exit Code is not {}'.format(exitcode))
        else:
            self.set_invalid(vt, 'Exit Code is {}'.format(exitcode))

    def val_test_file_exist(self, sectname, vt):
        s = self.t[sectname]
        sect = s['SECTION']
        file_exist = sect.get('file_exist', '')
        vt = s['VALRESULTS'][vt]
        ret = s.get('RETURN', {})
        if not ret:
            self.set_invalid(vt, 'No command was run')
            return
        if not file_exist:
            self.set_invalid(vt, 'No file_exist defined for this section')
            return
        if os.path.exists(file_exist):
            self.set_valid(vt, 'File {} exists'.format(file_exist))
        else:
            self.set_invalid(vt, 'File {} does not exist'.format(file_exist))

    def val_test_file_exist_contents(self, sectname, vt):
        s = self.t[sectname]
        sect = s['SECTION']
        file_exist = sect.get('file_exist', '')
        vt = s['VALRESULTS'][vt]
        ret = s.get('RETURN', {})
        if not ret:
            self.set_invalid(vt, 'No command was run')
            return
        if not file_exist:
            self.set_invalid(vt, 'No file_exist defined for this section')
            return
        if os.path.exists(file_exist):
            cf = open(file_exist)
            c = cf.read()
            cf.close()
            if len(c.splitlines()) >= 15:
                c = c.splitlines()[0:10]
                c.append('...trimmed for brevity...\n')
                c = '\n'.join(c)
            c = '\n\n```\n{}```'.format(c)

            self.set_valid(vt, 'File {} exists, content:{}'.format(file_exist, c))
        else:
            self.set_invalid(vt, 'File {} does not exist'.format(file_exist))

    def val_test_noerror(self, sectname, vt):
        s = self.t[sectname]
        sect = s['SECTION']
        vt = s['VALRESULTS'][vt]
        ret = s.get('RETURN', {})
        errormatch_def = 'Traceback ,Error occurred: ,ERROR:'
        errormatch = sect.get('errormatch', errormatch_def).split(',')
        errormatch = [x for x in errormatch if x]
        if not ret:
            self.set_invalid(vt, 'No command was run')
            return
        stdout = ret.get('stdout').strip().splitlines()
        stderr = ret.get('stderr').strip().splitlines()
        for x in errormatch:
            for y in stdout:
                if x in y:
                    self.set_invalid(vt, 'Found {} in standard output'.format(x))
                    return
            for y in stderr:
                if x in y:
                    self.set_invalid(vt, 'Found {} in standard error'.format(x))
                    return
        self.set_valid(vt, 'No error texts found in stderr/stdout')

    def val_test_filematch(self, sectname, vt):
        s = self.t[sectname]
        sect = s['SECTION']
        filematch = sect.get('filematch', '')
        dirmatch = sect.get('dirmatch', '')
        vt = s['VALRESULTS'][vt]
        ret = s.get('RETURN', {})
        if not ret:
            self.set_invalid(vt, 'No command was run')
            return
        if not filematch or not dirmatch:
            self.set_invalid(
                vt, 'No filematch and/or dirmatch defined for this section')
            return
        matchfound = search_dir(dirmatch, filematch)
        if matchfound:
            self.set_valid(
                vt, 'File matches found for {}/{}: {}'.format(
                    dirmatch, filematch, matchfound))
        else:
            self.set_invalid(
                vt, 'No file matches found for {}/{}'.format(
                    dirmatch, filematch))

    def val_test_nofilematch(self, sectname, vt):
        s = self.t[sectname]
        sect = s['SECTION']
        filematch = sect.get('filematch', '')
        dirmatch = sect.get('dirmatch', '')
        vt = s['VALRESULTS'][vt]
        ret = s.get('RETURN', {})
        if not ret:
            self.set_invalid(vt, 'No command was run')
            return
        if not filematch or not dirmatch:
            self.set_invalid(
                vt, 'No filematch and/or dirmatch defined for this section')
            return
        matchfound = search_dir(dirmatch, filematch)
        if matchfound:
            self.set_invalid(
                vt, 'File matches found for {}/{}: {}'.format(
                    dirmatch, filematch, matchfound))
        else:
            self.set_valid(
                vt, 'No file matches found for {}/{}'.format(
                    dirmatch, filematch))

    def set_invalid(self, vt, msg):
        parent_func = inspect.stack()[1][3]
        vt['valid'] = False
        vt['msgs'].append(msg)
        logging.warn((
            "\t{} result: **INVALID**: {}"
        ).format(parent_func, msg))

    def set_valid(self, vt, msg):
        parent_func = inspect.stack()[1][3]
        if vt['valid'] is None:
            vt['valid'] = True
        vt['msgs'].append(msg)
        logging.info((
            "\t{} result: VALID: {}"
        ).format(parent_func, msg))

    def create_md(self):
        if not self.t:
            m = (
                "No sections found in: {}, unable to generate a report!"
            ).format(self.filename)
            raise Exception(m)

        self.md_addmh()
        self.md_addtoc()

        for sectname, sectdict in self.t.iteritems():
            self.md_addsecth(sectname, sectdict)
            self.md_addnotes(sectname, sectdict)
            self.md_addcontent(sectname, sectdict)
            self.md_addsectcmd(sectname, sectdict)
            self.md_addsectout(sectname, sectdict)
            self.md_addsectafter(sectname, sectdict)
            self.md_addvalout(sectname, sectdict)
            self.md_addtoclink()
        self.md_addgen()
        self.mdtext = '\n'.join(self.md)

    def md_addmh(self):
        '''add main header'''
        mh = self.conf.get(self.MH, self.MHDEF)
        if not mh:
            return
        m = (
            "{}\n===========================\n"
        ).format(mh)
        self.md.append(m)

    def md_addtoc(self):
        tocbool = self.conf.get(self.TOCBOOL, self.TOCBOOLDEF)
        if not tocbool:
            return
        m = (
            "---------------------------\n"
            "<a name='toc'>Table of contents:</a>\n"
        )
        self.md.append(m)
        for sectname in self.sections:
            if sectname == self.C_SECT:
                continue
            s = self.t[sectname]
            aref = sectname.lower().replace(' ', '-')
            depth = s['SECTION'].get(self.DEPTH, self.DEPTHDEF)
            depth = "  " * int(depth)
            m = (
                "{}* [{}](#user-content-{})"
            ).format(depth, sectname, aref)
            self.md.append(m)
        m = (
            "\n---------------------------\n"
        )
        self.md.append(m)

    def md_addtoclink(self):
        tocbool = self.conf.get(self.TOCBOOL, self.TOCBOOLDEF)
        if not tocbool:
            return
        m = (
            "\n\n[TOC](#user-content-toc)\n\n"
        )
        self.md.append(m)

    def md_addgen(self):
        ci = self.conf.get(self.CI, self.CIDEF)
        utctime = time.strftime("%c %Z")
        if ci:
            ci = "Contact info: **{}**".format(ci)
        m = (
            "###### generated by: `{} v{}`, date: {}, {}"
        ).format(pname, __version__, utctime, ci)
        self.md.append(m)

    def md_addsecth(self, sectname, sectdict):
        '''add section header'''
        sectconf = sectdict.get('SECTION', {})
        hd = int(sectconf.get(self.DEPTH, self.DEPTHDEF))
        m = (
            "{} {}\n"
        ).format(('#' * hd), sectname)
        self.md.append(m)

    def md_addnotes(self, sectname, sectdict):
        sectconf = sectdict.get('SECTION', {})
        added = False
        for k in sorted(sectconf):
            if not k.startswith(self.NOTES):
                continue
            depth = k.replace(self.NOTES, '')
            depth = len(depth)
            depth = "  " * depth
            v = sectconf[k]
            m = (
                "{}* {}"
            ).format(depth, v)
            self.md.append(m)
            added = True
        if added:
            self.md.append('')

    def md_addcontent(self, sectname, sectdict):
        content = sectdict.get('CONTENT', {})
        if not content:
            logging.debug("No content to output in {}".format(sectname))
            return
        for k, v in content.iteritems():
            fn = v.get('cname', '')
            ftext = v.get('ctext', '')
            ftype = v.get('ctype', '')
            if ftype == 'json':
                try:
                    ftext = json.loads(ftext)
                    ftext = jsonify(ftext)
                except:
                    pass
            if not fn:
                continue
            m = (
                " * Content File: {}\n\n```{}\n{}\n```\n"
            ).format(fn, ftype, ftext)
            self.md.append(m)

    def md_addsectcmd(self, sectname, sectdict):
        sectconf = sectdict.get('SECTION', {})
        cmd = sectconf.get(self.CMD, '')
        if not cmd:
            return
        outtype = self.CMDOUTTYPE
        m = (
            "```{}\n{}\n```\n"
        ).format(outtype, cmd)
        self.md.append(m)

    def md_addsectout(self, sectname, sectdict):
        '''add stderr/stdout for this sections cmd return'''
        if not self.conf.get(self.OUTBOOL, self.OUTBOOLDEF):
            return
        sectconf = sectdict.get('SECTION', {})
        ret = sectdict.get('RETURN', {})
        if not ret:
            return
        stdout = ret.get('stdout').strip()
        stderr = ret.get('stderr').strip()
        outtype = sectconf.get(self.OUTTYPE, '')
        if stdout:
            m = (
                "```{}\n{}\n```\n"
            ).format(outtype, stdout)
            self.md.append(m)
        if stderr:
            m = (
                "```STDERR\n{}\n```\n"
            ).format(stderr)
            self.md.append(m)

    def md_addsectafter(self, sectname, sectdict):
        sectconf = sectdict.get('SECTION', {})
        for k in sorted(sectconf):
            if not k.startswith(self.AFTERFN):
                continue
            fn = sectconf[k]
            contentid = k.replace(self.AFTERFN, '')
            typekey = '{}{}'.format(self.AFTERTYPE, contentid)
            ctype = sectconf.get(typekey, '')
            try:
                ctext = load_utf8(fn)
            except:
                ctext = "Failed to load file!"
            if ctype == 'json':
                try:
                    ctext = json.loads(ctext)
                    ctext = jsonify(ctext)
                    logging.debug((
                        "Aftercontent type JSON rendered! {}"
                    ).format(ctext))
                except:
                    logging.debug((
                        "Aftercontent type JSON unable to render! {}"
                    ).format(ctext), exc_info=True)
            logging.debug((
                "Found aftercontent in section {}: filename {}, type {}, "
                "text {}"
            ).format(sectname, fn, ctype, ctext))
            m = (
                " * Post-command contents of: {}\n\n```{}\n{}\n```\n"
            ).format(fn, ctype, ctext)
            self.md.append(m)

    def md_addvalout(self, sectname, sectdict):
        if not self.conf.get(self.VALBOOL, self.VALBOOLDEF):
            return

        vts = sectdict.get('VALRESULTS', {})

        for vt in sorted(vts):
            vtdict = vts[vt]
            valid = vtdict.get('valid', 'UNKNOWN!?')
            msgs = vtdict.get('msgs', [])
            msgs = '\n'.join(msgs)
            m = (
                "  * Validation Test: {}\n"
                "    * Valid: **{}**\n"
                "    * Messages: {}\n"
            ).format(vt, valid, msgs)
            self.md.append(m)

    def gfm_curl(self, data):
        try:
            shell_safe_json = data.decode('utf-8')
            curl_args = [
                'curl',
                '-H',
                'Content-Type: application/json',
                '-d',
                shell_safe_json,
                'https://api.github.com/markdown'
            ]

            if self.github_token:
                curl_args[1:1] = [
                    '-',
                    self.github_token
                ]

            markdown_html = subprocess.Popen(
                curl_args,
                stdout=subprocess.PIPE,
            ).communicate()[0].decode('utf-8')

            return markdown_html
        except subprocess.CalledProcessError:
            logging.error((
                'Unable to convert Markdown to HTML using Github API '
                'urllib and curl both failed!'
            ), exc_info=True)
        return None

    def gfm_urllib(self, markdown_text):
        gfm_html = 'markdown conversion failed'
        logging.debug('Converting markdown to HTML using Github API...')
        data = {
            "text": markdown_text,
            "mode": "markdown"
        }
        data = json.dumps(data).encode('utf-8')

        try:
            headers = {
                'Content-Type': 'application/json'
            }
            if self.github_token:
                headers['Authorization'] = "token %s" % self.github_token
            url = "https://api.github.com/markdown"
            request = Request(url, data, headers)
            gfm_html = urlopen(request).read().decode('utf-8')
        except HTTPError:
            e = sys.exc_info()[1]
            if e.code in [401, 403]:
                logging.error(
                    'Github API auth failed. Please check your OAuth token.')
            else:
                print e.code
                print e
                logging.error('Github API responded in an unfashion way :/')
        except URLError:
            gfm_html = self.gfm_curl(data)
        except:
            logging.error((
                'Github API failed via urllib and curl. '
                'Check for a firewall or add an auth token'
            ), exc_info=True)
        else:
            logging.info('Converted Markdown with github API successfully')
        return gfm_html

    def convert_md(self):
        logging.info("Converting {0.name} to HTML".format(self.fh))
        css = github_css
        title = self.conf.get(self.TITLE, self.TITLEDEF)
        gfm_body = self.gfm_urllib(self.mdtext)
        html = (
            '<!DOCTYPE html>\n'
            '<html><head><meta charset="utf-8">\n'
            '<style>{css}</style>\n'
            '<title>{title}</title>\n'
            '</head><body>\n{body}\n</body></html>'
        ).format(css=css, title=title, body=gfm_body)
        return html

    def mk_dir(self, outdir):
        if not os.path.isdir(outdir):
            os.makedirs(outdir)

    def save_files(self):
        if self.mdtext:
            self.save_file(self.MDEXT, self.mdtext)
        if self.htmltext:
            self.save_file(self.HTMLEXT, self.htmltext)

    def save_file(self, ext, text, basename=None, outdir=None):
        if not outdir:
            outdir = self.conf.get(self.OUTDIR)
        if not basename:
            basename = self.conf.get(self.BASENAME)
        self.mk_dir(outdir)
        filename = "{}.{}".format(basename, ext)
        filename = os.path.join(outdir, filename)
        logging.info("Saving file: {}".format(filename))
        save_utf8(filename, text)


def add_file_log(logfile=None, logdir='/tmp'):
    '''setup file logging'''
    if not logfile:
        parent_func = inspect.stack()[1][3]
        now = get_now()
        logfilename = "%s_%s.log" % (parent_func, now)
        logfile = os.path.join(logdir, logfilename)
    basename = os.path.basename(logfile)
    try:
        [L.removeHandler(x) for x in L.handlers if x.name is basename]
        file_handler = logging.FileHandler(logfile, 'a')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(lfdebug)
        L.addHandler(file_handler)
        logging.info("Logging to: %s" % logfile)
    except:
        logging.error(
            "Problem setting up file logging to %s" % logfile,
            exc_info=True)


def setup_logging(debug=False, logfile=False):
    '''setup console logging'''
    [L.removeHandler(x) for x in L.handlers if x.name is 'console']
    console_handler = logging.StreamHandler(sys.__stdout__)
    console_handler.set_name('console')
    L.setLevel(logging.DEBUG)
    if debug:
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(lfdebug)
    else:
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(lfinfo)
    L.addHandler(console_handler)
    if logfile:
        add_file_log(logfile)


def setup_parser(desc, help=True):
    parser = MyParser(
        description=desc,
        add_help=help,
        formatter_class=CustomFormatter,
    )
    parser.add_argument(
        '-f',
        '--file',
        type=argparse.FileType('r'),
        required=True,
        action='store',
        dest='file',
        help='The doctest definition file',
    )
    parser.add_argument(
        '-a',
        '--auth',
        required=False,
        default='',
        action='store',
        dest='github_token',
        help='Github oauth token (needed if you plan to use the Github API '
        'to convert Markdown to HTML more than 60 times an hour).',
    )
    parser.add_argument(
        '-o',
        '--outdir',
        required=False,
        action='store',
        default='/tmp/{}'.format(get_now()),
        dest='outdir',
        help='The output directory for the Markdown and HTML files',
    )
    parser.add_argument(
        '-l',
        '--log',
        required=False,
        default=False,
        dest='logfile',
        const=fn_gen("log"),
        nargs='?',
        help='Save the log to a file (if no file supplied, will be saved '
        'to $date.$prog.log)',
    )
    parser.add_argument(
        '-s',
        '--skipconvert',
        required=False,
        action='store_true',
        default=False,
        dest='skipconvert',
        help='Skip Converting the Markdown to GFM (which needs access to '
        'https://api.github.com )',
    )
    parser.add_argument(
        '-c',
        '--convertonly',
        required=False,
        action='store_true',
        default=False,
        dest='convertonly',
        help='Just convert a markdown file in -f to HTML using github',
    )
    parser.add_argument(
        '-t',
        '--title',
        required=False,
        action='store',
        default='',
        dest='title',
        help='Title of HTML document',
    )
    parser.add_argument(
        '-v',
        '--verbose',
        required=False,
        action='count',
        dest='verbose',
        help='Increase console output verbosity',
    )
    return parser


F = logging.Formatter
lfdebug = F(
    '[%(lineno)-5d - %(filename)20s:%(funcName)25s()] %(asctime)s\n'
    '%(levelname)-8s %(message)s'
)
lfinfo = F('%(levelname)-8s %(message)s')
L = logging.getLogger()

if __name__ == "__main__":
    parser = setup_parser(__doc__)
    args = parser.parse_args()

    DEBUGMODE = False
    if args.verbose >= 1:
        DEBUGMODE = True

    if args.logfile not in [True, False, None]:
        args.logfile = pathfix(args.logfile)
        if os.path.isdir(args.logfile):
            args.logfile = os.path.join(args.logfile, fn_gen("log"))

    setup_logging(debug=DEBUGMODE, logfile=args.logfile)

    mdtest_args = {}
    mdtest_args['filehandle'] = args.file
    mdtest_args['convertonly'] = args.convertonly
    mdtest_args['skipconvert'] = args.skipconvert
    mdtest_args['github_token'] = args.github_token
    if args.outdir:
        mdtest_args['outdir'] = args.outdir
    if args.title:
        mdtest_args['title'] = args.title

    mdtest = MDTest(**mdtest_args)

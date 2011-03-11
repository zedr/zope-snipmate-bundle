#!/usr/bin/python

'''
File: tm2snip.py
Description: Converts TextMate style snippets to Vim snipMate snippets.
URL: http://github.com/zedr

'''

__author__ = "zedr <zedr@zedr.com>"
__version__ = "1.0"

import os
import sys
import codecs
from datetime import datetime

from xml.dom import minidom
from xml.parsers.expat import ExpatError

class SnipWriter(object):
    """SnipWriter Class
    """

    def __init__(self, domain='zope'):
        self.data = {}
        self.domain = domain

    def read_dir(self, path):
        """ Read .tmSnippet files from a directory,
        and store the parsed content.

        """
        suffix = '.tmSnippet' # Standard TextMate snipper suffix
        try:
            flist = [f for f in os.listdir(path) if f.endswith(suffix)]
        except OSError as e:
            sys.stderr.write(
                "FAIL: Could not open directory '%s'. Aborting... \n" % path
            )
            return
        if not flist:
            sys.stdout.write(
                "WARN: No TextMate snippets found in directory '%s'. \n" % path
            )
            return
        n_valid = 0
        for f in flist:
            fpath = os.sep.join((path, f))
            n_valid += self.read(fpath) 
        sys.stdout.write(
            "\n" + 
            "INFO: Read %d snippets out of %d files and found %d namespaces. \n" % (
                n_valid, len(flist), len(self.data.keys())
            )
        )

    def read(self, path):
        """ Parse a single file and store the extracted data in a dict.
        """
        d = self._parse_file(path)
        if not d:
            return 0
        # The 'uuid' item is unused, so remove it.
        del(d['uuid'])
        # Canonicalize the scope name and derive a namespace, so we can
        # use it as a filename and also lower the number of files to create.
        d['scope'] = scope = d['scope'].replace("\n",".")
        nspace = "-".join(scope.split('.')[1:3])
        nspace = "-".join((nspace, self.domain))
        if nspace in self.data.keys():
            self.data[nspace].append(d)
        else:
            self.data[nspace] = [d,]
        return 1

    def write(self, path):
        """ Write the parsed data to a series of snipMate style snippet files.
        """
        if not self.data:
            sys.stdout.write(
                "INFO: No data loaded. Read some files first. \n"
            )
            return
        d = self.data
        n_wrote = 0
        suffix = '.snippets'
        now = datetime.now()
        prg_name = sys.argv[0]
        banner_str = "# Created by %s @ %s\n\n" % (prg_name, now)
        for k in d.keys():
            fname = "".join((k, suffix))
            fpath = os.sep.join((path, fname))
            fd = codecs.open(fpath, 'w', encoding='utf-8')
            header_str = (
                "# %s snippets for snipMate.\n" % k +
                banner_str
            )
            fd.write(header_str)
            for s in d[k]:
                try:
                    name = "".join(s['name'].split(' ')[1:])
                except:
                    name = s['name']
                cont = s['content'].replace("\n", "\n\t")
                trig = s['tabTrigger']
                snip_str = (
                    "# %s\n" % name +
                    "snippet %s %s\n" % (trig, name) +
                    "\t%s" % cont +
                    "\n\n"
                )
                fd.write(snip_str)
                n_wrote += 1
            fd.close()
        sys.stdout.write(
            "INFO: Successfully wrote %d snipMate snippet files. \n" % n_wrote
        )

    @staticmethod
    def _parse_file(fpath):
        """ Take an XML dict node and turn it into a Python dict.

        TextMate style snippets are XML files, so they will be parsed
        using xml.minidom.

        This method works only when we have a dict node structured
        in the following way:

            <dict>
                <key>content</key>
                <string>browser.handleErrors = True</string>
                ...
            </dict>

        """
        fname = fpath.split(os.sep)[-1]
        try:
            doc = minidom.parse(fpath)
        except ExpatError:
            sys.stdout.write(
                "WARN: '%s' is not a valid TextMate snippet. " % fname +
                "Skipping... \n"
            )
            return
        key_nodes = doc.getElementsByTagName('key')
        str_nodes = doc.getElementsByTagName('string')
        if not (key_nodes and str_nodes):
            sys.stdout.write(
                "WARN: '%s' has invalid snippet information. \n" % fname +
                "Skipping... \n"
            )
            return
        elif not (len(key_nodes) == len(str_nodes)):
            sys.stdout.write(
                "WARN: '%s' is missing some snippet information. " % fname +
                "Skipping... \n"
            )
            return
        ks = [(
            kn.firstChild.data, sn.firstChild.data
        ) for kn, sn in zip(
            key_nodes, str_nodes
        )]
        d = dict(ks)
        required_keys = ('content', 'name', 'scope', 'tabTrigger') 
        for rk in required_keys:
            if rk not in d.keys():
                sys.stdout.write(
                    "WARN: Required key '%s' is missing " % rk + 
                    "in snippet '%s'. " % fname +
                    "Skipping... \n"
                )
                return
        return d

def main():
    """ Main.
    """
    if len(sys.argv) < 3:
        usage()
        sys.exit(0)
    source_dir= sys.argv[1]
    target_dir = sys.argv[2]
    sw = SnipWriter()
    sw.read_dir(source_dir)
    sw.write(target_dir)

def usage():
    """ Print usage.
    """
    msg = (
        "tm2snip.py - Convert TextMate snippets to Vim's snipMate. \n\n"
        "Usage: ./tm2snip.py <TextMate snippets source dir> "
        "<target dir> \n"
    )
    sys.stdout.write(msg)

if __name__ == '__main__':
    """ Run the script.
    """
    main()
    sys.exit(0)

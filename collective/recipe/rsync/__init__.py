# -*- coding: utf-8 -*-
"""Recipe rsync"""

import logging
import sys
import subprocess
from pkg_resources import working_set
from sys import executable
from zc.buildout.easy_install import scripts as create_script


LINE = ('-----------------------------------' +
        '-----------------------------------')
LOG = logging.getLogger("rsync")
OPTIONS = '-av --partial --progress'


def rsync(source=None, target=None, port=None):
    if port:
        cmd = ['rsync', '-e', 'ssh -p %s' % port, '-av', '--partial',
            '--progress', source, target]
    else:
        cmd = ['rsync', '-av', '--partial', '--progress', source, target]
    LOG.info(LINE)
    LOG.info('Running rsync with command: ')
    LOG.info('  $ %s' % ' '.join(cmd))
    LOG.info('  Note: depending on the source file(s) size and location, this may take a while!')
    LOG.info(LINE)
    subprocess.call(cmd)
    LOG.info('Done.')


class Recipe(object):
    """zc.buildout recipe"""

    def __init__(self, buildout, name, options):
        self.buildout, self.name, self.options = buildout, name, options
        self.source = options['source']
        self.target = options['target']
        self.port = None
        self.script = False
        if 'port' in options:
            self.port = options['port']
        if 'script' in options:
            if options['script'] == 'true':
                self.script = True

    def install(self):
        """Installer"""
        if self.script:
            bindir = self.buildout['buildout']['bin-directory']
            arguments = "source='%s', target='%s', port=%s"
            create_script(
                [('%s' % self.name, 'collective.recipe.rsync.__init__', 'rsync')],
                working_set, executable, bindir, arguments=arguments % (
                self.source, self.target, self.port))
            return tuple((bindir + '/' + 'rsync',))
        else:
            # if we make it this far, script option is not set so we execute
            # as buildout runs
            rsync(source=self.source, target=self.target, port=self.port)
            return tuple()

    def update(self):
        """Updater"""
        self.install()

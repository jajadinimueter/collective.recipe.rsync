# -*- coding: utf-8 -*-
"""Recipe rsync"""

import logging
import sys
import subprocess
from pkg_resources import working_set
from sys import executable
from zc.buildout.easy_install import scripts as create_script

_LOG = logging.getLogger("rsync")
line = ('-----------------------------------' +
        '-----------------------------------')


def rsync(source=None, target=None, port=None, args=None):
    if not source:
        _LOG.error('No `source` option specified. Add source = /path/to/source')
        return

    if not target:
        _LOG.error('No `target` option specified. Add target = remotehost:/path/to/target/')
        return

    args = args or []

    cmd = ['rsync', '-av', '--partial', '--progress']

    # add custom args
    cmd.extend(args)

    if port:
        cmd.extend(['-e', 'ssh -p %s' % port])

    cmd.extend([source, target])

    _LOG.info(line)
    _LOG.info('Running rsync with command: ')
    _LOG.info('  $ %s' % ' '.join(cmd))
    _LOG.info('  Note: depending on the source file(s) size and location, this may take a while!')
    _LOG.info(line)
    subprocess.call(cmd)
    _LOG.info('Done.')


class Recipe(object):
    """zc.buildout recipe"""

    def __init__(self, buildout, name, options):
        self.buildout, self.name, self.options = buildout, name, options
        self.source = options.get('source')
        self.target = options.get('target')
        self.port = None
        self.script = False
        self.args = []
        if 'port' in options:
            self.port = options['port']
        if 'script' in options:
            if options['script'] == 'true':
                self.script = True
        args = self.options.get('args')
        if args:
            self.args = [p.strip() for p in args.split(' ')
                         if p.strip()]

    def install(self):
        """Installer"""

        if self.script:
            bindir = self.buildout['buildout']['bin-directory']
            arguments = "source=%s, target=%s, port=%s, args=[%s]"
            arguments = arguments % (
                _format_arg_string(self.source),
                _format_arg_string(self.target),
                self.port,
                ','.join(["'%s'" % a for a in self.args]))

            create_script([('%s' % self.name, 'collective.recipe.rsync.__init__', 'rsync')],
                          working_set, executable, bindir, arguments=arguments)

            return tuple((bindir + '/' + 'rsync',))
        else:
            # if we make it this far, script option is not set so we execute
            # as buildout runs
            rsync(source=self.source, target=self.target, port=self.port)
            return tuple()

    def update(self):
        """Updater"""
        self.install()


def _format_arg_string(s):
    if not s:
        return 'None'
    else:
        return "'%s'" % s


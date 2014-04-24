# -*- coding: utf-8 -*-
import logging
import subprocess
from pkg_resources import working_set
from sys import executable
from zc.buildout.easy_install import scripts as create_script


CMD = 'rsync'
LINE = '-' * 80
LOG = logging.getLogger('rsync')
OPTIONS = '-a --partial --progress'


def rsync(exclude=None, port=None, rsync_options=None, source=None, target=None,
          verbose=False):
    """
    Parse options, build and run command
    """

    if not source:
        LOG.error('No `source` option specified. Add source = /path/to/source')
        return

    if not target:
        LOG.error('No `target` option specified. Add target = remotehost:/path/to/target/')
        return

    # Parse options
    if rsync_options is None:
        rsync_options = OPTIONS.split()
    else:
        rsync_options = rsync_options.split()

    if verbose:
        rsync_options.append('-v')

    if exclude:
        for e in exclude.split():
            rsync_options += ['--exclude=%s' % e]
    if port:
        rsync_options += ['-e', 'ssh -p %s' % port]

    rsync_options.append(source)
    rsync_options.append(target)

    # Build cmd
    cmd = rsync_options
    cmd.insert(0, CMD)

    LOG.info(LINE)
    LOG.info('Running rsync with command: ')
    LOG.info('  $ %s' % ' '.join(cmd))
    LOG.info(
        'Note: depending on size & location of source file(s),'
        ' this may take a while!'
    )
    LOG.info(LINE)
    subprocess.call(cmd)
    LOG.info('Done.')


def asbool(val):
    if val:
        return val.strip().lower() == 'true'
    return False


def format_arg(val):
    if not val:
        return 'None'
    else:
        return "'%s'" % val


def build_script_args(arguments):
    """
    Build comma separated argument list to pass to
    the :func.`.rsync` function inside a binscript.
    """
    return ','.join('%s=%s' % (k, format_arg(v))
                    for k, v in arguments.items()
                    if v is not None)


class Recipe(object):
    """
    """

    def __init__(self, buildout, name, options):
        """
        Called by buildout when the part is initialized
        """
        bool_args = ['verbose']
        self.buildout, self.name, self.options = buildout, name, options
        arguments = dict(**options)

        # actually just ignores mission source/target options
        ignore_errors = asbool(options.pop('ignore-errors', False))

        # this is set by the user if he wants to create
        # a script inside bin/ named like the part to execute
        # the rsync command
        self.script = asbool(options.pop('script', False))

        if 'args' in arguments:
            arguments['args'] = [arg.strip()
                                 for arg in arguments['args'].split()
                                 if arg.strip()]

        for arg_name in bool_args:
            if arg_name in arguments:
                arguments[arg_name] = asbool(arguments[arg_name])

        if not ignore_errors:
            # trigger validation of source and target
            _ = options['source']
            _ = options['target']

        self.arguments = arguments

    def install(self):
        """
        Called every time the user runs buildout
        """
        if self.script:
            # the user wants us to create a script called like
            # the part the recipe is configured
            bindir = self.buildout['buildout']['bin-directory']
            script_args = build_script_args(self.arguments)

            create_script(
                [('%s' % self.name,
                  'collective.recipe.rsync.__init__', 'rsync')],
                working_set, executable, bindir,
                arguments=script_args)
        else:
            # if we make it this far, script option is not set so we execute
            # as buildout runs
            rsync(**self.arguments)

        return ()

    def update(self):
        """
        Called every time the user runs buildout
        """
        self.install()


# -*- coding: utf-8 -*-
import logging
import subprocess
from pkg_resources import working_set
from sys import executable
from zc.buildout.easy_install import scripts as create_script


try:
    #noinspection PyUnresolvedReferences
    STR_INST = (basestring, )
except:
    STR_INST = (str, )

CMD = 'rsync'
LINE = '-' * 80
LOG = logging.getLogger('rsync')
OPTIONS = '-a --partial'

# declare arguments we like to receive
EXPECTED_ARGS = {'source': None, 'target': None, 'exclude': None,
                 'port':None, 'options': None}
EXPECTED_BOOL_ARGS = {'verbose': False, 'ignore-errors': False,
                      'script': False}
EXPECTED_ARGS.update(EXPECTED_BOOL_ARGS)
EXPECTED_LIST_ARGS = {'args': None}
EXPECTED_ARGS.update(EXPECTED_LIST_ARGS)


def rsync(exclude=None, port=None, options=None, source=None, target=None,
          verbose=False, args=None):
    """
    Actually runs the rsync command with previously parsed options
    """

    # Parse options
    if options is None:
        options = OPTIONS.split()
    else:
        options = options.split()

    if args:
        options.extend(args)

    if verbose:
        options.extend(['-v',  '--progress'])

    if exclude:
        for e in exclude.split():
            options += ['--exclude=%s' % e]
    if port:
        options += ['-e', 'ssh -p %s' % port]

    options.append(source)
    options.append(target)

    # Build cmd
    cmd = options
    cmd.insert(0, CMD)

    if verbose:
        LOG.info(LINE)
        LOG.info('Running rsync with command: ')
        LOG.info('  $ %s' % ' '.join(cmd))
        LOG.info(
            'Note: depending on size & location of source file(s),'
            ' this may take a while!'
        )
        LOG.info(LINE)

    subprocess.call(cmd)

    if verbose:
        LOG.info('Done.')


def asbool(val):
    if val:
        return val.strip().lower() == 'true'
    return False


def format_arg(val):
    if isinstance(val, STR_INST):
        return '"%s"' % val
    return val


def build_script_args(arguments):
    """
    Build comma separated argument list to pass to
    the :func.`.rsync` function inside a binscript.
    """
    return ','.join('%s=%s' % (k, format_arg(v))
                    for k, v in list(arguments.items()))


def convert_arg(k, v):
    v = v or ''
    v = v.strip()
    if not v:
        return EXPECTED_ARGS.get(k)
    elif k in EXPECTED_BOOL_ARGS:
        return asbool(v)
    elif k in EXPECTED_LIST_ARGS:
        return [arg.strip()
                for arg in v.split()
                if arg.strip()]
    elif k in EXPECTED_ARGS:
        return v
    else:
        return None


def include_arg(k):
    return k in EXPECTED_ARGS


class Recipe(object):
    """
    """

    def __init__(self, buildout, name, options):
        """
        Called by buildout when the part is initialized
        """

        self.buildout, self.name, self.options = buildout, name, options

        arguments = dict((k, convert_arg(k, options.get(k))) for k in EXPECTED_ARGS
                         if include_arg(k))

        # actually just ignores mission source/target options
        ignore_errors = arguments.pop('ignore-errors')

        # this is set by the user if he wants to create
        # a script inside bin/ named like the part to execute
        # the rsync command
        self.script = arguments.pop('script')

        if not ignore_errors:
            # trigger validation of source and target
            _ = options['source']
            _ = options['target']

        self.arguments = arguments

    def install(self):
        """
        Called every time the user runs buildout
        """

        # check whether one of source or target is not defined
        # exit with an error message
        if not self.arguments.get('source'):
            LOG.error('Error in part %s: no "source" option specified. '
                      'Add source = /path/to/source' % self.name)
            return

        if not self.arguments.get('target'):
            LOG.error('Error in part %s: no "target" option specified. '
                      'Add target = remotehost:/path/to/target/' % self.name)
            return

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


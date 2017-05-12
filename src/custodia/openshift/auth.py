# Copyright (C) 2017  Custodia Project Contributors - see LICENSE file
from __future__ import absolute_import

from custodia import log
from custodia.plugin import HTTPAuthenticator, PluginOption


DOCKER_REGEX = r'/docker-([0-9a-f]{64})\.scope'
# 'rkt-$uuid'.replace('-', r'\x{:x}'.format(ord('-')))
RKT_REGEX = (
    r'/machine-rkt\\x2d([0-9a-f]{8})\\x2d([0-9a-f]{4})\\x2d([0-9a-f]{4})'
    r'\\x2d([0-9a-f]{4})\\x2d([0-9a-f]{12})\.scope')

log.warn_provisional(__name__)


class ContainerAuth(HTTPAuthenticator):
    matchers = PluginOption('str_list', ['docker', 'rkt'], None)
    docker_regex = PluginOption('regex', DOCKER_REGEX, None)
    rkt_regex = PluginOption('regex', RKT_REGEX, None)

    def _read_cgroup(self, pid):
        with open('/proc/{:d}/cgroup'.format(pid)) as f:
            return list(f)

    def _match_docker(self, lines):
        for line in lines:
            # pylint: disable=no-member
            mo = self.docker_regex.search(line)
            if mo is not None:
                return mo.group(1)
        return None, None

    def _match_rkt(self, lines):
        for line in lines:
            # pylint: disable=no-member
            mo = self.docker_regex.search(line)
            if mo is not None:
                return '-'.join(mo.groups())

    def handle(self, request):
        creds = request.get('creds')
        if creds is None:
            self.logger.debug('Missing "creds" on request')
            return None

        pid = int(creds['pid'])
        try:
            lines = self._read_cgroup(pid)
        except OSError:
            self.logger.exception("Failed to read cgroup for pid %i", pid)
            return None

        for matcher in self.matchers:  # pylint: disable=not-an-iterable
            func = getattr(self, '_match_{}'.format(matcher))
            result = func(lines)
            if result is not None:
                creds['container'] = (matcher, result)
                self.logger.info(
                    "Detected %s://%s for pid %i", matcher, result, pid)
                return True

        return False

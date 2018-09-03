# Copyright (C) 2017  Custodia Project Contributors - see LICENSE file
from __future__ import absolute_import

import warnings

from custodia import log
from custodia.plugin import HTTPAuthorizer, PluginOption
from custodia.plugin import INHERIT_GLOBAL, REQUIRED

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

log.warn_provisional(__name__)

warnings.filterwarnings("ignore", category=InsecureRequestWarning)


class OpenShiftHostnameAuthz(HTTPAuthorizer):
    """

    https://github.com/openshift/origin/blob/master/docs/cluster_up_down.md

    $ oc project
    test
    $ oc create serviceaccount custodia
    $ oc policy add-role-to-user view system:serviceaccount:test:custodia
    $ oc describe serviceaccount custodia
    ...
    Mountable secrets:      custodia-token-...
    ...
    $ oc describe secret custodia-token-...
    """
    oc_uri = PluginOption(str, REQUIRED, None)
    token = PluginOption(str, REQUIRED, None)
    project = PluginOption(str, REQUIRED, None)
    tls_verify = PluginOption(bool, True, None)
    tls_cafile = PluginOption(str, INHERIT_GLOBAL(None), 'Path to CA file')
    hostname_annotation = PluginOption(
        str,
        "latchset.github.io/custodia.hostname",
        None
    )

    def __init__(self, config, section=None):
        super(OpenShiftHostnameAuthz, self).__init__(config, section)
        self.session = None
        self.oc_uri = self.oc_uri.rstrip('/')

    def finalize_init(self, config, cfgparser, context=None):
        super(OpenShiftHostnameAuthz, self).finalize_init(
            config, cfgparser, context)
        self.session = requests.Session()
        self.session.headers["Authorization"] = "Bearer {}".format(self.token)
        if self.tls_cafile is not None:
            self.session.verify = self.tls_cafile
        else:
            self.session.verify = self.tls_verify

    def get_pods(self):
        url = "{0.oc_uri}/api/v1/namespaces/{0.project}/pods".format(self)
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def find_pod(self, data, containerid):
        for pod in data['items']:
            for status in pod[u'status'][u'containerStatuses']:
                if u'containerID' in status and status[u'containerID'] == containerid:
                    return pod

    def handle(self, request):
        creds = request.get('creds')
        if creds is None:
            self.logger.debug('Missing "creds" on request')
            return None

        container = creds.get('container')
        if not container:
            self.logger.debug('Missing "container" on request')
            return None
        containerid = "{}://{}".format(*container)
        pods = self.get_pods()
        pod = self.find_pod(pods, containerid)
        if pod is None:
            self.logger.error('No pod for container %s found',
                              containerid)
            self.audit_svc_access(log.AUDIT_SVC_AUTHZ_FAIL,
                                  request['client_id'], request['path'])
            return False
        metadata = pod[u'metadata']
        self.logger.info(
            "Found pod %s for %s", metadata[u'selfLink'], containerid
        )
        hostname = metadata[u'annotations'].get(self.hostname_annotation)
        if not hostname:
            self.logger.error("No hostname configured for %s",
                              metadata[u'selfLink'])
            self.audit_svc_access(log.AUDIT_SVC_AUTHZ_FAIL,
                                  request['client_id'], request['path'])
            return False
        if hostname != request['path_chain'][-1]:
            self.logger.error(
                "Path %s does not match hostname '%s' for %s",
                request['path_chain'], hostname, containerid
            )
            self.audit_svc_access(log.AUDIT_SVC_AUTHZ_FAIL,
                                  request['client_id'], request['path'])
            return False

        self.logger.debug(
            "Container %s matches %s: '%s'",
            metadata[u'selfLink'], self.hostname_annotation, hostname
        )
        self.audit_svc_access(log.AUDIT_SVC_AUTHZ_PASS,
                              request['client_id'], request['path'])

        return True

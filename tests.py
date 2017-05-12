# pylint: disable=redefined-outer-name
from __future__ import absolute_import

from custodia.compat import configparser

from custodia.openshift.auth import ContainerAuth
from custodia.openshift.authz import OpenShiftHostnameAuthz

import pkg_resources

import pytest


CONFIG = u"""
[auth:container]
handler = ContainerAuth

[authz:openshift]
handler = OpenShiftHostnameAuthz
oc_uri = https://localhost:8443
token = bearertoken
project = test
tls_verify = False
"""


@pytest.fixture
def parser():
    parser = configparser.ConfigParser(
        interpolation=configparser.ExtendedInterpolation(),
    )
    parser.read_string(CONFIG)
    return parser


@pytest.fixture
def containerauth(parser):
    return ContainerAuth(parser, 'auth:container')


@pytest.fixture
def osauthz(parser):
    return OpenShiftHostnameAuthz(parser, 'authz:openshift')


def test_auth_ok(containerauth):
    pass


def test_authz_ok(osauthz):
    pass


@pytest.mark.parametrize('group,name,cls', [
    ('custodia.authenticators', 'ContainerAuth', ContainerAuth),
    ('custodia.authorizers', 'OpenShiftHostnameAuthz', OpenShiftHostnameAuthz),
])
def test_plugins(group, name, cls, dist='custodia.openshift'):
    ep = pkg_resources.get_entry_info(dist, group, name)
    assert ep.dist.project_name == dist
    assert ep.resolve() is cls

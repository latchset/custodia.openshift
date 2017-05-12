# OpenShift and Container plugins for Custodia

## ContainerAuth

Map PID to container engine and container id

## OpenShiftHostnameAuthz

Authorize hostname against OpenShift API for IPACertRequest

## Configuration

Set up a local system according to https://github.com/openshift/origin/blob/master/docs/cluster_up_down.md

1. Create OC project *test*

2. Create custodia service account and grant *view* permission

```
$ oc project
test
$ oc create serviceaccount custodia
$ oc policy add-role-to-user view system:serviceaccount:test:custodia
```

3. Get authentication token for service account

```
$ oc describe serviceaccount custodia
Name:           custodia
Namespace:      test
Labels:         <none>

Image pull secrets:     custodia-dockercfg-9w57j

Mountable secrets:      custodia-token-zrz9g
                        custodia-dockercfg-9w57j

Tokens:                 custodia-token-z6j23
                        custodia-token-zrz9g

$ oc describe secret custodia-token-zrz9g
Name:           custodia-token-zrz9g
Namespace:      test
Labels:         <none>
Annotations:    kubernetes.io/service-account.name=custodia
                kubernetes.io/service-account.uid=dccff988-36ff-11e7-8735-54ee7547ca7b

Type:   kubernetes.io/service-account-token

Data
====
ca.crt:         1070 bytes
namespace:      4 bytes
service-ca.crt: 2186 bytes
token:          eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

4. Configure plugins

```
[auth:container]
handler = ContainerAuth

[authz:openshift]
handler = OpenShiftHostnameAuthz
oc_uri = https://localhost:8443
token = eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
project = test
tls_verify = false
```

5. Bind-mount socket into container

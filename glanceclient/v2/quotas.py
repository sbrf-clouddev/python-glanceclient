# Copyright 2017 Sberbank
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from oslo_utils import units
import six


def _get_convertion_rate(n):
    if n in ('total_images_size', 'total_snapshots_size'):
        return units.G
    else:
        return 1


def convert_to_gb(q):
    for n, v in six.iteritems(q):
        if _get_convertion_rate(n) != 1 and v > 0:
            q[n] = int(float(v) / _get_convertion_rate(n))
    return q


def convert_from_gb(q):
    for k, v in six.iteritems(q):
        if v > -1:
            q[k] = int(float(v) * _get_convertion_rate(k))
        else:
            q[k] = v
    return q


class QuotaController(object):
    def __init__(self, http_client, version=2):
        self.http_client = http_client
        self.version = "v%s" % str(version)

    def set_quota_classes(self, quota_classes):
        """Updates quota classes

        :param quota_classes dict of quota classes that needs to be updated.
        :return updated quota classes
        """
        url = '/%s/quota_classes' % self.version
        body = {'quota_classes': convert_from_gb(quota_classes)}
        resp, upd_classes = self.http_client.put(url, data=body)
        return convert_to_gb(upd_classes['quota_classes'])

    def get_quota_classes(self):
        url = '/%s/quota_classes' % self.version
        resp, body = self.http_client.get(url)
        return convert_to_gb(body['quota_classes'])

    def set_quotas(self, scope, quotas):
        """Updates quotas

        :param quotas dict of quotas that needs to be updated.
        :return updated quotas
        """
        url = '/%(version)s/quotas/%(scope)s' % {
            'version': self.version,
            'scope': scope}
        body = {'quotas': convert_from_gb(quotas)}
        resp, upd_quotas = self.http_client.put(url, data=body)
        return convert_to_gb(upd_quotas['quotas'])

    def get_quotas(self, scope):
        url = '/%(version)s/quotas/%(scope)s' % {
            'version': self.version,
            'scope': scope}
        resp, quotas = self.http_client.get(url)
        return convert_to_gb(quotas['quotas'])

    def reset_quotas(self, scope):
        """Reset quotas to default values

        :param scope: project of domain where quota must be applied
        """
        url = '/%(version)s/quotas/%(scope)s' % {
            'version': self.version,
            'scope': scope}
        self.http_client.delete(url)

    def get_usage(self, scope):
        """Get usage for project quotas

        :param scope: project_id
        :return: dict with quota usage
        """
        url = '/%(version)s/quotas/%(scope)s/usage' % {
            'version': self.version,
            'scope': scope}
        resp, data = self.http_client.get(url)
        usage = data['usage']
        for n in usage:
            usage[n]['limit'] = usage[n]['limit'] // _get_convertion_rate(n)
            if n.endswith("_size"):
                v = float(usage[n]['usage']) / _get_convertion_rate(n)
                usage[n]['usage'] = int(v)
        return usage

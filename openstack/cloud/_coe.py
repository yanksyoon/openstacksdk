# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# import types so that we can reference ListType in sphinx param declarations.
# We can't just use list, because sphinx gets confused by
# openstack.resource.Resource.list and openstack.resource2.Resource.list
import types  # noqa

from openstack.cloud import _utils
from openstack.cloud import exc


class CoeCloudMixin:

    @property
    def _container_infra_client(self):
        if 'container-infra' not in self._raw_clients:
            self._raw_clients['container-infra'] = self._get_raw_client(
                'container-infra')
        return self._raw_clients['container-infra']

    @_utils.cache_on_arguments()
    def list_coe_clusters(self):
        """List COE (Container Orchestration Engine) cluster.

        :returns: A list of container infrastructure management ``Cluster``
            objects.
        :raises: ``OpenStackCloudException``: if something goes wrong during
            the OpenStack API call.
        """
        return list(self.container_infrastructure_management.clusters())

    def search_coe_clusters(self, name_or_id=None, filters=None):
        """Search COE cluster.

        :param name_or_id: cluster name or ID.
        :param filters: a dict containing additional filters to use.
        :param detail: a boolean to control if we need summarized or
            detailed output.

        :returns: A list of container infrastructure management ``Cluster``
            objects.
        :raises: ``OpenStackCloudException``: if something goes wrong during
            the OpenStack API call.
        """
        coe_clusters = self.list_coe_clusters()
        return _utils._filter_list(coe_clusters, name_or_id, filters)

    def get_coe_cluster(self, name_or_id, filters=None):
        """Get a COE cluster by name or ID.

        :param name_or_id: Name or ID of the cluster.
        :param filters:
            A dictionary of meta data to use for further filtering. Elements
            of this dictionary may, themselves, be dictionaries. Example::

                {
                    'last_name': 'Smith',
                    'other': {
                        'gender': 'Female'
                    }
                }

            OR
            A string containing a jmespath expression for further filtering.
            Example:: "[?last_name==`Smith`] | [?other.gender]==`Female`]"

        :returns: A container infrastructure management ``Cluster`` object if
            found, else None.
        """
        return _utils._get_entity(self, 'coe_cluster', name_or_id, filters)

    def create_coe_cluster(
        self, name, cluster_template_id, **kwargs,
    ):
        """Create a COE cluster based on given cluster template.

        :param string name: Name of the cluster.
        :param string cluster_template_id: ID of the cluster template to use.
        :param dict kwargs: Any other arguments to pass in.

        :returns: a dict containing the cluster description
        :returns: The created container infrastructure management ``Cluster``
            object.
        :raises: ``OpenStackCloudException`` if something goes wrong during
            the OpenStack API call
        """
        cluster = self.container_infrastructure_management.create_cluster(
            name=name,
            cluster_template_id=cluster_template_id,
            **kwargs,
        )

        self.list_coe_clusters.invalidate(self)
        return cluster

    def delete_coe_cluster(self, name_or_id):
        """Delete a COE cluster.

        :param name_or_id: Name or unique ID of the cluster.
        :returns: True if the delete succeeded, False if the
            cluster was not found.

        :raises: OpenStackCloudException on operation error.
        """

        cluster = self.get_coe_cluster(name_or_id)

        if not cluster:
            self.log.debug(
                "COE Cluster %(name_or_id)s does not exist",
                {'name_or_id': name_or_id},
                exc_info=True,
            )
            return False

        self.container_infrastructure_management.delete_cluster(cluster)
        self.list_coe_clusters.invalidate(self)
        return True

    def update_coe_cluster(self, name_or_id, **kwargs):
        """Update a COE cluster.

        :param name_or_id: Name or ID of the COE cluster being updated.
        :param kwargs: Cluster attributes to be updated.

        :returns: The updated cluster ``Cluster`` object.

        :raises: OpenStackCloudException on operation error.
        """
        self.list_coe_clusters.invalidate(self)
        cluster = self.get_coe_cluster(name_or_id)
        if not cluster:
            raise exc.OpenStackCloudException(
                "COE cluster %s not found." % name_or_id)

        cluster = self.container_infrastructure_management.update_cluster(
            cluster,
            **kwargs
        )

        return cluster

    def get_coe_cluster_certificate(self, cluster_id):
        """Get details about the CA certificate for a cluster by name or ID.

        :param cluster_id: ID of the cluster.

        :returns: Details about the CA certificate for the given cluster.
        """
        msg = ("Error fetching CA cert for the cluster {cluster_id}".format(
               cluster_id=cluster_id))
        url = "/certificates/{cluster_id}".format(cluster_id=cluster_id)
        data = self._container_infra_client.get(url,
                                                error_message=msg)

        return self._get_and_munchify(key=None, data=data)

    def sign_coe_cluster_certificate(self, cluster_id, csr):
        """Sign client key and generate the CA certificate for a cluster

        :param cluster_id: UUID of the cluster.
        :param csr: Certificate Signing Request (CSR) for authenticating
            client key.The CSR will be used by Magnum to generate a signed
            certificate that client will use to communicate with the cluster.

        :returns: a dict representing the signed certs.

        :raises: OpenStackCloudException on operation error.
        """
        error_message = ("Error signing certs for cluster"
                         " {cluster_id}".format(cluster_id=cluster_id))
        with _utils.shade_exceptions(error_message):
            body = {}
            body['cluster_uuid'] = cluster_id
            body['csr'] = csr

            certs = self._container_infra_client.post(
                '/certificates', json=body)

        return self._get_and_munchify(key=None, data=certs)

    @_utils.cache_on_arguments()
    def list_cluster_templates(self, detail=False):
        """List cluster templates.

        :param bool detail. Ignored. Included for backwards compat.
            ClusterTemplates are always returned with full details.

        :returns: a list of dicts containing the cluster template details.

        :raises: ``OpenStackCloudException``: if something goes wrong during
            the OpenStack API call.
        """
        return list(
            self.container_infrastructure_management.cluster_templates())

    def search_cluster_templates(
            self, name_or_id=None, filters=None, detail=False):
        """Search cluster templates.

        :param name_or_id: cluster template name or ID.
        :param filters: a dict containing additional filters to use.
        :param detail: a boolean to control if we need summarized or
            detailed output.

        :returns: a list of dict containing the cluster templates

        :raises: ``OpenStackCloudException``: if something goes wrong during
            the OpenStack API call.
        """
        cluster_templates = self.list_cluster_templates(detail=detail)
        return _utils._filter_list(
            cluster_templates, name_or_id, filters)

    def get_cluster_template(self, name_or_id, filters=None, detail=False):
        """Get a cluster template by name or ID.

        :param name_or_id: Name or ID of the cluster template.
        :param filters:
            A dictionary of meta data to use for further filtering. Elements
            of this dictionary may, themselves, be dictionaries. Example::

                {
                    'last_name': 'Smith',
                    'other': {
                        'gender': 'Female'
                    }
                }

            OR
            A string containing a jmespath expression for further filtering.
            Example:: "[?last_name==`Smith`] | [?other.gender]==`Female`]"

        :returns: A cluster template dict or None if no matching
            cluster template is found.
        """
        return _utils._get_entity(
            self, 'cluster_template', name_or_id,
            filters=filters, detail=detail)

    def create_cluster_template(
            self, name, image_id=None, keypair_id=None, coe=None, **kwargs):
        """Create a cluster template.

        :param string name: Name of the cluster template.
        :param string image_id: Name or ID of the image to use.
        :param string keypair_id: Name or ID of the keypair to use.
        :param string coe: Name of the coe for the cluster template.
            Other arguments will be passed in kwargs.

        :returns: a dict containing the cluster template description

        :raises: ``OpenStackCloudException`` if something goes wrong during
            the OpenStack API call
        """
        cluster_template = self.container_infrastructure_management \
            .create_cluster_template(
                name=name,
                image_id=image_id,
                keypair_id=keypair_id,
                coe=coe,
                **kwargs,
            )

        return cluster_template

    def delete_cluster_template(self, name_or_id):
        """Delete a cluster template.

        :param name_or_id: Name or unique ID of the cluster template.
        :returns: True if the delete succeeded, False if the
            cluster template was not found.

        :raises: OpenStackCloudException on operation error.
        """

        cluster_template = self.get_cluster_template(name_or_id)

        if not cluster_template:
            self.log.debug(
                "Cluster template %(name_or_id)s does not exist",
                {'name_or_id': name_or_id},
                exc_info=True)
            return False

        self.container_infrastructure_management.delete_cluster_template(
            cluster_template)
        return True

    def update_cluster_template(self, name_or_id, **kwargs):
        """Update a cluster template.

        :param name_or_id: Name or ID of the cluster template being updated.

        :returns: an update cluster template.

        :raises: OpenStackCloudException on operation error.
        """
        cluster_template = self.get_cluster_template(name_or_id)
        if not cluster_template:
            raise exc.OpenStackCloudException(
                "Cluster template %s not found." % name_or_id)

        cluster_template = self.container_infrastructure_management \
            .update_cluster_template(
                cluster_template,
                **kwargs
            )

        return cluster_template

    def list_magnum_services(self):
        """List all Magnum services.
        :returns: a list of dicts containing the service details.

        :raises: OpenStackCloudException on operation error.
        """
        with _utils.shade_exceptions("Error fetching Magnum services list"):
            data = self._container_infra_client.get('/mservices')
            return self._normalize_magnum_services(
                self._get_and_munchify('mservices', data))

    def _normalize_coe_clusters(self, coe_clusters):
        ret = []
        for coe_cluster in coe_clusters:
            ret.append(self._normalize_coe_cluster(coe_cluster))
        return ret

    def _normalize_coe_cluster(self, coe_cluster):
        """Normalize Magnum COE cluster."""

        # Only import munch when really necessary
        import munch

        coe_cluster = coe_cluster.copy()

        # Discard noise
        coe_cluster.pop('links', None)

        c_id = coe_cluster.pop('uuid')

        ret = munch.Munch(
            id=c_id,
            location=self._get_current_location(),
        )

        if not self.strict_mode:
            ret['uuid'] = c_id

        for key in (
                'status',
                'cluster_template_id',
                'stack_id',
                'keypair',
                'master_count',
                'create_timeout',
                'node_count',
                'name'):
            if key in coe_cluster:
                ret[key] = coe_cluster.pop(key)

        ret['properties'] = coe_cluster
        return ret

    def _normalize_cluster_templates(self, cluster_templates):
        ret = []
        for cluster_template in cluster_templates:
            ret.append(self._normalize_cluster_template(cluster_template))
        return ret

    def _normalize_cluster_template(self, cluster_template):
        """Normalize Magnum cluster_templates."""

        import munch

        cluster_template = cluster_template.copy()

        # Discard noise
        cluster_template.pop('links', None)
        cluster_template.pop('human_id', None)
        # model_name is a magnumclient-ism
        cluster_template.pop('model_name', None)

        ct_id = cluster_template.pop('uuid')

        ret = munch.Munch(
            id=ct_id,
            location=self._get_current_location(),
        )
        ret['is_public'] = cluster_template.pop('public')
        ret['is_registry_enabled'] = cluster_template.pop('registry_enabled')
        ret['is_tls_disabled'] = cluster_template.pop('tls_disabled')
        # pop floating_ip_enabled since we want to hide it in a future patch
        fip_enabled = cluster_template.pop('floating_ip_enabled', None)
        if not self.strict_mode:
            ret['uuid'] = ct_id
            if fip_enabled is not None:
                ret['floating_ip_enabled'] = fip_enabled
            ret['public'] = ret['is_public']
            ret['registry_enabled'] = ret['is_registry_enabled']
            ret['tls_disabled'] = ret['is_tls_disabled']

        # Optional keys
        for (key, default) in (
                ('fixed_network', None),
                ('fixed_subnet', None),
                ('http_proxy', None),
                ('https_proxy', None),
                ('labels', {}),
                ('master_flavor_id', None),
                ('no_proxy', None)):
            if key in cluster_template:
                ret[key] = cluster_template.pop(key, default)

        for key in (
                'apiserver_port',
                'cluster_distro',
                'coe',
                'created_at',
                'dns_nameserver',
                'docker_volume_size',
                'external_network_id',
                'flavor_id',
                'image_id',
                'insecure_registry',
                'keypair_id',
                'name',
                'network_driver',
                'server_type',
                'updated_at',
                'volume_driver'):
            ret[key] = cluster_template.pop(key)

        ret['properties'] = cluster_template
        return ret

    def _normalize_magnum_services(self, magnum_services):
        ret = []
        for magnum_service in magnum_services:
            ret.append(self._normalize_magnum_service(magnum_service))
        return ret

    def _normalize_magnum_service(self, magnum_service):
        """Normalize Magnum magnum_services."""
        import munch
        magnum_service = magnum_service.copy()

        # Discard noise
        magnum_service.pop('links', None)
        magnum_service.pop('human_id', None)
        # model_name is a magnumclient-ism
        magnum_service.pop('model_name', None)

        ret = munch.Munch(location=self._get_current_location())

        for key in (
                'binary',
                'created_at',
                'disabled_reason',
                'host',
                'id',
                'report_count',
                'state',
                'updated_at'):
            ret[key] = magnum_service.pop(key)
        ret['properties'] = magnum_service
        return ret

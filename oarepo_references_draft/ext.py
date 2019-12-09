from typing import List

from flask import url_for
from invenio_pidstore.models import PersistentIdentifier
from invenio_records_rest.views import verify_record_permission, RecordResource

from invenio_records_draft.signals import collect_records, check_can_publish, check_can_unpublish, check_can_edit, \
    before_publish_record
from oarepo_references.models import RecordReference
from invenio_records_draft.proxies import current_drafts
from invenio_records_draft.api import CollectAction, RecordContext
from oarepo_references.utils import transform_dicts_in_data


def collect_referenced_records(sender, record: RecordContext = None, action=None):

    if not getattr(record, 'record_url', None):
        # add the external url of the record
        if action == CollectAction.PUBLISH:
            endpoint = find_endpoint_by_pid_type(current_drafts.draft_endpoints,
                                                         record.record_pid.pid_type)
        else:
            endpoint = find_endpoint_by_pid_type(current_drafts.published_endpoints,
                                                         record.record_pid.pid_type)
        view_name = RecordResource.view_name.format(endpoint['endpoint'])
        record.record_url = url_for(view_name, _external=True,
                                    pid_value=record.record_pid.pid_value)

    # add the external published and draft urls of the record
    if action == CollectAction.PUBLISH:
        record.draft_record_url = record.record_url
        endpoint = find_endpoint_by_pid_type(current_drafts.published_endpoints,
                                                     record.record_pid.pid_type)
        view_name = RecordResource.view_name.format(endpoint['endpoint'])
        record.published_record_url = url_for(view_name, _external=True,
                                    pid_value=record.record_pid.pid_value)
    else:
        record.published_record_url = record.record_url

        endpoint = find_endpoint_by_pid_type(current_drafts.draft_endpoints,
                                                     record.record_pid.pid_type)
        view_name = RecordResource.view_name.format(endpoint['endpoint'])
        record.draft_record_url = url_for(view_name, _external=True,
                                    pid_value=record.record_pid.pid_value)

    for ref in RecordReference.query.filter_by(record_uuid=record.record.model.id):
        if not ref.reference_uuid:
            continue
        for pid in PersistentIdentifier.query.filter_by(object_type='rec',
                                                        object_uuid=ref.reference_uuid):
            if (
                (action == CollectAction.PUBLISH and current_drafts.is_draft(pid))
                or current_drafts.is_published(pid)
            ):
                # this pid is the target pid
                yield RecordContext(record=current_drafts.get_record(pid),
                                    record_pid=pid,
                                    record_url=ref.reference)
                break


def find_endpoint_by_pid_type(endpoints, pid_type):
    for endpoint in endpoints.values():
        if endpoint['pid_type'] == pid_type:
            return endpoint
    raise KeyError('Endpoint for pid type %s not found' % pid_type)


def check_can_publish_callback(sender, record: RecordContext = None):
    endpoint = find_endpoint_by_pid_type(current_drafts.draft_endpoints, record.record_pid.pid_type)
    permission_factory = endpoint['publish_permission_factory']
    if permission_factory:
        verify_record_permission(permission_factory, record.record)


def check_can_unpublish_callback(sender, record: RecordContext = None):
    endpoint = find_endpoint_by_pid_type(current_drafts.published_endpoints, record.record_pid.pid_type)
    permission_factory = endpoint['unpublish_permission_factory']
    if permission_factory:
        verify_record_permission(permission_factory, record.record)


def check_can_edit_callback(sender, record: RecordContext = None):
    endpoint = find_endpoint_by_pid_type(current_drafts.published_endpoints, record.record_pid.pid_type)
    permission_factory = endpoint['edit_permission_factory']
    if permission_factory:
        verify_record_permission(permission_factory, record.record)


def before_publish_record_callback(sender, record: RecordContext = None, metadata=None,
                                   collected_records: List[RecordContext] = None):
    # replace all references inside the metadata
    def replace_func(node):
        if isinstance(node, dict) and '$ref' in node:
            ref = node['$ref']
            pass
        return node

    transform_dicts_in_data(metadata, replace_func)


class OARepoReferencesDraft:
    def __init__(self, app=None, db=None):
        if app:
            self.init_app(app, db)

    # noinspection PyUnusedLocal
    def init_app(self, _app, db=None):
        collect_records.connect(collect_referenced_records)
        check_can_publish.connect(check_can_publish_callback)
        check_can_unpublish.connect(check_can_unpublish_callback)
        check_can_edit.connect(check_can_edit_callback)
        before_publish_record.connect(before_publish_record_callback)

from typing import List

from invenio_pidstore.models import PersistentIdentifier
from invenio_records_draft.api import CollectAction, RecordContext
from invenio_records_draft.proxies import current_drafts
from invenio_records_draft.signals import before_publish_record, \
    before_unpublish_record, collect_records
from oarepo_references.models import RecordReference
from oarepo_references.utils import transform_dicts_in_data


def collect_referenced_records(sender, record: RecordContext = None, action=None):
    # gather references inside the record (which point to draft or published record)
    for ref in RecordReference.query.filter_by(record_uuid=record.record.model.id):
        if not ref.reference_uuid:
            continue
        for pid in PersistentIdentifier.query.filter_by(object_type='rec',
                                                        object_uuid=ref.reference_uuid):
            if (
                (action == CollectAction.PUBLISH and current_drafts.is_draft(pid)) or
                (action != CollectAction.PUBLISH and current_drafts.is_published(pid))
            ):
                # this pid is the target pid
                yield RecordContext(record=current_drafts.get_record(pid),
                                    record_pid=pid,
                                    record_url=ref.reference)
                break


def before_publish_record_callback(sender, record: RecordContext = None, metadata=None,
                                   collected_records: List[RecordContext] = None):
    # replace all references to known draft records with published records inside the metadata
    def replace_func(node):
        if isinstance(node, dict) and '$ref' in node:
            ref = node['$ref']
            for referenced_rec in collected_records:
                if referenced_rec.record_url == ref:
                    node['$ref'] = referenced_rec.published_record_url
                    break
        return node

    transform_dicts_in_data(metadata, replace_func)


def before_unpublish_record_callback(sender, record: RecordContext = None, metadata=None,
                                     collected_records: List[RecordContext] = None):

    # replace all references to known draft records with published records inside the metadata
    def replace_func(node):
        if isinstance(node, dict) and '$ref' in node:
            ref = node['$ref']
            for referenced_rec in collected_records:
                if referenced_rec.record_url == ref:
                    node['$ref'] = referenced_rec.draft_record_url
                    break
        return node

    transform_dicts_in_data(metadata, replace_func)


class OARepoReferencesDraft:
    def __init__(self, app=None, db=None):
        if app:
            self.init_app(app, db)

    # noinspection PyUnusedLocal
    def init_app(self, _app, db=None):
        collect_records.connect(collect_referenced_records)
        before_publish_record.connect(before_publish_record_callback)
        before_unpublish_record.connect(before_unpublish_record_callback)

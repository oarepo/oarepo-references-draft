import uuid

from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from sample.records.config import DraftRecord, PublishedRecord

from invenio_records_draft.api import RecordContext
from invenio_records_draft.signals import CollectAction
from oarepo_references_draft.ext import collect_referenced_records


def test_collect(app, db, schemas):
    with db.session.begin_nested():
        draft_uuid = uuid.uuid4()

        rec1 = DraftRecord.create({
            'id': '1',
            'title': 'rec1'
        }, id_=draft_uuid)
        draft1_pid = PersistentIdentifier.create(
            pid_type='drecid', pid_value='1', status=PIDStatus.REGISTERED,
            object_type='rec', object_uuid=draft_uuid
        )

        published_uuid = uuid.uuid4()
        published = PublishedRecord.create({
            'id': '3',
            'title': 'rec1a'
        }, id_=published_uuid)
        published_pid = PersistentIdentifier.create(
            pid_type='recid', pid_value='3', status=PIDStatus.REGISTERED,
            object_type='rec', object_uuid=published_uuid
        )

        draft2_uuid = uuid.uuid4()
        rec2 = DraftRecord.create({
            'id': '2',
            'title': 'rec2',
            'ref': {'$ref': 'http://localhost/api/drafts/records/1'},
            'ref_pub': {'$ref': 'http://localhost/api/records/3'}
        }, id_=draft2_uuid)
        draft2_pid = PersistentIdentifier.create(
            pid_type='drecid', pid_value='2', status=PIDStatus.REGISTERED,
            object_type='rec', object_uuid=draft2_uuid
        )

    collected = list(
        collect_referenced_records(None, RecordContext(record=rec2, record_pid=draft2_pid),
                                   CollectAction.PUBLISH))
    assert len(collected) == 1
    assert collected[0].record_pid == draft1_pid
    assert collected[0].record.model.id == rec1.model.id


def test_collect_no_api(app, db, schemas):
    with db.session.begin_nested():
        draft_uuid = uuid.uuid4()

        rec1 = DraftRecord.create({
            'id': '1',
            'title': 'rec1'
        }, id_=draft_uuid)
        draft1_pid = PersistentIdentifier.create(
            pid_type='drecid', pid_value='1', status=PIDStatus.REGISTERED,
            object_type='rec', object_uuid=draft_uuid
        )

        published_uuid = uuid.uuid4()
        published = PublishedRecord.create({
            'id': '3',
            'title': 'rec1a'
        }, id_=published_uuid)
        published_pid = PersistentIdentifier.create(
            pid_type='recid', pid_value='3', status=PIDStatus.REGISTERED,
            object_type='rec', object_uuid=published_uuid
        )

        draft2_uuid = uuid.uuid4()
        rec2 = DraftRecord.create({
            'id': '2',
            'title': 'rec2',
            'ref': {'$ref': 'http://localhost/drafts/records/1'},
            'ref_pub': {'$ref': 'http://localhost/records/3'}
        }, id_=draft2_uuid)
        draft2_pid = PersistentIdentifier.create(
            pid_type='drecid', pid_value='2', status=PIDStatus.REGISTERED,
            object_type='rec', object_uuid=draft2_uuid
        )

    collected = list(
        collect_referenced_records(None, RecordContext(record=rec2, record_pid=draft2_pid),
                                   CollectAction.PUBLISH))
    assert len(collected) == 1
    assert collected[0].record_pid == draft1_pid
    assert collected[0].record.model.id == rec1.model.id


def test_collect_for_unpublish(app, db, schemas):
    with db.session.begin_nested():
        published_uuid = uuid.uuid4()

        rec1 = PublishedRecord.create({
            'id': '1',
            'title': 'rec1'
        }, id_=published_uuid)
        published1_pid = PersistentIdentifier.create(
            pid_type='recid', pid_value='1', status=PIDStatus.REGISTERED,
            object_type='rec', object_uuid=published_uuid
        )

        draft_uuid = uuid.uuid4()
        draft = DraftRecord.create({
            'id': '3',
            'title': 'rec1a'
        }, id_=draft_uuid)
        draft_pid = PersistentIdentifier.create(
            pid_type='drecid', pid_value='3', status=PIDStatus.REGISTERED,
            object_type='rec', object_uuid=draft_uuid
        )

        published2_uuid = uuid.uuid4()
        rec2 = PublishedRecord.create({
            'id': '2',
            'title': 'rec2',
            'ref': {'$ref': 'http://localhost/api/records/1'},
            'ref_pub': {'$ref': 'http://localhost/api/draft/records/3'}
        }, id_=published2_uuid)
        published2_pid = PersistentIdentifier.create(
            pid_type='recid', pid_value='2', status=PIDStatus.REGISTERED,
            object_type='rec', object_uuid=published2_uuid
        )

    collected = list(
        collect_referenced_records(None, RecordContext(record=rec2, record_pid=published2_pid),
                                   CollectAction.UNPUBLISH))
    assert len(collected) == 1
    assert collected[0].record_pid == published1_pid
    assert collected[0].record.model.id == rec1.model.id

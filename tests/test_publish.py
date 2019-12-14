import uuid

from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from sample.records.config import DraftRecord, PublishedRecord

from invenio_records_draft.api import RecordContext
from invenio_records_draft.proxies import current_drafts


def test_publish(app, db, schemas):
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

    current_drafts.publish(RecordContext(record=rec2, record_pid=draft2_pid))

    published2_pid = PersistentIdentifier.get(pid_type='recid', pid_value=draft2_pid.pid_value)
    pr = PublishedRecord.get_record(published2_pid.object_uuid)
    assert pr.dumps() == {
        '$schema': 'https://localhost/schemas/records/record-v1.0.0.json',
        'id': '2',
        'ref': {'$ref': 'http://localhost/records/1'},
        'ref_pub': {'$ref': 'http://localhost/records/3'},
        'title': 'rec2'
    }

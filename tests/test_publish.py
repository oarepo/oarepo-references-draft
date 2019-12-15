import uuid

from invenio_indexer.api import RecordIndexer
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_search import current_search_client, current_search, RecordsSearch
from sample.records.config import DraftRecord, PublishedRecord

from invenio_records_draft.api import RecordContext
from invenio_records_draft.proxies import current_drafts


def test_publish(app, db, schemas, mappings, prepare_es):
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
        RecordIndexer().index(rec2)

    current_search_client.indices.flush()

    es_draft2 = RecordsSearch(index='draft-records-record-v1.0.0').get_record(draft2_pid.object_uuid).execute()
    assert len(es_draft2.hits) == 1

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

    current_search_client.indices.flush()

    es_published2 = RecordsSearch(index='records-record-v1.0.0').get_record(published2_pid.object_uuid).execute()
    assert len(es_published2.hits) == 1
    es_published2 = es_published2.hits[0].to_dict()
    es_published2.pop('_created')
    es_published2.pop('_updated')
    assert es_published2 == {
        '$schema': 'https://localhost/schemas/records/record-v1.0.0.json',
        'id': '2',
        'ref': {'published': '1'},
        'ref_pub': {'published': '3'},
        'title': 'rec2'}

    es_draft2 = RecordsSearch(index='draft-records-record-v1.0.0').get_record(draft2_pid.object_uuid).execute()
    assert len(es_draft2.hits) == 0

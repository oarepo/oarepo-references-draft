import uuid

from invenio_indexer.api import RecordIndexer
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_search import current_search_client, current_search, RecordsSearch
from sample.records.config import DraftRecord, PublishedRecord

from invenio_records_draft.api import RecordContext
from invenio_records_draft.proxies import current_drafts
from tests.helpers import disable_test_authenticated


def test_unpublish(app, db, schemas, mappings, prepare_es):
    with disable_test_authenticated():
        with db.session.begin_nested():
            published_uuid1 = uuid.uuid4()

            published_rec1 = PublishedRecord.create({
                'id': '1',
                'title': 'rec1'
            }, id_=published_uuid1)
            published_pid1 = PersistentIdentifier.create(
                pid_type='recid', pid_value='1', status=PIDStatus.REGISTERED,
                object_type='rec', object_uuid=published_uuid1
            )

            published_uuid2 = uuid.uuid4()
            published_rec2 = PublishedRecord.create({
                'id': '2',
                'title': 'rec2'
            }, id_=published_uuid2)
            published_pid2 = PersistentIdentifier.create(
                pid_type='recid', pid_value='2', status=PIDStatus.REGISTERED,
                object_type='rec', object_uuid=published_uuid2
            )

            published_uuid3 = uuid.uuid4()
            published_rec3 = PublishedRecord.create({
                'id': '3',
                'title': 'rec3',
                'ref': {'$ref': 'http://localhost/records/1'},
                'ref_pub': {'$ref': 'http://localhost/records/2'}
            }, id_=published_uuid3)
            published_pid3 = PersistentIdentifier.create(
                pid_type='recid', pid_value='3', status=PIDStatus.REGISTERED,
                object_type='rec', object_uuid=published_uuid3
            )
            RecordIndexer().index(published_rec3)

        current_search_client.indices.flush()

        es = RecordsSearch(index='draft-records-record-v1.0.0'). \
            get_record(published_pid3.object_uuid).execute()
        assert len(es.hits) == 0

        es = RecordsSearch(index='records-record-v1.0.0'). \
            get_record(published_pid3.object_uuid).execute()
        assert len(es.hits) == 1

        current_drafts.unpublish(RecordContext(record=published_rec3, record_pid=published_pid3))

        draft_pid3 = PersistentIdentifier.get(pid_type='drecid',
                                              pid_value=published_pid3.pid_value)
        pr = DraftRecord.get_record(draft_pid3.object_uuid)
        assert pr.dumps() == {
            '$schema': 'https://localhost/schemas/draft/records/record-v1.0.0.json',
            'id': '3',
            'invenio_draft_validation': {'valid': True},
            'ref': {'$ref': 'http://localhost/drafts/records/1'},
            'ref_pub': {'$ref': 'http://localhost/drafts/records/2'},
            'title': 'rec3'
        }

        draft_pid2 = PersistentIdentifier.get(pid_type='drecid',
                                              pid_value=published_pid2.pid_value)
        pr = DraftRecord.get_record(draft_pid2.object_uuid)
        assert pr.dumps() == {
            '$schema': 'https://localhost/schemas/draft/records/record-v1.0.0.json',
            'id': '2',
            'invenio_draft_validation': {'valid': True},
            'title': 'rec2'
        }

        draft_pid1 = PersistentIdentifier.get(pid_type='drecid',
                                              pid_value=published_pid1.pid_value)
        pr = DraftRecord.get_record(draft_pid1.object_uuid)
        assert pr.dumps() == {
            '$schema': 'https://localhost/schemas/draft/records/record-v1.0.0.json',
            'id': '1',
            'invenio_draft_validation': {'valid': True},
            'title': 'rec1'
        }

        current_search_client.indices.flush()

        es = RecordsSearch(index='draft-records-record-v1.0.0'). \
            get_record(draft_pid3.object_uuid).execute()
        assert len(es.hits) == 1
        es = es.hits[0].to_dict()
        es.pop('_created')
        es.pop('_updated')
        assert es == {
            '$schema': 'https://localhost/schemas/draft/records/record-v1.0.0.json',
            'id': '3',
            'invenio_draft_validation': {'valid': True},
            'ref': {'draft': '1'},
            'ref_pub': {'draft': '2'},
            'title': 'rec3'
        }

        es = RecordsSearch(index='records-record-v1.0.0'). \
            get_record(published_pid3.object_uuid).execute()
        assert len(es.hits) == 0

        es = RecordsSearch(index='draft-records-record-v1.0.0'). \
            get_record(draft_pid1.object_uuid).execute()
        assert len(es.hits) == 1
        es = es.hits[0].to_dict()
        es.pop('_created')
        es.pop('_updated')
        assert es == {
            '$schema': 'https://localhost/schemas/draft/records/record-v1.0.0.json',
            'id': '1',
            'invenio_draft_validation': {'valid': True},
            'title': 'rec1'
        }

        es = RecordsSearch(index='records-record-v1.0.0'). \
            get_record(published_pid1.object_uuid).execute()
        assert len(es.hits) == 0

        es = RecordsSearch(index='records-record-v1.0.0'). \
            get_record(published_pid3.object_uuid).execute()
        assert len(es.hits) == 0

        es = RecordsSearch(index='draft-records-record-v1.0.0'). \
            get_record(draft_pid2.object_uuid).execute()
        assert len(es.hits) == 1
        es = es.hits[0].to_dict()
        es.pop('_created')
        es.pop('_updated')
        assert es == {
            '$schema': 'https://localhost/schemas/draft/records/record-v1.0.0.json',
            'id': '2',
            'invenio_draft_validation': {'valid': True},
            'title': 'rec2'
        }

        es = RecordsSearch(index='records-record-v1.0.0'). \
            get_record(published_pid2.object_uuid).execute()
        assert len(es.hits) == 0

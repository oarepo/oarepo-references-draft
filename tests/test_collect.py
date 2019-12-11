import uuid

from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_records import Record

from invenio_records_draft.api import RecordContext
from invenio_records_draft.record import (
    DraftEnabledRecordMixin,
    MarshmallowValidator,
)
from invenio_records_draft.signals import CollectAction
from oarepo_references_draft.ext import collect_referenced_records


class TestDraftRecord(DraftEnabledRecordMixin, Record):
    schema = None

    def validate(self, **kwargs):
        self['$schema'] = self.schema
        return super().validate(**kwargs)

    draft_validator = MarshmallowValidator(
        'sample.records.marshmallow:MetadataSchemaV1',
        'records/record-v1.0.0.json'
    )


class TestPublishedRecord(DraftEnabledRecordMixin, Record):
    schema = None

    def validate(self, **kwargs):
        self['$schema'] = self.schema
        return super().validate(**kwargs)


def test_collect(app, db, schemas):
    TestDraftRecord.schema = schemas['draft']
    TestPublishedRecord.schema = schemas['published']
    with db.session.begin_nested():
        draft_uuid = uuid.uuid4()

        rec1 = TestDraftRecord.create({
            'id': '1',
            'title': 'rec1'
        }, id_=draft_uuid)
        draft1_pid = PersistentIdentifier.create(
            pid_type='drecid', pid_value='1', status=PIDStatus.REGISTERED,
            object_type='rec', object_uuid=draft_uuid
        )

        draft2_uuid = uuid.uuid4()
        rec2 = TestDraftRecord.create({
            'id': '2',
            'title': 'rec2',
            'ref': {'$ref': 'http://localhost/api/drafts/records/1'}
        }, id_=draft2_uuid)
        draft2_pid = PersistentIdentifier.create(
            pid_type='drecid', pid_value='2', status=PIDStatus.REGISTERED,
            object_type='rec', object_uuid=draft2_uuid
        )

    collected = list(collect_referenced_records(None, RecordContext(record=rec2, record_pid=draft2_pid),
                                                CollectAction.PUBLISH))
    assert len(collected) == 1
    assert collected[0].record_pid == draft1_pid
    assert collected[0].record.model.id == rec1.model.id

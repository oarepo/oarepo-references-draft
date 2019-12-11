import uuid

import pytest
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_records import Record

from invenio_records_draft.api import RecordContext
from invenio_records_draft.proxies import current_drafts
from invenio_records_draft.record import (
    DraftEnabledRecordMixin,
    InvalidRecordException,
    MarshmallowValidator,
)
from tests.helpers import disable_test_authenticated


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


def test_publish_record(app, db, schemas):
    TestDraftRecord.schema = schemas['draft']
    TestPublishedRecord.schema = schemas['published']
    with db.session.begin_nested():
        draft_uuid = uuid.uuid4()

        rec = TestDraftRecord.create({
            'id': '1'
        }, id_=draft_uuid)
        draft_pid = PersistentIdentifier.create(
            pid_type='drecid', pid_value='1', status=PIDStatus.REGISTERED,
            object_type='rec', object_uuid=draft_uuid
        )

        with pytest.raises(InvalidRecordException):
            # title is required but not in rec, so should fail
            with disable_test_authenticated():
                current_drafts.publish(RecordContext(record=rec, record_pid=draft_pid))

        with pytest.raises(PIDDoesNotExistError):
            # no record should be created
            PersistentIdentifier.get(pid_type='recid', pid_value='1')

        # make the record valid
        rec['title'] = 'blah'
        rec.commit()

        # and publish it again
        with disable_test_authenticated():
            current_drafts.publish(RecordContext(record=rec, record_pid=draft_pid))

        # draft should be gone
        draft_pid = PersistentIdentifier.get(pid_type='drecid', pid_value='1')
        assert draft_pid.status == PIDStatus.DELETED
        rec = TestDraftRecord.get_record(draft_uuid, with_deleted=True)
        assert rec.model.json is None

        published_pid = PersistentIdentifier.get(pid_type='recid', pid_value='1')
        assert published_pid.status == PIDStatus.REGISTERED
        rec = TestPublishedRecord.get_record(published_pid.object_uuid)
        assert rec.model.json is not None

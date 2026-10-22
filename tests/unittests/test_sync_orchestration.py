import copy
import unittest
from unittest.mock import MagicMock, patch

from singer.catalog import Catalog

from tap_ukg_pro_ultipro.exceptions import UKGProError, UKGProInternalServerError
from tap_ukg_pro_ultipro.streams import STREAMS
from tap_ukg_pro_ultipro.sync import get_stream_object, sync, write_schema

from test_stream_sync import make_client, make_entry, position

ROLES = STREAMS["roles"].path
JOBS = STREAMS["jobs"].path
POSITIONS = STREAMS["positions"].path
PERSON_DETAILS = STREAMS["person_details"].path


class SyncHarness(unittest.TestCase):
    """Runs `sync` with writers patched and records everything that is emitted."""

    def setUp(self):
        self.events = []
        self.states = []
        patches = [
            patch(
                "tap_ukg_pro_ultipro.streams.abstracts.write_schema",
                side_effect=lambda stream_id, schema, keys: self.events.append(("schema", stream_id)),
            ),
            patch(
                "tap_ukg_pro_ultipro.streams.abstracts.write_record",
                side_effect=lambda stream_id, record: self.events.append(("record", stream_id)),
            ),
            patch("singer.write_state", side_effect=lambda state: self.states.append(copy.deepcopy(state))),
        ]
        for patcher in patches:
            patcher.start()
            self.addCleanup(patcher.stop)

    @staticmethod
    def catalog(*names, unselected=()):
        return Catalog([make_entry(name, selected=name not in unselected) for name in names])

    def run_sync(self, catalog, client, state=None):
        state = {} if state is None else state
        sync(client, {}, catalog, state)
        return state

    def schema_order(self):
        return [stream_id for kind, stream_id in self.events if kind == "schema"]

    def records_of(self, stream_id):
        return [e for e in self.events if e == ("record", stream_id)]


class TestStreamSelection(SyncHarness):

    def test_only_selected_streams_are_requested_and_written(self):
        client = make_client({
            ROLES: [[{"roleId": "1"}]],
            JOBS: [[{"jobCode": "J1"}]],
        })
        catalog = self.catalog("roles", "jobs", "tax_groups", unselected=("jobs",))

        self.run_sync(catalog, client)

        requested = {request["endpoint"] for request in client.requests}
        self.assertEqual(requested, {ROLES, STREAMS["tax_groups"].path})
        self.assertEqual(self.schema_order(), ["roles", "tax_groups"])
        self.assertEqual(len(self.records_of("roles")), 1)
        self.assertEqual(self.records_of("jobs"), [])

    def test_schema_is_written_once_before_the_records_of_each_stream(self):
        client = make_client({ROLES: [[{"roleId": "1"}, {"roleId": "2"}]]})

        self.run_sync(self.catalog("roles"), client)

        self.assertEqual(
            self.events,
            [("schema", "roles"), ("record", "roles"), ("record", "roles")],
        )

    def test_nothing_selected_syncs_nothing(self):
        client = make_client()

        self.run_sync(self.catalog("roles", unselected=("roles",)), client)

        self.assertEqual(self.events, [])
        client.make_request.assert_not_called()

    def test_stream_not_supported_by_the_tap_raises(self):
        entry = make_entry("roles")
        entry.tap_stream_id = entry.stream = "does_not_exist"

        with self.assertRaises(UKGProError) as ctx:
            self.run_sync(Catalog([entry]), make_client())

        self.assertIn("does_not_exist", str(ctx.exception))

    def test_get_stream_object_requires_a_catalog_entry(self):
        with self.assertRaises(UKGProError):
            get_stream_object("roles", make_client(), Catalog([]))


class TestStateAndResume(SyncHarness):

    def test_currently_syncing_is_set_per_stream_and_cleared_at_the_end(self):
        client = make_client({ROLES: [[{"roleId": "1"}]], JOBS: [[{"jobCode": "J1"}]]})

        final_state = self.run_sync(self.catalog("roles", "jobs"), client)

        self.assertEqual(
            [s.get("currently_syncing") for s in self.states],
            ["roles", None, "jobs", None],
        )
        self.assertNotIn("currently_syncing", final_state)
        self.assertNotIn("currently_syncing", self.states[-1])

    def test_bookmark_is_in_the_state_written_when_the_stream_finishes(self):
        client = make_client({POSITIONS: [[position("A", "2022-03-01T00:00:00Z")]]})

        self.run_sync(self.catalog("positions"), client)

        self.assertEqual(
            self.states[-1],
            {"bookmarks": {"positions": {"dateTimeCreated": "2022-03-01T00:00:00.000000Z"}}},
        )

    def test_interrupted_sync_resumes_with_the_currently_syncing_stream(self):
        client = make_client()
        state = {"currently_syncing": "roles"}

        self.run_sync(self.catalog("positions", "roles", "jobs"), client, state)

        self.assertEqual(self.schema_order(), ["roles", "jobs", "positions"])
        self.assertNotIn("currently_syncing", state)

    def test_unknown_currently_syncing_stream_is_ignored(self):
        client = make_client()
        state = {"currently_syncing": "removed_stream"}

        self.run_sync(self.catalog("roles", "jobs"), client, state)

        self.assertEqual(self.schema_order(), ["roles", "jobs"])
        self.assertNotIn("currently_syncing", state)

    def test_existing_bookmarks_are_preserved(self):
        bookmarks = {"positions": {"dateTimeCreated": "2022-06-01T00:00:00.000000Z"}}
        client = make_client({ROLES: [[{"roleId": "1"}]]})
        state = {"bookmarks": copy.deepcopy(bookmarks)}

        self.run_sync(self.catalog("roles"), client, state)

        self.assertEqual(state["bookmarks"], bookmarks)

    def test_failed_stream_keeps_currently_syncing_and_stops_the_run(self):
        client = make_client(
            {JOBS: [[{"jobCode": "J1"}]]},
            error_by_path={ROLES: UKGProInternalServerError("HTTP-error-code: 500")},
        )
        state = {}

        with self.assertRaises(UKGProInternalServerError):
            self.run_sync(self.catalog("jobs", "roles", "tax_groups"), client, state)

        # jobs finished, roles failed, tax_groups was never started
        self.assertEqual(self.states[-1]["currently_syncing"], "roles")
        self.assertEqual(state["currently_syncing"], "roles")
        self.assertEqual(self.schema_order(), ["jobs", "roles"])
        requested = {request["endpoint"] for request in client.requests}
        self.assertNotIn(STREAMS["tax_groups"].path, requested)

    def test_rerun_after_failure_starts_with_the_failed_stream(self):
        client = make_client()
        state = {"currently_syncing": "roles", "bookmarks": {}}

        self.run_sync(self.catalog("jobs", "roles", "tax_groups"), client, state)

        self.assertEqual(self.schema_order(), ["roles", "tax_groups", "jobs"])


class TestParentChildStreams(SyncHarness):
    """No concrete stream declares a parent today; these cover the supported mechanism.

    `positions` is temporarily declared as the parent of `person_details`.
    """

    def setUp(self):
        super().setUp()
        for patcher in (
            patch.object(STREAMS["positions"], "children", ["person_details"]),
            patch.object(STREAMS["person_details"], "parent", "positions"),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)

    def client(self):
        return make_client({
            POSITIONS: [[position("A", "2022-03-01T00:00:00Z"), position("B", "2022-04-01T00:00:00Z")]],
            PERSON_DETAILS: [[{"employeeId": "E1", "datetimeCreated": "2022-03-05T00:00:00Z"}]],
        })

    def test_parent_syncs_the_selected_child_once_per_parent_record(self):
        client = self.client()

        self.run_sync(self.catalog("positions", "person_details"), client)

        self.assertEqual(self.schema_order(), ["positions", "person_details"])
        self.assertEqual(len(self.records_of("positions")), 2)
        self.assertEqual(len(self.records_of("person_details")), 2)
        child_requests = [r for r in client.requests if r["endpoint"] == PERSON_DETAILS and r["params"]["page"] == 1]
        self.assertEqual(len(child_requests), 2)

    def test_child_is_not_synced_on_its_own(self):
        client = self.client()

        self.run_sync(self.catalog("positions", "person_details"), client)

        # exactly one top level pass over the parent endpoint (page 1 plus the empty page)
        parent_pages = [r["params"]["page"] for r in client.requests if r["endpoint"] == POSITIONS]
        self.assertEqual(parent_pages, [1, 2])

    def test_selecting_only_the_child_still_reads_the_parent_but_writes_only_child_data(self):
        client = self.client()

        self.run_sync(self.catalog("positions", "person_details", unselected=("positions",)), client)

        self.assertEqual(self.schema_order(), ["person_details"])
        self.assertEqual(self.records_of("positions"), [])
        self.assertEqual(len(self.records_of("person_details")), 2)

    def test_unselected_child_is_not_synced(self):
        client = self.client()

        self.run_sync(self.catalog("positions", "person_details", unselected=("person_details",)), client)

        self.assertEqual(self.schema_order(), ["positions"])
        self.assertNotIn(PERSON_DETAILS, {r["endpoint"] for r in client.requests})


class TestWriteSchemaChildren(unittest.TestCase):

    def test_child_missing_from_the_catalog_is_skipped(self):
        parent = MagicMock()
        parent.is_selected.return_value = True
        parent.children = ["roles"]
        parent.child_to_sync = []
        catalog = MagicMock()
        catalog.get_stream.return_value = None

        write_schema(parent, MagicMock(), ["roles"], catalog)

        parent.write_schema.assert_called_once()
        self.assertEqual(parent.child_to_sync, [])

import hashlib
import hmac
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

from orville_core.scheduler import EventIntake, ScheduleStore


class SchedulerTests(unittest.TestCase):
    def test_schedule_enable_due_and_claim(self):
        with tempfile.TemporaryDirectory() as directory:
            store = ScheduleStore(Path(directory) / "scheduler.db")
            schedule = store.create("schedule-1", "workflow-1", 60)
            store.set_enabled(schedule.schedule_id, True)
            due = store.due(datetime.now(UTC) + timedelta(seconds=61))
            self.assertEqual(len(due), 1)
            claimed = store.claim(schedule.schedule_id)
            self.assertTrue(claimed.next_run_at)

    def test_signed_event_intake_is_idempotent(self):
        secret = "signing-secret"
        intake = EventIntake(secret)
        body = b'{"ok":true}'
        signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        accepted = intake.accept("event-1", "webhook", "task", {"ok": True}, signature_body=body, signature=signature)
        duplicate = intake.accept("event-1", "webhook", "task", {"ok": True}, signature_body=body, signature=signature)
        invalid = intake.accept("event-2", "webhook", "task", {}, signature_body=body, signature="bad")
        self.assertTrue(accepted.accepted)
        self.assertFalse(duplicate.accepted)
        self.assertFalse(invalid.accepted)


if __name__ == "__main__":
    unittest.main()

    def test_schedule_leases_are_exclusive_and_recoverable(self):
        with tempfile.TemporaryDirectory() as directory:
            store = ScheduleStore(Path(directory) / "scheduler.db")
            schedule = store.create("schedule-lease", "workflow-1", 60)
            store.set_enabled(schedule.schedule_id, True)
            now = datetime.now(UTC)
            claimed = store.claim(schedule.schedule_id, now=now, worker_id="worker-a", lease_seconds=30)
            self.assertEqual(claimed.lease_owner, "worker-a")
            with self.assertRaises(RuntimeError):
                store.claim(schedule.schedule_id, now=now + timedelta(seconds=1), worker_id="worker-b", lease_seconds=30)
            self.assertEqual(store.recover_stale_leases(now=now + timedelta(seconds=31)), 1)
            reclaimed = store.claim(schedule.schedule_id, now=now + timedelta(seconds=32), worker_id="worker-b", lease_seconds=30)
            self.assertEqual(reclaimed.lease_owner, "worker-b")
            released = store.release(schedule.schedule_id, worker_id="worker-b")
            self.assertIsNone(released.lease_owner)

    def test_schedule_list_includes_disabled_schedules(self):
        with tempfile.TemporaryDirectory() as directory:
            store = ScheduleStore(Path(directory) / "scheduler.db")
            store.create("schedule-list", "workflow-1", 60)
            self.assertEqual([item.schedule_id for item in store.list()], ["schedule-list"])

    def test_timestamped_signature_and_recent_delivery_record(self):
        secret = "signing-secret"
        with tempfile.TemporaryDirectory() as directory:
            intake = EventIntake(secret, Path(directory) / "events.db")
            body = b'{"event_id":"event-ts","payload":{"ok":true}}'
            timestamp = int(datetime.now(UTC).timestamp())
            signed = f"{timestamp}.".encode() + body
            signature = f"t={timestamp},v1=" + hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
            accepted = intake.accept("event-ts", "webhook", "task", {"ok": True}, signature_body=body, signature=signature)
            duplicate = intake.accept("event-ts", "webhook", "task", {"ok": True}, signature_body=body, signature=signature)
            self.assertTrue(accepted.accepted)
            self.assertFalse(duplicate.accepted)
            recent = intake.recent()
            self.assertEqual(recent[0]["event_id"], "event-ts")
            self.assertTrue(recent[0]["accepted"])

    def test_invalid_metadata_is_rejected_before_persistence(self):
        with tempfile.TemporaryDirectory() as directory:
            intake = EventIntake(None, Path(directory) / "events.db")
            rejected = intake.accept("", "webhook", "task", {})
            self.assertFalse(rejected.accepted)
            self.assertEqual(rejected.reason, "invalid event metadata")
            self.assertEqual(intake.recent(), tuple())

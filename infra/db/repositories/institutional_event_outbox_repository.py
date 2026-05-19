import json


class InstitutionalEventOutboxRepository:

    def __init__(self, conn):
        self.conn = conn
        self.enabled = self._table_exists()

    def _table_exists(self):
        with self.conn.cursor() as cursor:
            cursor.execute("""
                SELECT to_regclass('analytics.institutional_events_outbox')
            """)
            return cursor.fetchone()[0] is not None

    def publish(self, event):
        if not self.enabled:
            return False

        payload = event.to_dict()

        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO analytics.institutional_events_outbox (
                    event_type,
                    event_date,
                    source_system,
                    source_reference,
                    source_record_id,
                    source_document_id,
                    source_url,
                    raw_hash,
                    normalized_hash,
                    payload
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                ON CONFLICT (
                    source_system,
                    source_reference,
                    event_type
                )
                DO UPDATE SET
                    event_date = EXCLUDED.event_date,
                    source_record_id = EXCLUDED.source_record_id,
                    source_document_id = EXCLUDED.source_document_id,
                    source_url = EXCLUDED.source_url,
                    raw_hash = EXCLUDED.raw_hash,
                    normalized_hash = EXCLUDED.normalized_hash,
                    payload = EXCLUDED.payload,
                    status = 'pending',
                    last_error = NULL
            """, (
                payload["event_type"],
                payload.get("event_date"),
                payload["source_system"],
                payload["source_reference"],
                payload.get("source_record_id"),
                payload.get("source_document_id"),
                payload.get("source_url"),
                payload.get("raw_hash"),
                payload.get("normalized_hash"),
                json.dumps(payload, ensure_ascii=False),
            ))

        return True

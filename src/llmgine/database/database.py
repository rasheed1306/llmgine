import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from llmgine.messages import EVENT_CLASSES, ScheduledEvent


class DatabaseEngine:
    _engine: Optional[Engine] = None

    @classmethod
    def get_engine(cls) -> Engine:
        if cls._engine is None:
            # Load environment and create engine
            project_root = Path(__file__).parent.parent.parent.parent
            env_path = project_root / ".env"
            load_dotenv(dotenv_path=env_path, override=True)
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                raise ValueError("DATABASE_URL is not set.")
            cls._engine = create_engine(database_url)
        return cls._engine


def get_and_delete_unfinished_events() -> List[ScheduledEvent]:
    """
    Retrieve all unfinished events from the database and delete them.

    Returns:
        List[ScheduledEvent]: List of events that were stored in the database
    """
    engine = DatabaseEngine.get_engine()
    events: List[ScheduledEvent] = []

    try:
        with engine.connect() as connection:
            # Get all events from the database
            select_query = text("""
                SELECT event_data, event_class_name
                FROM silver.llmgine_bus_events 
                ORDER BY event_timestamp ASC
            """)

            result = connection.execute(select_query)
            rows = result.fetchall()

            # Convert JSON data back to Event objects
            for row in rows:
                event_data = row[0]  # event_data column
                event_class_name = row[1]  # event_class_name column
                try:
                    # Try to reconstruct the event from the stored data
                    event: ScheduledEvent = EVENT_CLASSES[event_class_name].from_dict(
                        event_data
                    )
                    events.append(event)
                except Exception as e:
                    print(f"Error reconstructing event from data: {e}")
                    # Continue with other events even if one fails

            # Delete all events after successful retrieval
            if rows:
                delete_query = text("DELETE FROM silver.llmgine_bus_events")
                connection.execute(delete_query)
                connection.commit()
                print(f"Retrieved and deleted {len(events)} unfinished events")

    except Exception as e:
        print(f"Error retrieving unfinished events: {e}")
        return []

    return events


def save_unfinished_events(events: List[ScheduledEvent]) -> None:
    """
    Save a list of unfinished events to the database.

    Args:
        events: List of events to save
    """
    if not events:
        return

    engine = DatabaseEngine.get_engine()

    try:
        with engine.connect() as connection:
            # Prepare the insert statement
            insert_query = text("""
                INSERT INTO silver.llmgine_bus_events (event_data, event_timestamp, event_class_name)
                VALUES (:event_data, :event_timestamp, :event_class_name)
            """)

            # Convert events to JSON and insert
            for event in events:
                event_dict = event.to_dict()
                connection.execute(
                    insert_query,
                    {
                        "event_data": json.dumps(event_dict),
                        "event_timestamp": datetime.now(),
                        "event_class_name": event.__class__.__name__,
                    },
                )

            connection.commit()
            print(f"Saved {len(events)} unfinished events to database")

    except Exception as e:
        print(f"Error saving unfinished events: {e}")

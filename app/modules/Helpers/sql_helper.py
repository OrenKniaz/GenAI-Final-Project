# app/modules/Helpers/sql_helper.py
# This module provides helper functions for connecting to the SQL Server database and running queries. It uses the pyodbc library to manage database connections and execute SQL commands.

import datetime as dt

import pyodbc

from app.config import get_settings # Import the get_settings function from the config module to access the SQL Server connection string and other settings.

# A helper function to create and return a new database connection using the connection string from the settings.
def get_connection() -> pyodbc.Connection:
    settings = get_settings()
    return pyodbc.connect(settings.sql_server_connection_string)

# A function that runs a simple query to get available interview slots from the Schedule table. It uses a parameterized query to limit the number of results returned.
def get_available_slots(
    position: str,
    limit: int = 3,
    target_date: dt.date | None = None,
    target_time: dt.time | None = None,
    from_date: dt.date | None = None,
):
    if target_date is None or target_time is None:
        query = """
            SELECT TOP (?) ScheduleID, [date], [time], position
            FROM dbo.Schedule
            WHERE available = 1
            AND position = ?
            AND (? IS NULL OR [date] >= ?)
            ORDER BY [date], [time]
        """
        params = (limit, position, from_date, from_date)
    else:
        query = """
            SELECT TOP (?) ScheduleID, [date], [time], position
            FROM dbo.Schedule
            WHERE available = 1
              AND position = ?
            ORDER BY ABS(
                DATEDIFF(
                    MINUTE,
                    CAST(? AS datetime) + CAST(? AS datetime),
                    CAST([date] AS datetime) + CAST([time] AS datetime)
                )
            ),
            [date],
            [time]
        """
        params = (limit, position, target_date, target_time)

    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(query, *params)
        return cursor.fetchall()

# A function that gives more accurte available slot based on the candidate's requested time.
# Basically asking, does the candidate requested time exists for the role?
def get_exact_available_slot(position: str, slot_date: dt.date, slot_time: dt.time):
    query = """
        SELECT TOP (1) ScheduleID, [date], [time], position
        FROM dbo.Schedule
        WHERE available = 1
          AND position = ?
          AND [date] = ?
          AND [time] = ?
    """
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(query, position, slot_date, slot_time)
        return cursor.fetchone()


# get the earliest available slot for interview
def get_schedule_reference_date(position: str) -> dt.date | None:
    query = """
        SELECT MIN([date])
        FROM dbo.Schedule
        WHERE available = 1
          AND position = ?
    """
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(query, position)
        result = cursor.fetchone()
        return result[0] if result else None

if __name__ == "__main__":
    slots = get_available_slots(position="Python Dev")
    for row in slots:
        print(row)
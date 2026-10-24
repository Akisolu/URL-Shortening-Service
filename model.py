import sqlite3 as db
from datetime import UTC, datetime


class Database:
    def conect(self, path: str, name: str):
        connection = db.connect(f"{path}/{name}.db")
        cursor = connection.cursor()

        return cursor, connection

    def save_shorten_url(self, url: str, shortCode: str, cursor, connection):
        """
        Save a URL to the database
        """

        time_and_hours = datetime.now(UTC).isoformat(timespec="seconds")

        # Logic for saving the shortened URL to the database
        cursor.execute(
            "INSERT INTO urls (url, short_code, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (url, shortCode, time_and_hours, time_and_hours),
        )
        connection.commit()
        return {
            "id": cursor.lastrowid,
            "url": url,
            "shortCode": shortCode,
            "createdAt": time_and_hours,
            "updatedAt": time_and_hours,
        }

    def update_short_code(
        self, current_short_code: str, new_short_code: str, cursor, connection
    ):
        """
        Replaces the short code of an existing row
        """
        cursor.execute(
            "UPDATE urls SET short_code = ? WHERE short_code = ?",
            (new_short_code, current_short_code),
        )
        connection.commit()

    def get_shorten_url(self, shortCode: str, cursor):
        """
        Get a URL using the shortcode from the database
        """
        # Logic for retrieving the shortened URL details from the database
        cursor.execute(
            "SELECT url_id, url, short_code, created_at, updated_at FROM urls WHERE short_code = ?",
            (shortCode,),
        )

        result = cursor.fetchone()
        if result is None:
            return None

        return {
            "id": result[0],
            "url": result[1],
            "shortCode": result[2],
            "createdAt": result[3],
            "updatedAt": result[4],
        }

    def update_shorten_url(
        self, shortCode: str, url: str, new_shortCode: str, cursor, connection
    ):
        """
        Updates a URL associated with a shortcode in the database
        """

        time_and_hours = datetime.now(UTC).isoformat(timespec="seconds")

        # Logic for updating the shortened URL in the database
        cursor.execute(
            "UPDATE urls SET url = ?, short_code = ?, updated_at = ? WHERE short_code = ?",
            (url, new_shortCode, time_and_hours, shortCode),
        )

        connection.commit()

        return self.get_shorten_url(new_shortCode, cursor)

    def delete_shorten_url(self, shortCode: str, cursor, connection):
        """
        Deletes a shortcode and its associated URL from the database
        """
        # Logic for deleting the shortened URL from the database
        cursor.execute("DELETE FROM urls WHERE short_code = ?", (shortCode,))
        connection.commit()

        return True

    def get_shorten_url_stats(self, shortCode: str, cursor):
        """
        Retrieves statistics for a short code
        """
        # Logic for retrieving the statistics of the shortened URL from the database
        cursor.execute("SELECT * FROM urls WHERE short_code = ?", (shortCode,))

        result = cursor.fetchone()
        if result is None:
            return None

        return {
            "id": result[0],
            "url": result[1],
            "shortCode": result[2],
            "createdAt": result[3],
            "updatedAt": result[4],
            "accessCount": result[5],
        }

    def url_exists(self, url: str, cursor):
        """
        Checks if a URL exists.
        Returns True if it exists.
        Returns False if it does not exist.
        """
        cursor.execute("SELECT COUNT(*) FROM urls WHERE url = ? LIMIT 1", (url,))

        result = cursor.fetchone()

        count = result[0]

        if count == 0:
            return False

        return True

    def short_code_exists(self, shortCode: str, cursor):
        """
        Checks if a Short code exists.
        Returns True if it exists.
        Returns False if it does not exist.
        """
        cursor.execute(
            "SELECT COUNT(*) FROM urls WHERE short_code = ? LIMIT 1", (shortCode,)
        )

        result = cursor.fetchone()

        count = result[0]

        if count == 0:
            return False

        return True

    def increment_counter(self, shortCode: str, cursor, conn):
        """
        Atomically increments the access count for a URL.
        Returns the number of rows affected (0 if the code does not exist).
        """
        # A single UPDATE avoids the read-modify-write race of a SELECT + UPDATE
        # pair, so concurrent requests cannot overwrite each other's increment.
        cursor.execute(
            "UPDATE urls SET access_count = access_count + 1 WHERE short_code = ?",
            (shortCode,),
        )

        conn.commit()

        return cursor.rowcount

    def close(self, connection):
        connection.close()

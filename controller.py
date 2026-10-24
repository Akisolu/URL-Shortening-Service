from uuid import uuid4

from fastapi import HTTPException, status
from pydantic import HttpUrl

from model import Database

BASE62_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

# Generated codes are derived from the autoincremented id. The offset keeps the
# first codes from being trivially enumerable (/1, /2, /3...).
SHORT_CODE_OFFSET = 100_000


def encode_base62(number: int) -> str:
    """
        Encode a non-negative integer using the Base62 alphabet.
    """
    if number < 0:
        raise ValueError("Only non-negative integers can be encoded.")

    if number == 0:
        return BASE62_ALPHABET[0]

    encoded = []
    while number > 0:
        number, remainder = divmod(number, 62)
        encoded.append(BASE62_ALPHABET[remainder])

    return "".join(reversed(encoded))


class URLController:
    def __init__(self):
        self.db = Database()
        self.cursor, self.conn = self.db.conect("database", "url_shortener")

    def create_shorten_url(self, url: HttpUrl, shortCode: str | None):
        url = str(url)  # Convert HttpUrl to string
        self._ensure_url_not_exists(url)

        # If ShortCode is None, it generates one; otherwise, it uses the provided ShortCode.
        if shortCode is not None:
            self._ensure_not_short_code_exists(shortCode)
            return self.db.save_shorten_url(url, shortCode, self.cursor, self.conn)

        # A provisional code is required because short_code is NOT NULL and the
        # final code depends on the autoincremented id, which only exists after
        # the INSERT.
        placeholder = f"_pending{uuid4().hex}"
        data = self.db.save_shorten_url(url, placeholder, self.cursor, self.conn)

        shortCode = encode_base62(data["id"] + SHORT_CODE_OFFSET)
        self.db.update_short_code(placeholder, shortCode, self.cursor, self.conn)

        data["shortCode"] = shortCode

        return data

    def get_shorten_url(self, shortCode: str):
        # If the short code does not exist, neither does the URL.
        self._ensure_short_code_exists(shortCode)
        # Logic for retrieving the shortened URL details
        return self.db.get_shorten_url(shortCode, self.cursor)

    def update_shorten_url(self, shortCode: str, url: HttpUrl, new_shortCode: str | None):
        url = str(url)  # Convert HttpUrl to string
        # If the shortCode does not exist, return a 404 error
        self._ensure_short_code_exists(shortCode)

        if not (new_shortCode is None):
            # If the new shortCode is already registered, return a 409 error
            self._ensure_not_short_code_exists(new_shortCode)
        else:
            new_shortCode = shortCode
        # If the URL is already registered, return a 409 error
        self._ensure_url_not_exists(url)

        return self.db.update_shorten_url(shortCode, url, new_shortCode, self.cursor, self.conn)

    def delete_shorten_url(self, shortCode: str):
        # If the shortCode does not exist, return a 404 error
        self._ensure_short_code_exists(shortCode)

        self.db.delete_shorten_url(shortCode, self.cursor, self.conn)

    def get_shorten_url_stats(self, shortCode: str):
        # If the shortCode does not exist, return a 404 error
        self._ensure_short_code_exists(shortCode)

        return self.db.get_shorten_url_stats(shortCode, self.cursor)
    
    def access_url(self, shortCode):
        data = self.get_shorten_url(shortCode)
        url = data["url"]
        self.increment_clicks(shortCode)
        return url
    
    def increment_clicks(self, shortCode: str):
        self.db.increment_counter(shortCode, self.cursor, self.conn)
    
    def close(self):
        """
            Close the database connection held by this controller.
        """
        self.db.close(self.conn)
    
    def _ensure_short_code_exists(self, shortCode: str):
        """
            Raise a 404 if the short code does not exist.
        """
        if not self.db.short_code_exists(shortCode, self.cursor):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shortened URL not found."
            )
        
    def _ensure_not_short_code_exists(self, shortCode: str):
        """
            Raise a 409 if the short code does not exist.
        """
        if self.db.short_code_exists(shortCode, self.cursor):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Short Code is already registered."
            )

    def _ensure_url_not_exists(self, url: str):
        """
            Raise a 409 error if the URL already exists.
        """
        if self.db.url_exists(url, self.cursor):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="URL is already registered."
            )
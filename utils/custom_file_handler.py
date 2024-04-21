"""File handler with a few tweaks."""

from logging import FileHandler


class CustomFileHandler(FileHandler):
    """Custom logging file handler that adds an extra line at the EOF."""

    def close(self):
        if self.stream is not None:
            self.stream.write("")
        super().close()

from __future__ import annotations

import logging
import sys

FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(level=level, format=FORMAT, stream=sys.stdout)

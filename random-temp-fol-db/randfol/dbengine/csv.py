import csv
import logging
from collections import namedtuple

logger = logging.getLogger(__name__)

CSV_FILE = "./sensor_readings.csv"
CSV_FIELDS = ["timestamp", "sensor_id", "reading_value"]
SensorReading = namedtuple("SensorReading", CSV_FIELDS)


class CSV:
    def __init__(self, n_items=5):
        self._items_list = []
        self._n_items = n_items

        with open(CSV_FILE, "w") as csv_file:
            writer = csv.writer(csv_file)
            # Write header
            writer.writerow(CSV_FIELDS)

    def store(self, item: SensorReading):
        self._items_list.append(item)
        logger.info("Value appended to the CSV items list")

        if len(self._items_list) >= self._n_items:
            self._persist()

    def _persist(self):
        with open(CSV_FILE, "a") as csv_file:
            writer = csv.writer(csv_file)
            for item in self._items_list:
                writer.writerow(item)

        logger.info("Value correctly stored into CSV")
        self._items_list.clear()

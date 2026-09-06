from typing import Dict, Any, List, Optional
from collections import deque


class StockClassification:
    AVAILABLE = "AVAILABLE"
    LOW_STOCK = "LOW STOCK"
    EMPTY = "EMPTY"


def calculate_occupancy(detected_count: int, expected_capacity: int) -> float:
    """Calculates occupancy ratio capped at 1.0."""
    if expected_capacity <= 0:
        return 0.0
    return min(1.0, round(float(detected_count) / float(expected_capacity), 4))


def classify_stock_status(
    detected_count: int,
    expected_capacity: int,
    low_stock_threshold: float = 0.35,
    empty_threshold: float = 0.05
) -> Dict[str, Any]:
    """
    Classifies shelf stock level based on PRD Section 13 logic:
    IF detected_count == 0 (or occupancy_ratio <= empty_threshold):
        STATUS = EMPTY
    ELSE IF occupancy_ratio <= low_stock_threshold:
        STATUS = LOW STOCK
    ELSE:
        STATUS = AVAILABLE
    """
    occupancy_ratio = calculate_occupancy(detected_count, expected_capacity)

    if detected_count == 0 or occupancy_ratio <= empty_threshold:
        status = StockClassification.EMPTY
        severity = "CRITICAL"
    elif occupancy_ratio <= low_stock_threshold:
        status = StockClassification.LOW_STOCK
        severity = "WARNING"
    else:
        status = StockClassification.AVAILABLE
        severity = "INFO"

    return {
        "status": status,
        "occupancy_ratio": occupancy_ratio,
        "detected_count": detected_count,
        "expected_capacity": expected_capacity,
        "severity": severity,
        "is_alert_condition": status in [StockClassification.EMPTY, StockClassification.LOW_STOCK]
    }


class TemporalConfirmationFilter:
    """
    Temporal confirmation filter to prevent alert flickering on momentary video/webcam occlusion.
    Requires the condition to persist for N consecutive frames before transitioning state.
    """
    def __init__(self, window_size: int = 3):
        self.window_size = window_size
        self._history: Dict[int, deque] = {}
        self._confirmed: Dict[int, str] = {}

    def update(self, shelf_id: int, current_status: str) -> str:
        if shelf_id not in self._history:
            self._history[shelf_id] = deque(maxlen=self.window_size)
            self._confirmed[shelf_id] = current_status

        self._history[shelf_id].append(current_status)

        # If all N entries in the window match current_status, update confirmed status
        if len(self._history[shelf_id]) == self.window_size:
            if all(s == current_status for s in self._history[shelf_id]):
                self._confirmed[shelf_id] = current_status

        return self._confirmed.get(shelf_id, current_status)

    def reset(self, shelf_id: Optional[int] = None):
        if shelf_id is not None:
            self._history.pop(shelf_id, None)
            self._confirmed.pop(shelf_id, None)
        else:
            self._history.clear()
            self._confirmed.clear()


# Global temporal filter instance with default 3-frame confirmation window
shelf_temporal_filter = TemporalConfirmationFilter(window_size=3)

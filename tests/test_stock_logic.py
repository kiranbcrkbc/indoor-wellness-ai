import pytest
from backend.app.logic.stock_logic import (
    calculate_occupancy, classify_stock_status, StockClassification, TemporalConfirmationFilter
)


def test_calculate_occupancy():
    # Standard capacity
    assert calculate_occupancy(4, 10) == 0.4
    assert calculate_occupancy(10, 10) == 1.0
    # Overcapacity capped at 1.0
    assert calculate_occupancy(15, 10) == 1.0
    # Zero or negative capacity handled safely
    assert calculate_occupancy(5, 0) == 0.0
    assert calculate_occupancy(0, 10) == 0.0


def test_classify_stock_status_available():
    # 8 out of 10 items (80% occupancy, low_stock=0.35, empty=0.05)
    res = classify_stock_status(8, 10, low_stock_threshold=0.35, empty_threshold=0.05)
    assert res["status"] == StockClassification.AVAILABLE
    assert res["severity"] == "INFO"
    assert res["is_alert_condition"] is False
    assert res["occupancy_ratio"] == 0.8


def test_classify_stock_status_low_stock():
    # 3 out of 10 items (30% occupancy <= 0.35 and > 0.05)
    res = classify_stock_status(3, 10, low_stock_threshold=0.35, empty_threshold=0.05)
    assert res["status"] == StockClassification.LOW_STOCK
    assert res["severity"] == "WARNING"
    assert res["is_alert_condition"] is True
    assert res["occupancy_ratio"] == 0.3


def test_classify_stock_status_empty():
    # Zero items
    res_zero = classify_stock_status(0, 10, low_stock_threshold=0.35, empty_threshold=0.05)
    assert res_zero["status"] == StockClassification.EMPTY
    assert res_zero["severity"] == "CRITICAL"
    assert res_zero["is_alert_condition"] is True

    # 0 items out of 20 (occupancy 0% <= 0.05)
    res_empty_thresh = classify_stock_status(0, 20, low_stock_threshold=0.35, empty_threshold=0.05)
    assert res_empty_thresh["status"] == StockClassification.EMPTY


def test_temporal_confirmation_filter():
    filter_engine = TemporalConfirmationFilter(window_size=3)
    shelf_id = 1

    # Initially all frames are AVAILABLE
    filter_engine.update(shelf_id, StockClassification.AVAILABLE)
    filter_engine.update(shelf_id, StockClassification.AVAILABLE)
    assert filter_engine.update(shelf_id, StockClassification.AVAILABLE) == StockClassification.AVAILABLE

    # Frame 1: Transient occlusion (EMPTY) - should NOT immediately trigger confirmed EMPTY
    assert filter_engine.update(shelf_id, StockClassification.EMPTY) != StockClassification.EMPTY or len(filter_engine._history[shelf_id]) < 3

    # Frame 2: Still EMPTY
    filter_engine.update(shelf_id, StockClassification.EMPTY)

    # Frame 3: Confirmed EMPTY across all 3 consecutive frames
    confirmed = filter_engine.update(shelf_id, StockClassification.EMPTY)
    assert confirmed == StockClassification.EMPTY

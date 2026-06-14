from fastapi import APIRouter, Query, Depends
from datetime import datetime, timedelta
from typing import Optional
from data_manager import get_db_connection

router = APIRouter()

@router.get("/summary")
def get_report_summary(
    period: str = Query("weekly", pattern="^(daily|weekly|monthly|yearly|custom)$"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    conn = get_db_connection()
    try:
        now = datetime.now()
        if period == "daily":
            start_dt = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_dt = now
        elif period == "weekly":
            start_dt = now - timedelta(days=7)
            end_dt = now
        elif period == "monthly":
            start_dt = now - timedelta(days=30)
            end_dt = now
        elif period == "yearly":
            start_dt = now - timedelta(days=365)
            end_dt = now
        elif period == "custom" and start_date and end_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        else:
            # fallback to weekly
            start_dt = now - timedelta(days=7)
            end_dt = now
            
        start_str = start_dt.strftime("%Y-%m-%d %H:%M:%S")
        end_str = end_dt.strftime("%Y-%m-%d %H:%M:%S")
        
        # 1. Total Feed
        feed_query = conn.execute(
            "SELECT SUM(feed_weight_kg) as total FROM feed_logs WHERE date >= ? AND date <= ?",
            (start_dt.strftime("%Y-%m-%d"), end_dt.strftime("%Y-%m-%d"))
        ).fetchone()
        total_feed = feed_query["total"] if feed_query["total"] else 0.0

        # 2. Weight logic (starting, latest, gain, production value)
        weights = conn.execute(
            "SELECT maggot_weight_kg FROM weight_logs WHERE date >= ? AND date <= ? ORDER BY date ASC",
            (start_dt.strftime("%Y-%m-%d"), end_dt.strftime("%Y-%m-%d"))
        ).fetchall()
        
        starting_weight = weights[0]["maggot_weight_kg"] if weights else 0.0
        latest_weight = weights[-1]["maggot_weight_kg"] if weights else 0.0
        weight_gain = max(0.0, latest_weight - starting_weight)
        estimated_production_value = weight_gain * 7000  # Assume Rp 7000 / kg

        # 3. Sensor averages
        sensor_avg = conn.execute(
            "SELECT AVG(temperature) as avg_temp, AVG(humidity) as avg_hum FROM sensor_logs WHERE created_at >= ? AND created_at <= ?",
            (start_str, end_str)
        ).fetchone()
        avg_temp = sensor_avg["avg_temp"] if sensor_avg["avg_temp"] else 0.0
        avg_hum = sensor_avg["avg_hum"] if sensor_avg["avg_hum"] else 0.0

        # 4. Alert count
        alert_count = conn.execute(
            "SELECT COUNT(*) as count FROM alerts WHERE created_at >= ? AND created_at <= ?",
            (start_str, end_str)
        ).fetchone()["count"]

        # 5. Chart data (weights)
        chart_data = conn.execute(
            "SELECT date, maggot_weight_kg FROM weight_logs WHERE date >= ? AND date <= ? ORDER BY date ASC",
            (start_dt.strftime("%Y-%m-%d"), end_dt.strftime("%Y-%m-%d"))
        ).fetchall()

        return {
            "period": period,
            "metrics": {
                "total_feed": round(total_feed, 2),
                "starting_weight": round(starting_weight, 2),
                "latest_weight": round(latest_weight, 2),
                "weight_gain": round(weight_gain, 2),
                "estimated_production_value": estimated_production_value,
                "average_temperature": round(avg_temp, 2),
                "average_humidity": round(avg_hum, 2),
                "alert_count": alert_count
            },
            "chart_data": [dict(c) for c in chart_data]
        }
    finally:
        conn.close()

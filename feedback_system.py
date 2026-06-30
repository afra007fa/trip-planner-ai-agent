import json
import os
from datetime import datetime

FILE = "data/feedback.jsonl"

os.makedirs("data", exist_ok=True)


def save_feedback(
        city,
        poi_id,
        name,
        vote):

    record = {
        "timestamp":
            datetime.now().isoformat(),
        "city":
            city,
        "poi_id":
            poi_id,
        "name":
            name,
        "vote":
            vote
    }

    with open(
            FILE,
            "a",
            encoding="utf-8") as f:

        f.write(
            json.dumps(record)
            + "\n"
        )


def get_boost_score(
        city,
        poi_id):

    if not os.path.exists(FILE):
        return 0

    score = 0

    with open(
            FILE,
            "r",
            encoding="utf-8") as f:

        for line in f:

            try:

                record = json.loads(line)

                if (
                    record["city"] == city
                    and
                    str(record["poi_id"])
                    ==
                    str(poi_id)
                ):

                    if record["vote"] == "up":
                        score += 0.25
                    else:
                        score -= 0.35

            except:
                pass

    return score


def get_feedback_stats():

    if not os.path.exists(FILE):
        return {}

    stats = {}

    with open(
            FILE,
            "r",
            encoding="utf-8") as f:

        for line in f:

            try:

                r = json.loads(line)

                key = (
                    f"{r['city']} - "
                    f"{r['name']}"
                )

                if key not in stats:
                    stats[key] = 0

                if r["vote"] == "up":
                    stats[key] += 1
                else:
                    stats[key] -= 1

            except:
                pass

    return stats
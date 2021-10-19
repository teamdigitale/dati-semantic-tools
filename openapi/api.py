import sqlite3
from functools import lru_cache

import connexion
import pandas as pd
from sqlalchemy import create_engine
from werkzeug.exceptions import NotFound


def initdb(table_name):
    df = pd.read_csv(f"{table_name}.csv", index_col="op_code")
    engine = create_engine("sqlite:///datastore.db", echo=False)
    df.to_sql(f"{table_name}", con=engine, if_exists="replace")


initdb("countries")
db = create_engine("sqlite:///datastore.db", echo=True)


def get_status():
    return 200


@lru_cache(maxsize=128)
def list_tables():
    cur = db.execute(
        """SELECT name FROM sqlite_schema WHERE type ='table' AND name NOT LIKE 'sqlite_%';"""
    )
    return [x for (x,) in cur.fetchall()]


def list_vocabularies():
    ret = {"entries": [{"href": table_name} for table_name in list_tables()]}

    return ret


def test_list_vocabularies():
    assert "entries" in list_vocabularies()


def list_entries(vocabulary_id, limit=100, cursor="", **params):
    if vocabulary_id not in list_tables():
        raise NotFound(f"Vocabulary: {vocabulary_id}")

    entries = db.execute(
        f"""SELECT * FROM {vocabulary_id}
        WHERE op_code >= ?
        LIMIT {limit}""",
        (cursor,),
    )
    # Format entries as dictionaries.
    entries.cursor.row_factory = sqlite3.Row
    ret = entries.cursor.fetchall()
    ret = [dict(x) for x in ret] if ret else []
    return {
        "entries": ret,
        "count": len(ret),
        "last": next(iter(ret[-1].values())) if ret else "",
    }


def test_list_entries():
    ret = list_entries("countries", 10)
    assert len(ret["entries"]) == 10


def get_entry(vocabulary_id, entry_id):
    if vocabulary_id not in list_tables():
        raise NotFound(f"Vocabulary: {vocabulary_id}")

    entries = db.execute(
        f"""SELECT * FROM {vocabulary_id} WHERE op_code = ?""", (entry_id,)
    )

    entries.cursor.row_factory = sqlite3.Row
    ret = entries.cursor.fetchone()
    if not ret:
        raise NotFound
    return dict(ret)


def test_get_entry():
    ret = get_entry("countries", "ITA")
    assert ret.get("label_en") == "Italy"


if __name__ == "__main__":
    app = connexion.FlaskApp(__name__)
    app.add_api("vocabularies.yaml", validate_responses=True)
    app.run(port=8080)

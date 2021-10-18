import connexion
import pandas as pd
from sqlalchemy import create_engine

vocabularies = {"countries": pd.read_csv("countries.csv", index_col="op_code")}


def initdb(table_name):
    df = pd.read_csv(f"{table_name}.csv", index_col="op_code")
    engine = create_engine("sqlite:///datastore.db", echo=False)
    df.to_sql(f"{table_name}", con=engine, if_exists="replace")


initdb("countries")
db = create_engine("sqlite:///datastore.db", echo=True)


def get_status():
    return 200


def list_vocabularies():
    cur = db.execute(
        """SELECT name FROM sqlite_schema WHERE type ='table' AND name NOT LIKE 'sqlite_%';"""
    )
    ret = {"entries": [{"href": table_name} for (table_name,) in cur.fetchall()]}

    return ret


def test_list_vocabularies():
    assert "entries" in list_vocabularies()


def list_entries(vocabulary_id):
    v = vocabularies.get(vocabulary_id)
    if v is None:
        return 404

    return {"entries": v.to_dict("records")}


def get_entry(vocabulary_id, entry_id):
    v = vocabularies.get(vocabulary_id)
    if v is None:
        return 404

    record = v[v.index == entry_id]

    if record.empty:
        return 404

    return record.to_dict("records")[0]


app = connexion.FlaskApp(__name__)
app.add_api("vocabularies.yaml")
app.run(port=8080)

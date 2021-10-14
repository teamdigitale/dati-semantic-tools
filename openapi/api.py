import connexion
import pandas as pd

vocabularies = {"countries": pd.read_csv("countries.csv", index_col="op_code")}


def get_status():
    return 200


def list_vocabularies():
    return {"href": "countries"}


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

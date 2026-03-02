import pandas as pd
from ml_data import df_to_records, load_data
from schemas import InferenceRecord


def make_df(rows: list[dict]) -> pd.DataFrame:
    """Return a DataFrame built from a list of row dicts.

    This helper avoids the awkwardness of trying to merge column-wise overrides
    of different lengths.  The caller can simply pass the exact rows they want
    to test.
    """
    return pd.DataFrame(rows)


def test_drop_missing_id():
    df = make_df(
        [
            {"example_id": None},
            {"example_id": 2},
        ]
    )
    records = df_to_records(df)
    assert len(records) == 1
    assert records[0].example_id == 2


def test_safe_casting():
    df = make_df(
        [
            {"example_id": 1, "input_tokens": None},
        ]
    )
    rec = df_to_records(df)[0]
    # missing token count should become default 0
    assert rec.input_tokens == 0

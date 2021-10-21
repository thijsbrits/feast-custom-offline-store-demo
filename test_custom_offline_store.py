import os
import pandas as pd
from datetime import datetime

from feast import FeatureStore

from feature_repo.repo import driver, driver_hourly_stats_view


def test_end_to_end():
    fs = FeatureStore("feature_repo/")

    try:
        # apply repository
        fs.apply([driver, driver_hourly_stats_view])

        # load data into online store (materialize uses offline store functionality)
        fs.materialize_incremental(end_date=datetime.now())

        entity_df = pd.DataFrame(
            {"driver_id": [1001], "event_timestamp": [datetime.now()]}
        )

        # Read features from offline store
        feature_vector = (
            fs.get_historical_features(
                features=["driver_hourly_stats:conv_rate"], entity_df=entity_df
            )
            .to_df()
            .to_dict()
        )
        conv_rate = feature_vector["conv_rate"][0]
        assert conv_rate > 0
    finally:
        # tear down feature store
        fs.teardown()


def test_cli():
    os.system("PYTHONPATH=$PYTHONPATH:/$(pwd) feast -c feature_repo apply")
    try:
        os.system(
            "PYTHONPATH=$PYTHONPATH:/$(pwd) feast -c feature_repo materialize-incremental 2021-08-19T22:29:28 > output"
        )
        with open("output", "r") as f:
            output = f.read()

        if "Pulling latest features from my offline store" not in output:
            raise Exception(
                'Failed to successfully use provider from CLI. See "output" for more details.'
            )
    finally:
        os.system("PYTHONPATH=$PYTHONPATH:/$(pwd) feast -c feature_repo teardown")

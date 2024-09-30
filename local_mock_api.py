"""
An unlocked version of the timeseries API intended for testing alternate inputs.
Mirrors the production timeseries API in the crucial respects, but won't be as fast.

ONLY works afer the first three variables in MockAPI.__init__ are populated.
"""

from typing import Tuple
import os

import pandas as pd


class MockApi:
    """Class that replicates the online API for testing purposes."""

    def __init__(self):
        """
        YOU MUST UPDATE THE FIRST THREE LINES of this method.
        They've been intentionally left in an invalid state.

        Variables to set:
            input_paths: a list of two or more paths to the csv files to be served
            group_id_column: the column that identifies which groups of rows the API should serve.
                A call to iter_test serves all rows of all dataframes with the current
                group ID value.
            export_group_id_column: if true, the dataframes iter_test serves will include
                the group_id_column values.
        """
        root_path = (
            os.curdir + "/predict-energy-behavior-of-prosumers/example_test_files/"
        )
        self.input_paths = [
            root_path + "test.csv",
            root_path + "revealed_targets.csv",
            root_path + "client.csv",
            root_path + "historical_weather.csv",
            root_path + "forecast_weather.csv",
            root_path + "electricity_prices.csv",
            root_path + "gas_prices.csv",
            root_path + "sample_submission.csv",
        ]

        # Not in the production API but added in the mock api for debugging purposes
        for path in self.input_paths:
            if not os.path.exists(path):
                raise FileNotFoundError(f"File not found: {path}")

        self.group_id_column = "data_block_id"
        self.export_group_id_column = False
        # iter_test is only designed to support at least two dataframes,
        # such as test and sample_submission
        assert len(self.input_paths) >= 2

        self._status = "initialized"
        self.predictions = []

    def iter_test(self) -> Tuple[pd.DataFrame]:  # type: ignore
        """
        Loads all of the dataframes specified in self.input_paths,
        then yields all rows in those dataframes that equal the current self.group_id_column value.
        """
        if self._status != "initialized":

            raise RuntimeError(
                "WARNING: the real API can only iterate over `iter_test()` once."
            )

        dataframes = []
        for pth in self.input_paths:
            dataframes.append(pd.read_csv(pth, low_memory=False))
        group_order = dataframes[0][self.group_id_column].drop_duplicates().tolist()
        dataframes = [df.set_index(self.group_id_column) for df in dataframes]

        for group_id in group_order:
            self._status = "prediction_needed"
            current_data = []
            for df in dataframes:
                cur_df = df.loc[group_id].copy()
                # returning single line dataframes from df.loc requires special handling
                if not isinstance(cur_df, pd.DataFrame):
                    cur_df = pd.DataFrame(
                        dict(zip(cur_df.index.values, cur_df.values)),
                        index=[group_id],
                    )
                    cur_df.index.name = self.group_id_column
                cur_df = cur_df.reset_index(drop=not self.export_group_id_column)
                current_data.append(cur_df)
            yield tuple(current_data)

            while self._status != "prediction_received":
                print(
                    "You must call `predict()` successfully"
                    "before you can continue with `iter_test()`",
                    flush=True,
                )
                yield None

        with open("submission.csv", "w", encoding="utf-8") as f_open:
            pd.concat(self.predictions).to_csv(f_open, index=False)
        self._status = "finished"

    def predict(self, user_predictions: pd.DataFrame):
        """
        Accepts and stores the user's predictions and unlocks iter_test once that is done
        """
        if self._status == "finished":
            raise RuntimeError(
                "You have already made predictions for the full test set."
            )
        if self._status != "prediction_needed":
            raise RuntimeError(
                "You must get the next test sample from `iter_test()` first."
            )
        if not isinstance(user_predictions, pd.DataFrame):
            raise TypeError("You must provide a DataFrame.")

        self.predictions.append(user_predictions)
        self._status = "prediction_received"


def make_env():
    """Function to initialize MockAPI environment.
    Replicates the online API initialization call.
    """
    return MockApi()

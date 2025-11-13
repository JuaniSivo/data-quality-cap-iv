import logging
import json
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd

P_DATA = Path("data")
P_EXT_DATA = P_DATA.joinpath("01_external")

P_CONFIGS = Path("configs")
P_DQR = P_CONFIGS.joinpath("data_quality_requirements.json")

with open(P_DQR, "r") as f:
    dqr = json.load(f)
    
PROD_DATA_TYPES = dqr.get("production")
COMP_DATA_TYPES = dqr.get("completion")

logger = logging.getLogger(__name__)

def dtype_change(df: pd.DataFrame, dtype_dict: Dict[str, Dict[str, str]]) -> pd.DataFrame:
    df_aux = df.copy(True)
    for col, value in dtype_dict.items():
        data_type = value["data_type"]

        # conversion to datetime
        if data_type == "datetime64[ns]":
            date_format = value["date_format"]
            df_aux[col] = pd.to_datetime(
                arg=df_aux[col],
                errors="coerce",
                format=date_format
            )

        # conversion to numbers
        if data_type.startswith(("float", "int")):
            df_aux[col] = pd.to_numeric(arg=df_aux[col], errors="coerce")

        # data type change in he DataFrame
        df_aux[col] = df_aux[col].astype(dtype=data_type, errors="raise")

    return df_aux

def calc_dataset_perc(df_bool: pd.DataFrame) -> np.float32:
    calc = df_bool.sum().sum() / df_bool.size
    calc = calc * 100
    return calc

def calc_column_perc(df_bool: pd.DataFrame) -> pd.Series:
    calc = df_bool.sum() / df_bool.shape[0]
    calc = calc * 100
    return calc

def calc_column_null_count(df_bool: pd.DataFrame) -> pd.Series:
    calc = df_bool.shape[0] - df_bool.sum()
    return calc

def completness(df: pd.DataFrame) -> Tuple[np.float32, pd.Series, pd.Series]:
    completness = ~df.isnull()
    a = calc_dataset_perc(completness)
    b = calc_column_perc(completness)
    c = calc_column_null_count(completness)

    return (a, b, c)

def validity(df: pd.DataFrame, dtype_dict: Dict[str, Dict[str, str]]) -> Tuple[np.float32, pd.Series, pd.Series]:
    df_aux = dtype_change(df, dtype_dict)
    validity = df_aux.isna() == df.isna()
    a = calc_dataset_perc(validity)
    b = calc_column_perc(validity)
    c = calc_column_null_count(validity)

    return (a, b, c)

def main():
    df_prod = pd.read_parquet(P_EXT_DATA.joinpath("production.parquet"))
    df_comp = pd.read_parquet(P_EXT_DATA.joinpath("completion.parquet"))
    
    print("-- COMPLETNESS --")
    print(completness(df_prod))
    
    print("-- Validity --")
    print(validity(df_prod, PROD_DATA_TYPES))

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    logger.debug("Debugging module dataset")
    main()
    logger.debug("Finished debugging module")
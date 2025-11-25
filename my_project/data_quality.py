import logging
import logging.handlers
import json
from pathlib import Path
from typing import Dict, Tuple, Any

import numpy as np
import pandas as pd

P_DATA = Path("data")
P_EXT_DATA = P_DATA.joinpath("01_external")

P_CONFIGS = Path("configs")
P_DQR = P_CONFIGS.joinpath("data_quality_requirements.json")

P_LOGS = Path("logs")
P_LOG_FILENAME = P_LOGS.joinpath("data_auality.log")

with open(P_DQR, "r") as f:
    dqr = json.load(f)
    
PROD_DQR = dqr.get("production")
COMP_DQR = dqr.get("completion")

DQR_TYPE = Dict[str, Dict[str, Any]] # {field: {required: true/false, "data_range": {"min":  2000}}}

logger = logging.getLogger(__name__)

class DataQualityRequirements():
    pass

class DataQualityAssessment():
    pass

def dtype_change(df: pd.DataFrame, dict_dqr: DQR_TYPE) -> pd.DataFrame:
    logger.debug("Starting to convert data types")
    df_aux = df.copy(True)
    for col, value in dict_dqr.items():
        data_type = value["data_type"]

        # conversion to datetime
        if data_type == "datetime64[ns]":
            date_format = value["date_format"]
            df_aux[col] = pd.to_datetime(
                arg=df_aux[col],
                errors="coerce",
                format=date_format
            )
            logger.debug(f"Converted {col} to datetime")

        # conversion to numbers
        if data_type.startswith(("float", "int")):
            df_aux[col] = pd.to_numeric(arg=df_aux[col], errors="coerce")
            logger.debug(f"Converted {col} to numeric")

        # data type change in he DataFrame
        df_aux[col] = df_aux[col].astype(dtype=data_type, errors="raise")
        logger.debug(f"Converted {col} to numeric")

    logger.debug("All data types converted")
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
    logger.debug(f"Completeness: calculated mask for all columns")
    a = calc_dataset_perc(completness)
    b = calc_column_perc(completness)
    c = calc_column_null_count(completness)
    logger.debug("COMPLETENESS metrics calculated")

    return (a, b, c)

def valid_ranges_mask(df: pd.DataFrame, dict_dqr: DQR_TYPE) -> pd.DataFrame:
    df_aux = df.copy(True)
    df_validity = df == df
    df_validity.loc[:, :] = True
    for col, value in dict_dqr.items():
        if "data_range" in value.keys():
            data_range = value["data_range"]
            missing = df_aux[col].isna()
            if "min" in data_range.keys():
                validity = df_aux[col] >= data_range["min"]
                validity = validity | missing
                df_validity.loc[:, col] = df_validity.loc[:, col] & validity
                logger.debug(f"Validity range: calculated mask for {col}. Minimum: {data_range["min"]}")
            if "max" in data_range.keys():
                validity = df_aux[col] <= data_range["max"]
                validity = validity | missing
                df_validity.loc[:, col] = df_validity.loc[:, col] & validity
                logger.debug(f"Validity range: calculated mask for {col}. Maximum: {data_range["max"]}")
            if "set" in data_range.keys():
                data_range_set = data_range["set"]
                validity = df_aux[col].isin(data_range_set)
                validity = validity | missing
                df_validity.loc[:, col] = df_validity.loc[:, col] & validity
                logger.debug(f"Validity range: calculated mask for {col}. Set with {len(data_range_set)} items")

    return df_validity

def validity(df: pd.DataFrame, dict_dqr: DQR_TYPE) -> Tuple[np.float32, pd.Series, pd.Series]:
    df_aux = dtype_change(df, dict_dqr)
    validity_type = df_aux.isna() == df.isna()
    logger.debug(f"Validity data type: calculated mask for all columns")
    validity_range = valid_ranges_mask(df_aux, dict_dqr)
    logger.debug(f"Validity range: calculated mask for all columns")
    validity = validity_type & validity_range
    a = calc_dataset_perc(validity)
    b = calc_column_perc(validity)
    c = calc_column_null_count(validity)

    logger.debug("VALIDITY metrics calculated")
    return (a, b, c)

def main():
    df_prod = pd.read_parquet(P_EXT_DATA.joinpath("production.parquet"))
    df_comp = pd.read_parquet(P_EXT_DATA.joinpath("completion.parquet"))
    
    print("-- COMPLETNESS --")
    completness(df_prod)
    
    print("-- VALIDITY --")
    validity(df_prod, PROD_DQR)

if __name__ == "__main__":
    # logging.basicConfig(level=logging.DEBUG)

    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)12s - %(name)12s - %(levelname)12s - %(message)s')
    
    fh = logging.handlers.RotatingFileHandler(P_LOG_FILENAME, maxBytes=100000, backupCount=1)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)

    logger.info("Debugging module data quality")
    main()
    logger.info("Finished debugging module")
import logging
from pathlib import Path

import numpy as np
import pandas as pd

if Path("../data/01_external").exists: P_EXT_DATA = Path("../data/01_external")
if Path("data/01_external").exists: P_EXT_DATA = Path("data/01_external")

logger = logging.getLogger(__name__)

def completness_dataset_perc(df: pd.DataFrame) -> np.float32:
    completness = 1 - df.isnull().sum().sum() / df.size
    completness = completness * 100
    
    return completness

def completness_column_perc(df: pd.DataFrame) -> pd.Series:
    completness = 1 - df.isnull().sum() / df.shape[0]
    completness = completness * 100

    return completness

def completness_column_null_count(df: pd.DataFrame) -> pd.Series:
    return df.isnull().sum()

def main():
    df = pd.read_parquet(P_EXT_DATA.joinpath("production.parquet"))
    print(completness_dataset_perc(df))
    print(completness_column_perc(df))
    print(completness_column_null_count(df))

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    logger.debug("Debugging module dataset")
    main()
    logger.debug("Finished debugging module")
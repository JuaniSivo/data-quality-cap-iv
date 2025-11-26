import logging
import logging.handlers
from pathlib import Path

import pandas as pd

P_DATA = Path("data")
P_RAW_DATA = P_DATA.joinpath("02_raw")
P_INT_DATA = P_DATA.joinpath("03_interim")

P_LOGS = Path("logs")
P_LOG_FILENAME = P_LOGS.joinpath("etl_raw_int.log")

logger = logging.getLogger(__name__)


def extract():
    pass


def transform():
    pass


def load():
    pass


def main():
    # extract()
    # transform()
    # load()

    # Production dataset
    df_prod = pd.read_parquet(P_RAW_DATA.joinpath("production.parquet"))
    df_comp = pd.read_parquet(P_RAW_DATA.joinpath("completion.parquet"))

    df_prod_agg = df_prod.pivot_table(
        values=["caudal_pet", "caudal_gas", "tef"],
        index="idpozo",
        aggfunc={
            "caudal_pet": "max",
            "caudal_gas": "max",
            "tef": "sum",
        }
    )
    df_prod_agg.reset_index(inplace=True)
    df_prod_agg.rename(inplace=True, columns={
        "caudal_pet": "caudal_pet_max",
        "caudal_gas": "caudal_gas_max",
        "tef": "tef_acum",
    })

    df_prod_comp = pd.merge(
        left=df_prod_agg,
        right=df_comp,
        how="inner",
        on="idpozo"
    )

    df_prod_comp.to_parquet(P_INT_DATA.joinpath("prod_comp.parquet"))


if __name__ == "__main__":

    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)12s - %(name)8s - %(levelname)12s - %(message)s')
    
    fh = logging.handlers.RotatingFileHandler(P_LOG_FILENAME, maxBytes=100000, backupCount=1)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARNING)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)

    logger.info("Debugging module ETL external data to raw data")
    main()
    logger.info("Finished debugging ETL external data to raw data")
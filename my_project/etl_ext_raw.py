import logging
import logging.handlers
from pathlib import Path

import pandas as pd

P_DATA = Path("data")
P_EXT_DATA = P_DATA.joinpath("01_external")
P_RAW_DATA = P_DATA.joinpath("02_raw")

P_LOGS = Path("logs")
P_LOG_FILENAME = P_LOGS.joinpath("etl_ext_raw.log")

KEEP_COLUMNS_PROD = [
    "idpozo",
    "prod_pet",
    "prod_gas",
    "prod_agua",
    "tef",
    "fecha_data"
]

KEEP_COLUMNS_COMP = [
    "idpozo",
    "longitud_rama_horizontal_m",
    "cantidad_fracturas",
    "arena_bombeada_nacional_tn",
    "arena_bombeada_importada_tn",
    "agua_inyectada_m3"
]


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
    df_prod = pd.read_parquet(P_EXT_DATA.joinpath("production.parquet"))

    df_prod = df_prod.drop(columns=set(df_prod.columns)-set(KEEP_COLUMNS_PROD))
    df_prod.loc[:, ["prod_pet", "prod_gas", "prod_agua", "tef"]].clip(lower=0, inplace=True)
    df_prod.loc[:, ["tef"]].clip(upper=31, inplace=True)
    df_prod["caudal_pet"] = df_prod.loc[:, "prod_pet"] / df_prod.loc[:, "tef"]
    df_prod["caudal_gas"] = df_prod.loc[:, "prod_gas"] / df_prod.loc[:, "tef"]
    df_prod["caudal_agua"] = df_prod.loc[:, "prod_agua"] / df_prod.loc[:, "tef"]

    df_prod.to_parquet(P_RAW_DATA.joinpath("production.parquet"))

    # Completion dataset
    df_comp = pd.read_parquet(P_EXT_DATA.joinpath("completion.parquet"))

    df_comp = df_comp.drop(columns=set(df_comp.columns)-set(KEEP_COLUMNS_COMP))
    df_comp["arena_bombeada_tn"] = df_comp["arena_bombeada_nacional_tn"] + df_comp["arena_bombeada_importada_tn"]
    df_comp.drop(columns=["arena_bombeada_nacional_tn", "arena_bombeada_importada_tn"], inplace=True)
    df_comp.loc[:, ["longitud_rama_horizontal_m", "cantidad_fracturas", "arena_bombeada_tn", "agua_inyectada_m3"]].clip(lower=0, inplace=True)
    
    df_comp.to_parquet(P_RAW_DATA.joinpath("completion.parquet"))


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
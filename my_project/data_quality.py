import logging
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd

if Path("../data/01_external").exists: P_EXT_DATA = Path("../data/01_external")
if Path("data/01_external").exists: P_EXT_DATA = Path("data/01_external")
PROD_DATA_TYPES = {
    "idempresa": {"type": "string"},
    "anio": {"type": "int16"},
    "mes": {"type": "int8"},
    "idpozo": {"type": "int32"},
    "prod_pet": {"type": "float32"},
    "prod_gas": {"type": "float32"},
    "prod_agua": {"type": "float32"},
    "iny_agua": {"type": "float32"},
    "iny_gas": {"type": "float64"},
    "iny_co2": {"type": "float64"},
    "iny_otro": {"type": "float64"},
    "tef": {"type": "float32"},
    "vida_util": {"type": "float32"},
    "tipoextraccion": {"type": "string"},
    "tipoestado": {"type": "string"},
    "tipopozo": {"type": "string"},
    "observaciones": {"type": "string"},
    "fechaingreso": {"type": "datetime64[ns]", "format": "%Y-%m-%d %H:%M:%S.%f"},
    "rectificado": {"type": "bool"},
    "habilitado": {"type": "bool"},
    "idusuario": {"type": "int64"},
    "empresa": {"type": "string"},
    "sigla": {"type": "string"},
    "formprod": {"type": "string"},
    "profundidad": {"type": "float32"},
    "formacion": {"type": "string"},
    "idareapermisoconcesion": {"type": "string"},
    "areapermisoconcesion": {"type": "string"},
    "idareayacimiento": {"type": "string"},
    "areayacimiento": {"type": "string"},
    "cuenca": {"type": "string"},
    "provincia": {"type": "string"},
    "coordenadax": {"type": "float32"},
    "coordenaday": {"type": "float32"},
    "tipo_de_recurso": {"type": "string"},
    "proyecto": {"type": "string"},
    "clasificacion": {"type": "string"},
    "subclasificacion": {"type": "string"},
    "sub_tipo_recurso": {"type": "string"},
    "fecha_data": {"type": "datetime64[ns]", "format": "%Y-%m-%d"}
}
COMP_DATA_TYPES = {
    "id_base_fractura_adjiv": {"type": "int32"},
    "idpozo": {"type": "int32"},
    "sigla": {"type": "string"},
    "cuenca": {"type": "string"},
    "areapermisoconcesion": {"type": "string"},
    "yacimiento": {"type": "string"},
    "formacion_productiva": {"type": "string"},
    "tipo_reservorio": {"type": "string"},
    "subtipo_reservorio": {"type": "string"},
    "longitud_rama_horizontal_m": {"type": "float32"},
    "cantidad_fracturas": {"type": "int8"},
    "tipo_terminacion": {"type": "string"},
    "arena_bombeada_nacional_tn": {"type": "float32"},
    "arena_bombeada_importada_tn": {"type": "float32"},
    "agua_inyectada_m3": {"type": "float64"},
    "co2_inyectado_m3": {"type": "float64"},
    "presion_maxima_psi": {"type": "float64"},
    "potencia_equipos_fractura_hp": {"type": "float64"},
    "fecha_inicio_fractura": {"type": "datetime64[ns]", "format": "%Y-%m-%d"},
    "fecha_fin_fractura": {"type": "datetime64[ns]", "format": "%Y-%m-%d"},
    "fecha_data": {"type": "datetime64[ns]", "format": "%Y-%m-%d %H:%M:%S.%f"},
    "anio_if": {"type": "int16"},
    "mes_if": {"type": "int8"},
    "anio_ff": {"type": "int16"},
    "mes_ff": {"type": "int8"},
    "anio_carga": {"type": "int16"},
    "mes_carga": {"type": "int8"},
    "empresa_informante": {"type": "string"},
    "mes": {"type": "int8"},
    "anio": {"type": "int16"},
}

logger = logging.getLogger(__name__)

def dtype_change(df: pd.DataFrame, dtype_dict: Dict[str, Dict[str, str]]) -> pd.DataFrame:
    df_aux = df.copy(True)
    for col, value in dtype_dict.items():
        if value["type"] == "datetime64[ns]":
            df_aux[col] = pd.to_datetime(df_aux[col], errors="coerce", format=value["format"])

        if value["type"].startswith(("float", "int")):
            df_aux[col] = pd.to_numeric(df_aux[col], errors="coerce")

        df_aux[col] = df_aux[col].astype(dtype=value["type"], errors="raise")

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
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
P_DQR_PROD = P_CONFIGS.joinpath("dqr_production.json")
P_DQR_COMP = P_CONFIGS.joinpath("dqr_completion.json")
P_DQR_EXAMPLE = P_CONFIGS.joinpath("dqr_example.json")

P_LOGS = Path("logs")
P_LOG_FILENAME = P_LOGS.joinpath("data_quality.log")

DQR_TYPE = Dict[str, Dict[str, Any]] # {field: {required: true/false, "data_range": {"min":  2000}}}

logger = logging.getLogger(__name__)

class DataQualityRequirements:

    def __init__(self, dqr_dict: dict = dict()) -> None:
        self._dqr_dict = dict()
        self._set_dqr_dict(dqr_dict)


    def _get_dqr_dict(self) -> dict:
        if isinstance(self._dqr_dict, dict):
            return self._dqr_dict
        else:
            logger.warning("The data quality requirements dict is not a dict instance. Returning an empty dict.")
            return dict()
        

    def _set_dqr_dict(self, dqr_dict: dict) -> None:
        if isinstance(dqr_dict, dict):
            if self.valid_dict():
                self._dqr_dict = dqr_dict
            else:
                logger.error("Invalid data quality requirements dictionary")
        else:
            logger.error("The argument passed is not a dict instance")

    
    def load_from_json(self, path: Path | str):
        if isinstance(path, str): path = Path(path)
        if isinstance(path, Path):
            with open(path, "r") as f:
                dqr_dict = json.load(f)
            self._set_dqr_dict(dqr_dict)
        return self
    
    
    def valid_dict(self) -> bool:
        # TODO
        return True
    

    def get_column_dimension(self, column: str, dimension: str) -> dict:
        dqr_dict = self._get_dqr_dict()
        return dqr_dict[column][dimension]
    

    def group_by_dimension(self, dimension: str) -> dict:
        dqr_dict = self._get_dqr_dict()
        d = dict()

        for col in dqr_dict.keys():
            if dimension in dqr_dict[col].keys():
                d[col] = dqr_dict[col][dimension]
        
        return d
    

class DataQualityAssessment:

    def __init__(self,
                 dqr: DataQualityRequirements = DataQualityRequirements(),
                 dataset: pd.DataFrame = pd.DataFrame()) -> None:
        self._dqr = DataQualityRequirements()
        self._dataset = pd.DataFrame()
        self._dataset_typed = pd.DataFrame()
        self._set_dqr(dqr)
        self._set_dataset(dataset)


    def _get_dqr(self) -> DataQualityRequirements:
        if isinstance(self._dqr, DataQualityRequirements):
            return self._dqr
        else:
            logger.warning("The data quality requirements is not a DataQualityRequirements instance. Returning an empty DataQualityRequirements instance.")
            return DataQualityRequirements()
        

    def _get_dataset(self) -> pd.DataFrame:
        if isinstance(self._dataset, pd.DataFrame):
            return self._dataset
        else:
            logger.warning("The dataset is not a pandas.DataFrame instance. Returning an empty DataFrame.")
            return pd.DataFrame()
        

    def _get_dataset_typed(self) -> pd.DataFrame:
        if isinstance(self._dataset_typed, pd.DataFrame):
            return self._dataset_typed
        else:
            logger.warning("The dataset is not a pandas.DataFrame instance. Returning an empty DataFrame.")
            return pd.DataFrame()
        

    def _set_dqr(self, dqr: DataQualityRequirements) -> None:
        if isinstance(dqr, DataQualityRequirements):
            self._dqr = dqr
        else:
            logger.error(f"Data quality requirements is not {type(self)} instance")
            raise TypeError
        

    def _set_dataset(self, dataset: pd.DataFrame) -> None:
        if isinstance(dataset, pd.DataFrame):
            self._dataset = dataset
        else:
            logger.error(f"Dataset is not {type(pd.DataFrame)} instance nor None")
            raise TypeError
        

    def _set_dataset_typed(self, dataset: pd.DataFrame) -> None:
        if isinstance(dataset, pd.DataFrame):
            self._dataset_typed = dataset
        else:
            logger.error(f"Dataset is not {type(pd.DataFrame)} instance")
            raise TypeError
        
        
    def calc_dataset_success_perc(self, df_mask: pd.DataFrame) -> np.float32:
        calc = df_mask.sum().sum() / df_mask.size
        calc = calc * 100
        return calc
    

    def calc_column_success_perc(self, df_mask: pd.DataFrame) -> pd.Series:
        calc = df_mask.sum() / df_mask.shape[0]
        calc = calc * 100
        return calc
    

    def calc_column_bad_quality_count(self, df_mask: pd.DataFrame) -> pd.Series:
        calc = df_mask.shape[0] - df_mask.sum()
        return calc
    
    
    def dimension_metrics(self, df_mask: pd.DataFrame) -> Tuple[np.float32, pd.Series, pd.Series]:
        a = self.calc_dataset_success_perc(df_mask)
        b = self.calc_column_success_perc(df_mask)
        c = self.calc_column_bad_quality_count(df_mask)
        return (a, b, c)
    
    
    def is_complete(self) -> pd.DataFrame:
        df = self._get_dataset()
        return ~df.isnull()
    
    
    def is_valid(self) -> pd.DataFrame:
        return self.is_valid_type() & self.is_valid_range()
    
    
    def is_valid_type(self) -> pd.DataFrame:
        df = self._get_dataset()
        df_typed = self._get_dataset_typed()
        valid_type = df_typed.isna() == df.isna()
        incomplete = ~self.is_complete()
        return valid_type | incomplete
    
    
    def is_valid_range(self) -> pd.DataFrame:
        df_aux = self._get_dataset_typed().copy(True)
        dqr_validity = self._get_dqr().group_by_dimension("validity")
        df_validity = pd.DataFrame(True, index=df_aux.index, columns=df_aux.columns)

        # for col, value in dqr_dict.items():
        for col in dqr_validity.keys():
            if "data_range" in dqr_validity[col].keys():
                data_range = dqr_validity[col]["data_range"]
                column = df_aux[col]
                is_valid_masks = []
                
                if "min" in data_range.keys():
                    is_valid_masks.append(column >= data_range["min"])
                
                if "max" in data_range.keys():
                    is_valid_masks.append(column <= data_range["max"])
                
                if "set" in data_range.keys():
                    is_valid_masks.append(column.isin(data_range["set"]))
                
                for is_valid_mask in is_valid_masks:
                    df_validity.loc[:, col] = df_validity.loc[:, col] & is_valid_mask

        df_validity = df_validity | ~self.is_complete() | ~self.is_valid_type()
        return df_validity
        

    def assess_completeness(self) -> Tuple[np.float32, pd.Series, pd.Series]:
        completeness = self.is_complete()
        return self.dimension_metrics(completeness)
    
    
    def assess_validity(self) -> Tuple[np.float32, pd.Series, pd.Series]:
        validity = self.is_valid()
        return self.dimension_metrics(validity)
    

    def apply_data_types(self) -> pd.DataFrame:
        df_aux = self._get_dataset().copy(True)
        # dqr_dict = self._get_dqr()._get_dqr_dict()
        dqr_validity = self._get_dqr().group_by_dimension("validity")

        # for col, value in dqr_dict.items():
        for col in dqr_validity.keys():
            data_type = dqr_validity[col]["data_type"]

            # Conversion to datetime
            if data_type == "datetime64[ns]":
                date_format = dqr_validity[col]["date_format"]
                df_aux[col] = pd.to_datetime(
                    arg=df_aux[col],
                    errors="coerce",
                    format=date_format
                )
                logger.debug(f"Converted {col} to datetime")

            # Conversion to numbers
            if data_type.startswith(("float", "int")):
                df_aux[col] = pd.to_numeric(arg=df_aux[col], errors="coerce")
                logger.debug(f"Converted {col} to numeric")

            # Data type assignment
            df_aux[col] = df_aux[col].astype(dtype=data_type, errors="raise")
            logger.debug(f"Converted {col} to numeric")

        logger.debug("All data types converted")
        self._set_dataset_typed(df_aux)
        
        return df_aux
    

def main():
    # df_prod = pd.read_parquet(P_EXT_DATA.joinpath("production.parquet"))
    # df_comp = pd.read_parquet(P_EXT_DATA.joinpath("completion.parquet"))

    # dqr_prod = DataQualityRequirements().load_from_json(P_DQR_PROD)
    # dqr_comp = DataQualityRequirements().load_from_json(P_DQR_COMP)

    # dqa_prod = DataQualityAssessment(dqr_prod, df_prod)
    # dqa_comp = DataQualityAssessment(dqr_comp, df_comp)

    # dqas = [dqa_prod, dqa_comp]
    # for dqa in dqas:
    #     dqa.apply_data_types()
    #     print(dqa.assess_completeness()[2])
    #     print(dqa.assess_validity()[2])

    df_example = pd.read_csv(P_EXT_DATA.joinpath("example_mod.csv"), sep=";", decimal=",")
    dqr_example = DataQualityRequirements().load_from_json(P_DQR_EXAMPLE)
    dqa_example = DataQualityAssessment(dqr_example, df_example)
    dqa_example.apply_data_types()
    
    print(dqa_example.is_complete() & dqa_example.is_valid())


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

    logger.info("Debugging module data quality")
    main()
    logger.info("Finished debugging module")
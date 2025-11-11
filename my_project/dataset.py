import logging
import time
from pathlib import Path

import pandas as pd

if Path("../data/01_external").exists: P_EXT_DATA = Path("../data/01_external")
if Path("data/01_external").exists: P_EXT_DATA = Path("data/01_external")
URL_PRODUCTION = "http://datos.energia.gob.ar/dataset/c846e79c-026c-4040-897f-1ad3543b407c/resource/b5b58cdc-9e07-41f9-b392-fb9ec68b0725/download/produccin-de-pozos-de-gas-y-petrleo-no-convencional.csv"
URL_COMPLETION = "http://datos.energia.gob.ar/dataset/71fa2e84-0316-4a1b-af68-7f35e41f58d7/resource/2280ad92-6ed3-403e-a095-50139863ab0d/download/datos-de-fractura-de-pozos-de-hidrocarburos-adjunto-iv-actualizacin-diaria.csv"

logger = logging.getLogger(__name__)

def read_data(url: str) -> pd.DataFrame:
    """
    Read datasets from datos.energia.gob.ar.
    """

    logger.debug(f"Reading url {url}")
    start = time.time()
    df = pd.read_csv(
        filepath_or_buffer=url,
        sep=",",
        header=0,
        true_values=["t"],
        false_values=["f"],
        decimal=".",
        encoding="utf-8"
    )
    end = time.time()
    logger.debug(f"Dataset loaded to memory in {end-start:.4f} seconds")

    return df

def save_data(df: pd.DataFrame, folder_path: str | Path, filename: str) -> None:
    """
    Save DataFrame to parquet
    """
    
    p_folder = Path(folder_path)
    p_file = p_folder.joinpath(filename + ".parquet")

    if not p_folder.exists():
        logger.error(f"The folder \"{p_folder}\" does not exist. Cannot save file \"{filename}.parquet\"")
        return None
    
    if p_file.exists():
        repeat = True
        while repeat:
            r = input("\n> The file already exists. Overwrite? [y/n]:")
            if r in ["y", "n"]:
                repeat = False
            else:
                print(f"Your answer \"{r}\" is not supported. ", end="")
        print("")
        if r=="n": return None
        
    df.to_parquet(p_file)
    logger.debug(f"Dataset \"{filename}\" saved in \"{p_file}\"")
    
    return None

def main() -> None:
    
    for url, filename in zip([URL_PRODUCTION, URL_COMPLETION], ["production", "completion"]):
        save_data(
            df=read_data(url=url),
            folder_path=P_EXT_DATA,
            filename=filename
        )

    return None

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    logger.debug("Debugging module dataset")
    main()
    logger.debug("Finished debugging module")
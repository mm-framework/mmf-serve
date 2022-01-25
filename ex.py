import pickle
import time
import pandas
import mmf_meta as mmf
from mmf_meta.core import TARGETS


@mmf.target(
    description="Супер-функция",
    returns=mmf.DataFrame(out_format=mmf.DataFrameFormat.CSV),
)
def score(
    df: pandas.DataFrame = mmf.DataFrame(description="Описание df"),
    # other: dict = mmf.JsonFile(description="Описание other"),
):
    return df


@mmf.target(
    description="Другая супер-функция",
    returns=mmf.String(),
)
def other(
    inp=mmf.String(description="важный параметр"),
    another=mmf.Integer(description="еще один важный параметр"),
):
    time.sleep(30)
    return inp


mmf.artifact("some_file")


@mmf.artifact("other")
def model():
    with open("other", "br") as f:
        return pickle.load(f)

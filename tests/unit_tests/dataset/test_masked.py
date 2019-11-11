import itertools
import shutil
from typing import Optional, Tuple

import mock
import numpy as np
import py
import pytest

# from src.dataset.common import dataset_type
from src.dataset.masked import (
    generate_from_metadata, load_dataset, make_metadata
)
from src.asf_typing import MaskedDatasetMetadata

from .conftest import mock_gdal_open
from src.config import NETWORK_DEMS as dems


@pytest.fixture
def dataset_masked(tmpdir: py.path.local):
    dataset = "unittest_dataset"
    temp_dataset_dir = tmpdir.mkdir("datasets")

    shutil.copytree(
        "tests/data/datasets/sample_masked", temp_dataset_dir.join(dataset)
    )
    with mock.patch("src.dataset.common.DATASETS_DIR", temp_dataset_dir):
        yield dataset


@pytest.fixture
def metadata_masked() -> MaskedDatasetMetadata:
    return [("test_1.vh.x0_y0.tif", "test_1.vv.x0_y0.tif", "test_1.mask.x0_y0.tif"),
            ("test_2.vh.x0_y0.tif", "test_2.vv.x0_y0.tif", "test_2.mask.x0_y0.tif")]


def test_make_metadata(dataset_masked: str, tmpdir: py.path.local):
    train_metadata, test_metadata = make_metadata(dataset_masked)

    def abspath(*f: str) -> str:
        return tmpdir.join("datasets", dataset_masked, *f)

    assert train_metadata == [
        (
            abspath("train", "test_3.vh.x0_y0.tif"),
            abspath("train", "test_3.vv.x0_y0.tif"),
            abspath("train", "test_3.mask.x0_y0.tif"),
        ),
        (
            abspath("train", "test_4.vh.x0_y0.tif"),
            abspath("train", "test_4.vv.x0_y0.tif"),
            abspath("train", "test_4.mask.x0_y0.tif"),
        ),
    ]
    assert test_metadata == [
        (
            abspath("test", "test_1.vh.x0_y0.tif"),
            abspath("test", "test_1.vv.x0_y0.tif"),
            abspath("test", "test_1.mask.x0_y0.tif"),
        ),
        (
            abspath("test", "test_2.vh.x0_y0.tif"),
            abspath("test", "test_2.vv.x0_y0.tif"),
            abspath("test", "test_2.mask.x0_y0.tif"),
        ),
    ]


def generate_data(
    metadata: MaskedDatasetMetadata,
    img: np.ndarray,
    clip_range: Optional[Tuple[float, float]] = None
):
    with mock_gdal_open(img):
        return list(generate_from_metadata(metadata, clip_range=clip_range))


def test_generate_from_metadata(metadata_masked: MaskedDatasetMetadata):
    data = generate_data(metadata_masked, np.ones((dems, dems)))

    imgs = list(map(lambda x: x[0], data))
    masks = list(map(lambda x: x[1], data))
    for img in imgs:
        assert (img == np.ones((dems, dems, 2))).all()

    for mask in masks:
        assert (mask == np.ones((dems, dems, 1))).all()


def test_generate_from_metadata_clip_range(
    metadata_masked: MaskedDatasetMetadata
):
    data = generate_data(
        metadata_masked, np.ones((dems, dems)), clip_range=(0, 0.5)
    )

    imgs = list(map(lambda x: x[0], data))
    masks = list(map(lambda x: x[1], data))
    for img in imgs:
        assert (img == np.ones((dems, dems, 2)) / 2.0).all()

    for mask in masks:
        assert (mask == np.ones((dems, dems, 1))).all()


def test_generate_from_metadata_with_zeros(
    metadata_masked: MaskedDatasetMetadata
):
    assert generate_data(metadata_masked, np.zeros((dems, dems))) == []


def test_generate_from_metadata_with_nans(
    metadata_masked: MaskedDatasetMetadata
):
    assert generate_data(metadata_masked, np.zeros((dems, dems)) + np.nan) == []


def test_load_dataset(dataset_masked: str):
    with mock_gdal_open(np.ones((dems, dems))):
        train_iter, test_iter = load_dataset(dataset_masked)

    train = list(itertools.islice(train_iter, len(train_iter)))
    test = list(itertools.islice(test_iter, len(test_iter)))

    # Number of batches
    assert len(train) == 1
    assert len(test) == 2


# def test_dataset_type(dataset_masked: str):
#     assert dataset_type(dataset_masked) == ModelType.MASKED

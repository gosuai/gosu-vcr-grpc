import os
import logging
from functools import partial

import gosu_grpc.channel
import pytest
import yaml

from .vcr_channel import VcrRecordChannel, VcrPlaybackChannel

MARKER = "vcr_grpc"
logger = logging.getLogger(__name__)


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "vcr_grpc(): Mark the test as using GRPC cassettes."
    )


@pytest.fixture(autouse=True)
def _vcr_grpc_marker(request):
    marker = request.node.get_closest_marker(MARKER)
    if marker:
        request.getfixturevalue("vcr_grpc_cassette")


@pytest.fixture(scope="module")
def vcr_grpc_cassette_dir(request):
    test_dir = request.node.fspath.dirname
    return os.path.join(test_dir, "grpc_cassettes")


@pytest.fixture
def vcr_grpc_cassette_path(request, vcr_grpc_cassette_dir):
    return os.path.join(vcr_grpc_cassette_dir, f"{request.node.name}.yaml")


@pytest.fixture
def vcr_grpc_cassette(
    request, vcr_grpc_cassette_dir, vcr_grpc_cassette_path, monkeypatch
):
    if playback := os.path.exists(vcr_grpc_cassette_path):
        logger.debug(f"Using cassette {vcr_grpc_cassette_path} for playback")
        with open(vcr_grpc_cassette_path) as f:
            cassette = yaml.unsafe_load(f)
        channel_class = VcrPlaybackChannel
    else:
        logger.debug(f"Using cassette {vcr_grpc_cassette_path} for recording")
        cassette = []
        channel_class = VcrRecordChannel

    channel_factory = partial(
        channel_class, cassette_path=vcr_grpc_cassette_path, cassette=cassette
    )
    monkeypatch.setattr(gosu_grpc.channel, "Channel", channel_factory)

    yield
    # Unfortunately new pytest doesn't have ability
    # to check test status inside fixture.
    if not playback:
        os.makedirs(vcr_grpc_cassette_dir, exist_ok=True)
        data = yaml.dump(cassette)
        with open(vcr_grpc_cassette_path, "w") as f:
            f.write(data)
        logger.debug(f"Saved new cassette {vcr_grpc_cassette_path}")
        assert (
            True is False
        ), f"Cassette {vcr_grpc_cassette_path} is just recorded, failing the test"
    elif playback:
        assert (
            not cassette
        ), f"Cassette {vcr_grpc_cassette_path} has not played streams: {cassette}"

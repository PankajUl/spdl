import sys
import os
import subprocess

from spotdl import internals

import pytest


DUPLICATE_TRACKS_TEST_TABLE = [
    (
        (
            "https://open.spotify.com/track/2DGa7iaidT5s0qnINlwMjJ",
            "https://open.spotify.com/track/2DGa7iaidT5s0qnINlwMjJ",
        ),
        ("https://open.spotify.com/track/2DGa7iaidT5s0qnINlwMjJ",),
    ),
    (
        (
            "https://open.spotify.com/track/2DGa7iaidT5s0qnINlwMjJ",
            "",
            "https://open.spotify.com/track/3SipFlNddvL0XNZRLXvdZD",
        ),
        (
            "https://open.spotify.com/track/2DGa7iaidT5s0qnINlwMjJ",
            "https://open.spotify.com/track/3SipFlNddvL0XNZRLXvdZD",
        ),
    ),
    (
        (
            "ncs fade",
            "https://open.spotify.com/track/2DGa7iaidT5s0qnINlwMjJ",
            "",
            "ncs fade",
        ),
        ("ncs fade", "https://open.spotify.com/track/2DGa7iaidT5s0qnINlwMjJ"),
    ),
    (
        ("ncs spectre ", "  https://open.spotify.com/track/2DGa7iaidT5s0qnINlwMjJ", ""),
        ("ncs spectre", "https://open.spotify.com/track/2DGa7iaidT5s0qnINlwMjJ"),
    ),
]

STRING_IDS_TEST_TABLE = [
    (
        "https://open.spotify.com/artist/1feoGrmmD8QmNqtK2Gdwy8?si=_cVm-FBRQmi7VWML7E49Ig",
        "1feoGrmmD8QmNqtK2Gdwy8",
    ),
    (
        "https://open.spotify.com/artist/1feoGrmmD8QmNqtK2Gdwy8",
        "1feoGrmmD8QmNqtK2Gdwy8",
    ),
    ("spotify:artist:1feoGrmmD8QmNqtK2Gdwy8", "1feoGrmmD8QmNqtK2Gdwy8"),
    (
        "https://open.spotify.com/album/1d1l3UkeAjtM7kVTDyR8yp?si=LkVQLJGGT--Lh8BWM4MGvg",
        "1d1l3UkeAjtM7kVTDyR8yp",
    ),
    ("https://open.spotify.com/album/1d1l3UkeAjtM7kVTDyR8yp", "1d1l3UkeAjtM7kVTDyR8yp"),
    ("spotify:album:1d1l3UkeAjtM7kVTDyR8yp", "1d1l3UkeAjtM7kVTDyR8yp"),
    (
        "https://open.spotify.com/user/5kkyy50uu8btnagp30pobxz2f/playlist/3SFKRjUXm0IMQJMkEgPHeY?si=8Da4gbE2T9qMkd8Upg22ZA",
        "3SFKRjUXm0IMQJMkEgPHeY",
    ),
    (
        "https://open.spotify.com/playlist/3SFKRjUXm0IMQJMkEgPHeY?si=8Da4gbE2T9qMkd8Upg22ZA",
        "3SFKRjUXm0IMQJMkEgPHeY",
    ),
    (
        "https://open.spotify.com/playlist/3SFKRjUXm0IMQJMkEgPHeY",
        "3SFKRjUXm0IMQJMkEgPHeY",
    ),
    (
        "spotify:user:5kkyy50uu8btnagp30pobxz2f:playlist:3SFKRjUXm0IMQJMkEgPHeY",
        "3SFKRjUXm0IMQJMkEgPHeY",
    ),
    (
        "https://open.spotify.com/user/uqlakumu7wslkoen46s5bulq0",
        "uqlakumu7wslkoen46s5bulq0",
    ),
]


FROM_SECONDS_TEST_TABLE = [
    (35, "35"),
    (23, "23"),
    (158, "2:38"),
    (263, "4:23"),
    (4562, "1:16:02"),
    (26762, "7:26:02")
]


TO_SECONDS_TEST_TABLE = [
    ("0:23", 23),
    ("0:45", 45),
    ("2:19", 139),
    ("3:33", 213),
    ("7:38", 458),
    ("1:30:05", 5405),
]


def test_default_music_directory():
    if sys.platform.startswith("linux"):
        output = subprocess.check_output(["xdg-user-dir", "MUSIC"])
        expect_directory = output.decode("utf-8").rstrip()
    else:
        home = os.path.expanduser("~")
        expect_directory = os.path.join(home, "Music")

    directory = internals.get_music_dir()
    assert directory == expect_directory


class TestPathFilterer:
    def test_create_directory(self, tmpdir):
        expect_path = True
        global folder_path
        folder_path = os.path.join(str(tmpdir), "filter_this_folder")
        internals.filter_path(folder_path)
        is_path = os.path.isdir(folder_path)
        assert is_path == expect_path

    def test_remove_temp_files(self, tmpdir):
        expect_file = False
        file_path = os.path.join(folder_path, "pesky_file.temp")
        open(file_path, "a")
        internals.filter_path(folder_path)
        is_file = os.path.isfile(file_path)
        assert is_file == expect_file


@pytest.mark.parametrize("sec_duration, str_duration", FROM_SECONDS_TEST_TABLE)
def test_video_time_from_seconds(sec_duration, str_duration):
    duration = internals.videotime_from_seconds(sec_duration)
    assert duration == str_duration


@pytest.mark.parametrize("str_duration, sec_duration", TO_SECONDS_TEST_TABLE)
def test_get_seconds_from_video_time(str_duration, sec_duration):
    secs = internals.get_sec(str_duration)
    assert secs == sec_duration


@pytest.mark.parametrize("duplicates, expected", DUPLICATE_TRACKS_TEST_TABLE)
def test_get_unique_tracks(tmpdir, duplicates, expected):
    file_path = os.path.join(str(tmpdir), "test_duplicates.txt")
    with open(file_path, "w") as f:
        f.write("\n".join(duplicates))

    unique_tracks = internals.get_unique_tracks(file_path)
    assert tuple(unique_tracks) == expected


@pytest.mark.parametrize("input_str, expected_spotify_id", STRING_IDS_TEST_TABLE)
def test_extract_spotify_id(input_str, expected_spotify_id):
    spotify_id = internals.extract_spotify_id(input_str)
    assert spotify_id == expected_spotify_id

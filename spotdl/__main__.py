# ! Basic necessities to get the CLI running
import signal
import sys
import argparse
import os

# ! The actual download stuff
from spotdl.download.downloader import DownloadManager
from spotdl.search.spotifyClient import SpotifyClient
import spotdl.search.songGatherer as songGatherer

from spotdl.download import ffmpeg

# ! Usage is simple - call:
#   'python __main__.py <links, search terms, tracking files separated by spaces>
# ! Eg.
# !      python __main__.py
# !          https://open.spotify.com/playlist/37i9dQZF1DWXhcuQw7KIeM?si=xubKHEBESM27RqGkqoXzgQ
# !          'old gods of asgard Control'
# !          https://open.spotify.com/album/2YMWspDGtbDgYULXvVQFM6?si=gF5dOQm8QUSo-NdZVsFjAQ
# !          https://open.spotify.com/track/08mG3Y1vljYA6bvDt4Wqkj?si=SxezdxmlTx-CaVoucHmrUA
# !
# ! Well, yeah its a pretty long example but, in theory, it should work like a charm.
# !
# ! A '.spotdlTrackingFile' is automatically  created with the name of the first song in the
# ! playlist/album or the name of the song supplied. We don't really re re re-query YTM and Spotify
# ! as all relevant details are stored to disk.
# !
# ! Files are cleaned up on download failure.
# !
# ! All songs are normalized to standard base volume. the soft ones are made louder,
# ! the loud ones, softer.
# !
# ! The progress bar is synched across multiple-processes (4 processes as of now), getting the
# ! progress bar to synch was an absolute pain, each process knows how much 'it' progressed,
# ! but the display has to be for the overall progress so, yeah... that took time.
# !
# ! spotdl will show you its true speed on longer download's - so make sure you try
# ! downloading a playlist.
# !
# ! still yet to try and package this but, in theory, there should be no errors.
# !
# !                                                          - cheerio! (Michael)
# !
# ! P.S. Tell me what you think. Up to your expectations?

# ! Script Help
help_notice = """
To download a song run,
    spotdl [trackUrl]
    ex. spotdl https://open.spotify.com/track/0VjIjW4GlUZAMYd2vXMi3b?si=1stnMF5GSdClnIEARnJiiQ

To download a album run,
    spotdl [albumUrl]
    ex. spotdl https://open.spotify.com/album/4yP0hdKOZPNshxUOjY0cZj?si=AssgQQrVTJqptFe7X92jNg

To download a playlist, run:
    spotdl [playlistUrl]
    ex. spotdl https://open.spotify.com/playlist/37i9dQZF1E8UXBoz02kGID?si=oGd5ctlyQ0qblj_bL6WWow

To search for and download a song, run, with quotation marks:
Note: This is not accurate and often causes errors.
    spotdl [songQuery]
    ex. spotdl 'The Weeknd - Blinding Lights'

To resume a failed/incomplete download, run:
    spotdl [pathToTrackingFile]
    ex. spotdl 'The Weeknd - Blinding Lights.spotdlTrackingFile'

    .spotdlTrackingFiles are automatically created when a download starts and deleted on completion

You can queue up multiple download tasks by separating the arguments with spaces:
    spotdl [songQuery1] [albumUrl] [songQuery2] ... (order does not matter)
    ex. spotdl 'The Weeknd - Blinding Lights'
            https://open.spotify.com/playlist/37i9dQZF1E8UXBoz02kGID?si=oGd5ctlyQ0qblj_bL6WWow ...

You can use the --debug-termination flag to figure out where in the code spotdl got stuck.

spotDL downloads up to 4 songs in parallel, so for a faster experience,
download albums and playlist, rather than tracks.
"""


def console_entry_point():
    """
    This is where all the console processing magic happens.
    Its super simple, rudimentary even but, it's dead simple & it works.
    """
    arguments = parse_arguments()

    if (
        ffmpeg.has_correct_version(
            arguments.ignore_ffmpeg_version, arguments.ffmpeg or "ffmpeg"
        )
        is False
    ):
        sys.exit(1)

    SpotifyClient.init(
        client_id="5f573c9620494bae87890c0f08a60293",
        client_secret="212476d9b0f3472eaa762d90b19b0ba8",
    )

    if arguments.path:
        if not os.path.isdir(arguments.path):
            sys.exit("The output directory doesn't exist.")
        print(f"Will download to: {os.path.abspath(arguments.path)}")
        os.chdir(arguments.path)

    with DownloadManager(arguments.ffmpeg) as downloader:
        if not arguments.debug_termination:

            def gracefulExit(signal, frame):
                downloader.displayManager.close()
                sys.exit(0)

            signal.signal(signal.SIGINT, gracefulExit)
            signal.signal(signal.SIGTERM, gracefulExit)

        songObjList = []
        for request in arguments.query:
            if request.endswith(".spotdlTrackingFile"):
                print("Preparing to resume download...")
                downloader.resume_download_from_tracking_file(request)
            else:
                songObjList.extend(songGatherer.from_query(request))
                print()

        if len(songObjList) > 0:
            downloader.download_multiple_songs(songObjList)


def parse_arguments():
    parser = argparse.ArgumentParser(
        prog="spotdl",
        description=help_notice,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("query", type=str, nargs="+", help="URL/String for a song/album/playlist")
    parser.add_argument("--debug-termination", action="store_true")
    parser.add_argument("-o", "--output", help="Output directory path", dest="path")
    parser.add_argument("-f", "--ffmpeg", help="Path to ffmpeg", dest="ffmpeg")
    parser.add_argument(
        "--ignore-ffmpeg-version", help="Ignore ffmpeg version", action="store_true"
    )

    return parser.parse_args()


if __name__ == "__main__":
    console_entry_point()

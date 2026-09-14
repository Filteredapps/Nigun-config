import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import generate_home_feed as feed


class FeedRegressionTests(unittest.TestCase):
    def setUp(self):
        self.artist = {"name": "Allowed", "channelId": "UC" + "a" * 22, "genres": ["pop"]}
        self.cache = {}
        self.report = feed.initial_report(1)

    def search(self, aliases=None):
        return feed.search_itunes_by_artist_and_title(
            aliases or ["Allowed"], "Song", "SINGLE", self.cache, self.report)

    def test_outage_is_not_permanently_cached_as_no_results(self):
        with patch.object(feed, "itunes_request", side_effect=[None, {"results": []}]) as request:
            self.assertEqual([], self.search())
            self.assertEqual({}, self.cache)
            self.assertEqual([], self.search())
            self.assertEqual(2, request.call_count)
            self.search()
            self.assertEqual(2, request.call_count)

    def test_old_empty_cache_entries_are_retried(self):
        self.cache[feed.cache_key_for_search(["Allowed"], "Song", "SINGLE")] = []
        with patch.object(feed, "itunes_request", return_value={"results": []}) as request:
            self.search()
            request.assert_called_once()

    def test_budget_exhaustion_does_not_cache_an_incomplete_search(self):
        with patch.object(feed, "MAX_ITUNES_LOOKUPS_TOTAL", 1), patch.object(
            feed, "itunes_request", return_value={"results": []}
        ):
            self.search(["Allowed", "Alias"])
        self.assertEqual({}, self.cache)

    def test_distinct_tracks_in_one_album_are_not_collapsed(self):
        tracks = [{"trackId": i, "collectionId": 42, "wrapperType": "track"} for i in (1, 2)]
        with patch.object(feed, "itunes_request", return_value={"results": tracks}), patch.object(
            feed, "select_best_itunes_candidate", return_value=(None, 0, None)
        ):
            self.assertEqual(2, len(self.search()))

    def test_expired_successful_cache_is_refreshed(self):
        self.cache[feed.cache_key_for_search(["Allowed"], "Song", "SINGLE")] = {
            "results": [{"trackId": 1}], "expiresAt": 0}
        with patch.object(feed, "itunes_request", return_value={"results": []}) as request:
            self.search()
            request.assert_called_once()

    def test_missing_youtube_video_id_is_retried(self):
        cache = {"MPREtest": {"firstVideoId": None}}
        api = Mock()
        api.get_album.return_value = {"tracks": [{"videoId": "abcdefghijk"}]}
        with patch.object(feed, "sleep_youtube"):
            self.assertEqual("abcdefghijk", feed.first_youtube_track_video_id(api, "MPREtest", cache, self.report))
        api.get_album.assert_called_once()

    def test_malformed_blacklist_fails_instead_of_partially_unblocking(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "blocked.txt"
            path.write_text("abcdefghijk\nnot-an-id\n", encoding="utf-8")
            with patch.object(feed, "BLOCKED_SONGS_FILE", path):
                with self.assertRaises(ValueError):
                    feed.parse_blocked_song_ids()

    def test_malformed_artist_id_is_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "artists.txt"
            path.write_text("Artist | broken\n", encoding="utf-8")
            with patch.object(feed, "ALLOWED_ARTISTS_FILE", path):
                with self.assertRaises(ValueError):
                    feed.parse_allowed_artists()

    def test_reconciliation_removes_blocked_foreign_and_unplayable_songs(self):
        def song(video, channel=None):
            return {"type": "SINGLE", "youtubeVideoId": video, "artistChannelId": channel or self.artist["channelId"],
                    "releaseDate": feed.today_utc().isoformat(), "title": "Song"}
        original = {"items": [song("abcdefghijk"), song("blocked1234"), song("MPREalbum"), song("foreign1234", "other")],
                    "popularSongs": [song("blocked1234")], "popularArtists": [], "artistGenreShelves": []}
        result = feed.reconcile_feed(original, [self.artist], {"blocked1234"})
        self.assertEqual(["abcdefghijk"], [x["youtubeVideoId"] for x in result["items"]])
        self.assertEqual(1, result["itemsCount"])
        self.assertEqual([], result["popularSongs"])
        self.assertEqual(1, result["artistGenreArtistsCount"])
        self.assertEqual(4, len(original["items"]))

    def test_valid_prior_feed_survives_reconciliation(self):
        item = {"type": "ALBUM", "title": "Album", "youtubeBrowseId": "MPREtest",
                "artistChannelId": self.artist["channelId"], "releaseDate": feed.today_utc().isoformat()}
        result = feed.reconcile_feed({"items": [item]}, [self.artist], set())
        self.assertEqual([item], result["items"])
        self.assertEqual(result, feed.reconcile_feed(result, [self.artist], set()))


if __name__ == "__main__":
    unittest.main()

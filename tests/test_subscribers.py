import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from counts import parse_count
import generate_home_feed as feed
from refresh_artist_subscribers import refresh_rankings

class SubscriberTests(unittest.TestCase):
    def test_compact_and_localized_counts(self):
        for text, expected in [
            ("999", 999), ("1K", 1000), ("1.5K subscribers", 1500),
            ("1,5K subscribers", 1500), ("1,234 subscribers", 1234),
            ("1.234 subscribers", 1234), ("1\u00a0234", 1234),
            ("2.3M subscribers", 2300000), ("1.2 מיליון מנויים", 1200000),
            ("3 thousand subscribers", 3000), ("0", 0),
            (None, 0), ("unavailable", 0), (-4, 0), (float("nan"), 0),
        ]:
            with self.subTest(text=text):
                self.assertEqual(expected, parse_count(text))

    def test_only_subscribers_are_used(self):
        self.assertIsNone(feed.extract_artist_stats_text({"views": "9B", "monthlyListeners": "3M"}))
        self.assertEqual("1K", feed.extract_artist_stats_text({"subscribers": "1K", "views": "9B"}))

    def test_every_genre_and_popular_sort_numerically(self):
        items = [
            {"name": name, "channelId": name, "monthlyListenersText": count,
             "monthlyListeners": wrong, "genres": list(feed.GENRE_ORDER)}
            for name, count, wrong in [("small", "999", 999), ("large", "1K", 1), ("largest", "1.2M", 1)]
        ]
        expected = ["largest", "large", "small"]
        self.assertEqual(expected, [x["channelId"] for x in feed.dedupe_popular_artists(items)])
        for shelf in feed.build_artist_genre_shelves(items):
            self.assertEqual(expected, [x["channelId"] for x in shelf["artists"]])
            self.assertEqual([1200000, 1000, 999], [x["subscriberCount"] for x in shelf["artists"]])

    def test_reconcile_preserves_counts_and_is_idempotent(self):
        artists = [{"name": "small", "channelId": "UCsmall", "genres": ["pop"]},
                   {"name": "large", "channelId": "UClarge", "genres": ["pop"]}]
        original = {"artistGenreShelves": [{"id": "pop", "artists": [
            dict(artists[0], subscriberCount=999),
            dict(artists[1], monthlyListeners=1, monthlyListenersText="1K"),
        ]}]}
        result = feed.reconcile_feed(original, artists, set())
        self.assertEqual([1000, 999], [x["subscriberCount"] for x in result["artistGenreShelves"][0]["artists"]])
        self.assertEqual(result, feed.reconcile_feed(result, artists, set()))

    def test_refresh_ranks_all_artists_before_taking_top_twenty_and_preserves_failures(self):
        artists = [{"name": str(i), "channelId": str(i), "genres": ["pop"]} for i in range(25)]
        original = {"items": [], "popularSongs": [], "popularArtists": [
            dict(artists[0], subscriberCount=90000, subscriberCountText="90K")]}
        stats = {a["channelId"]: {"subscriberCount": i * 1000} for i, a in enumerate(artists) if i != 0}
        with patch.object(feed, "parse_blocked_song_ids", return_value=set()):
            result = refresh_rankings(original, artists, stats)
        self.assertEqual("0", result["popularArtists"][0]["channelId"])
        self.assertEqual("24", result["popularArtists"][1]["channelId"])
        self.assertEqual(20, len(result["popularArtists"]))
        self.assertEqual(25, len(result["artistGenreShelves"][0]["artists"]))
        self.assertEqual([], result["items"])

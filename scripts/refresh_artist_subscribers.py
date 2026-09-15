"""Refresh artist rankings without rebuilding releases or querying iTunes."""
import argparse
from pathlib import Path
from ytmusicapi import YTMusic
import generate_home_feed as feed

def active_artists():
    sources = feed.load_artist_sources()
    return [dict(a, genres=feed.artist_config(a, sources)["genres"])
            for a in feed.parse_allowed_artists()
            if feed.artist_config(a, sources)["homeFeedEnabled"]]

def refresh_rankings(original, artists, stats):
    cached = {}
    for shelf in original.get("artistGenreShelves", []):
        for item in shelf.get("artists", []):
            cached[item["channelId"]] = feed.normalize_subscriber_fields(item)
    for item in original.get("popularArtists", []):
        cached[item["channelId"]] = feed.normalize_subscriber_fields(item)
    candidates = []
    for artist in artists:
        channel = artist["channelId"]
        item = dict(cached.get(channel, {}), name=artist["name"], channelId=channel, genres=artist["genres"])
        fresh = stats.get(channel, {})
        # A missing public subscriber count must not erase the last known count.
        item.update({key: value for key, value in fresh.items() if value is not None})
        candidates.append(item)
    result = dict(original)
    result["popularArtists"] = feed.dedupe_popular_artists(candidates)
    result["artistGenreShelves"] = feed.build_artist_genre_shelves(candidates)
    result["subscriberCountsUpdatedAt"] = feed.utc_now_iso()
    return feed.reconcile_feed(result, artists, feed.parse_blocked_song_ids())

def collect(artists):
    api = YTMusic(language="en")
    report = feed.initial_report(len(artists))
    result = {}
    for index, artist in enumerate(artists, 1):
        data = feed.read_youtube_artist_data(api, artist, report)
        if data:
            result[artist["channelId"]] = feed.build_popular_artist_item(artist, data)
        print(f"Subscriber metadata: {index}/{len(artists)}", flush=True)
    if artists and not any(item.get("subscriberCount") is not None for item in result.values()):
        raise RuntimeError("No subscriber counts were available; preserving the current feed")
    print(f"Read {len(result)} artists; retained cached data for {len(artists) - len(result)}")
    return result

def main():
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--collect", type=Path)
    modes.add_argument("--apply", type=Path)
    args = parser.parse_args()
    artists = active_artists()
    if args.collect:
        feed.write_json_file(args.collect, collect(artists))
    else:
        original = feed.load_json_file(feed.OUTPUT_FILE, {})
        if not original or original.get("version") != 9:
            raise ValueError("Missing or unsupported home feed")
        result = refresh_rankings(original, artists, feed.load_json_file(args.apply, {}))
        feed.write_json_file(feed.OUTPUT_FILE, result)
        print(f"Sorted popular artists and {len(result['artistGenreShelves'])} genre shelves by subscribers")

if __name__ == "__main__":
    main()

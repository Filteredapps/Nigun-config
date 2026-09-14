import sys
from generate_home_feed import (
    parse_allowed_artists, parse_blocked_song_ids, load_artist_sources, artist_config,
    load_json_file, write_json_file, reconcile_feed, utc_now_iso, OUTPUT_FILE,
)

def main():
    artists = parse_allowed_artists()
    blocked = parse_blocked_song_ids()
    sources = load_artist_sources()
    active = [dict(a, genres=artist_config(a, sources)["genres"]) for a in artists if artist_config(a, sources)["homeFeedEnabled"]]
    original = load_json_file(OUTPUT_FILE, {})
    if not original or original.get("version") != 9:
        raise ValueError("Missing or unsupported home feed")
    reconciled = reconcile_feed(original, active, blocked)
    if "--reconcile" in sys.argv:
        if reconciled != original:
            reconciled["policyUpdatedAt"] = utc_now_iso()
            write_json_file(OUTPUT_FILE, reconciled)
    elif reconciled != original:
        raise ValueError("Feed policy, playable IDs or counters are stale; run with --reconcile")
    print(f"Validated {len(artists)} allowed artists, {len(blocked)} blocked songs, "
          f"{reconciled['itemsCount']} releases and {reconciled['popularSongsCount']} popular songs")

if __name__ == "__main__":
    main()

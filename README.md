# Nigun-config

Remote configuration repository for Nigun 1.0.

## Files consumed by the app

- `allowed_artists.txt` — allowed YouTube Music artists/channels.
- `blocked_songs.txt` — individual blocked YouTube song/video IDs. Blacklist always overrides the artist allow-list.
- `home_feed.json` — generated Home feed.

## Raw endpoints used by Nigun 1.0

- `https://raw.githubusercontent.com/Filteredapps/Nigun-config/refs/heads/main/allowed_artists.txt`
- `https://raw.githubusercontent.com/Filteredapps/Nigun-config/refs/heads/main/blocked_songs.txt`
- `https://raw.githubusercontent.com/Filteredapps/Nigun-config/refs/heads/main/home_feed.json`

### blocked_songs.txt format

One 11-character YouTube video/song ID per line. Blank lines and comments are ignored. A comment can be appended after `#`.

```text
# example only
dQw4w9WgXcQ # Artist - Song
```

The app caches the last valid remote blacklist. The feed generator also removes blocked song IDs before writing `home_feed.json`.

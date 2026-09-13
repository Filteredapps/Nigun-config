# README_ITUNES_REBUILD

הקובץ הזה נשאר לתאימות עם ZIP-ים קודמים.
ההוראות המעודכנות נמצאות כאן:

```text
README_ITUNES_FINAL.md
```


## Remote song blacklist

`blocked_songs.txt` contains one 11-character YouTube song/video ID per line. Comments may be appended after `#`. Nigun 1.0 downloads and caches this list independently of the allow-list, and blocked IDs always override an allowed artist. The feed generator also removes blocked song IDs before writing `home_feed.json`.

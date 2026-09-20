---
name: music-downloader
description: Search and download audio from YouTube and other platforms. Use when the user wants to download a song, extract audio from a video, convert video to audio, or grab music with metadata. Supports ytsearch queries, direct URLs, format conversion (m4a, opus, mp3, flac), and automatic ID3 tagging with album art. Triggers on "download music", "get audio", "extract audio", "download song", "get the mp3", "music for [query]".
---

## Quick Start

Download audio from a YouTube URL or search query, converting to m4a:

```bash
yt-dlp -f 140 -x --audio-format m4a -o "%(title)s.%(ext)s" "<url_or_search_query>"
```

## Search Syntax

| Format | Example |
|--------|---------|
| Search | `ytsearch1:Artist - Song Name` (1 result) |
| Search | `ytsearch5:Artist - Song Name` (5 results) |
| URL | `https://youtube.com/watch?v=...` |
| Playlist | `ytsearch10:Artist album name` |

The number before the colon limits results. Use `1` for exact matches, higher numbers for discovery.

## Format Selection

Highest quality audio formats from YouTube:

| Format ID | Codec | Quality | Extension |
|-----------|-------|---------|-----------|
| 251 | Opus | 133k | webm |
| 140 | AAC | 130k | m4a |
| 139 | AAC | 49k | m4a |

**Recommendation:** Use format `251` (opus) for highest quality, or `140` (m4a) for best compatibility.

## Output Formats

| Target | Command |
|--------|---------|
| m4a (AAC) | `-f 140 -x --audio-format m4a` |
| opus | `-f 251 -x --audio-format opus` |
| mp3 | `-f 140 -x --audio-format mp3` |
| flac | `-f 251 -x --audio-format flac` |

## Common Patterns

### Download single song (m4a)
```bash
yt-dlp -f 140 -x --audio-format m4a -o "%(title)s.%(ext)s" "<query>"
```

### Download single song (flac)
```bash
yt-dlp -f 251 -x --audio-format flac -o "%(title)s.%(ext)s" "<query>"
```

### Download from direct URL with metadata
```bash
yt-dlp -f 140 -x --audio-format m4a \
  --add-metadata \
  --embed-thumbnail \
  -o "%(title)s.%(ext)s" "<url>"
```

### Download with custom artist/title tags
```bash
yt-dlp -f 140 -x --audio-format m4a \
  --add-metadata \
  --embed-thumbnail \
  --add-metadata \
  --metadata-from-title "%(artist)s - %(title)s" \
  -o "%(artist)s - %(title)s.%(ext)s" "<query>"
```

## Metadata Tagging

YouTube provides metadata that can be embedded:

```bash
yt-dlp -f 140 -x --audio-format m4a \
  --add-metadata \
  --embed-thumbnail \
  -o "%(title)s.%(ext)s" "<query>"
```

For more control, tag files after download with mutagen:

```python
from mutagen.mp4 import MP4

audio = MP4("file.m4a")
audio.title = "Song Name"
audio.artist = "Artist Name"
audio.album = "Album Name"
audio.tags.append(MP4.Coordinates((0,)))  # embed artwork
audio.save()
```

## Troubleshooting

**HTTP 403 / SABR streams:** Update yt-dlp (`pip install -U yt-dlp`). Older versions skip SABR-only videos.

**PO Token needed (mweb client):** Some videos require a GVS PO Token. Either use `--extractor-args "youtube:po_token=mweb.gvs+XXX"` or try a different client like `--extractor-args "youtube:player_client=android"`.

**Only images available (web client):** Use `--extractor-args "youtube:player_client=android"` or `tv` client.

## Filename Conventions

- Use `%(title)s.%(ext)s` for simple names
- Use `%(artist)s - %(title)s.%(ext)s` for artist-prefixed names
- Special characters in titles (//, /) are replaced with `⧸⧸` by yt-dlp

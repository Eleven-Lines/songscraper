# songscraper

## Requirement
- Python 3.6+
- (Recommended) Pipenv

See `Pipfile` for required package.

## Usage

```sh
$ python fetch_ranking.py | sort | uniq > result.tsv
$ mkdir lyrics
$ python fetch_lyrics.py result.tsv
```

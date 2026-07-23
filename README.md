# Kwizerana Thesis Hub

Static archive for Kwizerana thesis articles and special briefs.

## Structure

- `index.html` is the hub homepage.
- `archive/index.html` lists all published theses.
- `archive/manifest.json` is the machine-readable article index.
- `articles/<slug>/index.html` stores each article.
- `scripts/publish_article.py` can add a new local HTML article and rebuild the hub.

## Add A New Article

```bash
python3 -B scripts/publish_article.py \
  --source /path/to/article.html \
  --slug article-slug \
  --date YYYY-MM-DD \
  --topic "Topic"
```

Commit and push after the script updates the site.

# Delivery checklist

- [ ] robots.txt checked, delay >= 1 s, no personal data, no captcha/paywall bypass
- [ ] Record count matches the site (compare with the site's counter or page count x items per page)
- [ ] All required fields filled; Summary shows 0 or explained empty fields
- [ ] Spot-check 5 random rows against the live site
- [ ] Prices are numbers (not text), links are clickable, header frozen, filter on
- [ ] Excel opens without warnings; CSV opens in Excel with correct letters (UTF-8 BOM)
- [ ] `uv run pytest -q` and `uv run ruff check .` pass
- [ ] No secrets in code: `git grep -nE "token|secret|password|api_key"`; `.env` not in the archive
- [ ] README_CLIENT.md updated with the client's command and output file names
- [ ] Logs folder removed from the archive (or contains only the last clean run)

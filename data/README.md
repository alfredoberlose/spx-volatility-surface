# Data

| File | Content | In the repository |
|---|---|---|
| `SPX_2026-10-26_1030.csv` | raw snapshot of SPX and SPXW option quotes (Yahoo Finance) | no |
| `SPX_2026-10-26_1030_clean.csv` | out-of-the-money options with forward and log-moneyness (notebook 02) | no |
| `SPX_2026-10-26_1030_iv.csv` | the same options with mid, bid and ask implied volatilities (notebook 03) | no |
| `SPX_2026-10-26_1030_svi.csv` | SVI parameters and quality checks for each expiry (notebook 04) | yes |
| `SPX_2026-10-26_1030_surface.csv` | SVI parameters with forward, rate and spot of each expiry (notebook 05) | yes |
| `SPX_2026-11-20_1210_svi.csv`, `SPX_2026-11-20_1210_surface.csv` | the same files for the snapshot of 20 November 2026, 12:10 New York time | yes |

Quote-level files are not redistributed. To rebuild them, run `01_download.ipynb` while the market
is open and set `SNAPSHOT` to the new file name in notebooks 02–06.

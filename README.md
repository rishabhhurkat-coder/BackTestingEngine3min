# EMA 200 Trades

Streamlit app for cleaning raw 3-minute CSV files, viewing EMA charts, and saving trade signals directly into per-scrip CSV files.

## Clean Repo Layout

```text
EMA 200 TRADES
├── streamlit_app.py
├── data_pipeline.py
├── component.py
├── requirements.txt
├── README.md
├── scripts/
├── snapshots/
├── tv_chart_component/
└── workspace_template/
```

## Working Folder Layout

Create or select a main working folder with this structure:

```text
Main Folder
├── Raw Files
├── Input Files
└── Output Files
```

- `Raw Files`: downloaded raw CSV fragments
- `Input Files`: cleaned merged chart-ready CSVs
- `Output Files`: saved signal CSVs used by the app

## App Flow

1. Click `Main Folder` and select your working folder.
2. Click `Process Input Files` to clean and merge files from `Raw Files` into `Input Files`.
3. Select a scrip.
4. Click chart candles to save BUY or SELL signals.
5. Saved signals update directly in the matching CSV inside `Output Files`.

## Notes

- `workspace_template/` is included as a clean starter structure for GitHub.
- Legacy helper scripts are stored in `archive/legacy/`.
- The `SALONILOCK` restore snapshot is stored in `snapshots/streamlit_app.SALONILOCK.py`.

## Run

```bash
streamlit run streamlit_app.py
```

Or use:

```bash
python scripts/launch_streamlit.py
```

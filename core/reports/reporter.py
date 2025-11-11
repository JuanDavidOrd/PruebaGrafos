from pathlib import Path
import pandas as pd
from core.sim.simulator import RunLog

def export_report(log: RunLog, out_dir: str | Path):
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(log.to_rows())
    df.to_csv(Path(out_dir)/"reporte.csv", index=False)
    df.to_json(Path(out_dir)/"reporte.json", orient="records", force_ascii=False)
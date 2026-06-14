# home_tracker.py
# 帰宅記録 API — 独立した FastAPI アプリ
#
# 起動: uvicorn home_tracker:app --host 127.0.0.1 --port 8001
# Nginx が /home/ → localhost:8001 にプロキシする
#
# ストレージ切り替え方法:
#   現在: JsonArrivalRepository（data/home_arrivals.json）
#   将来: get_repository() の return を PostgresArrivalRepository に差し替えるだけ

import json
import os
from abc import ABC, abstractmethod
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, Request, Header
from pydantic import BaseModel

# ─── 設定 ────────────────────────────────────────────────────────────────────

JST = timezone(timedelta(hours=9))

API_KEY: str = os.environ.get("HOME_API_KEY", "")

ALLOWED_UIDS: list[str] = [
    uid.strip().upper()
    for uid in os.environ.get("HOME_ALLOWED_UIDS", "").split(",")
    if uid.strip()
]

# ─── アプリ ───────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Home Tracker API",
    description="帰宅記録 API。ESP32 + RC522 から叩く。",
    version="1.0.0",
)

# ─── ドメインモデル ────────────────────────────────────────────────────────────

class ArrivalRecord(BaseModel):
    arrived_at: str
    uid: Optional[str] = None
    client_ip: Optional[str] = None
    note: Optional[str] = None

# ─── Repository 抽象基底クラス ──────────────────────────────────────────────────

class AbstractArrivalRepository(ABC):
    @abstractmethod
    def save(self, record: ArrivalRecord) -> None: ...

    @abstractmethod
    def get_all(self) -> list[ArrivalRecord]: ...

    def get_latest(self) -> Optional[ArrivalRecord]:
        records = self.get_all()
        return records[-1] if records else None

# ─── JSON 実装（現在使用中） ────────────────────────────────────────────────────

class JsonArrivalRepository(AbstractArrivalRepository):
    def __init__(self, path: Path):
        self._path = path

    def _load_raw(self) -> list[dict]:
        if not self._path.exists():
            return []
        return json.loads(self._path.read_text(encoding="utf-8")).get("arrivals", [])

    def save(self, record: ArrivalRecord) -> None:
        records = self._load_raw()
        records.append(record.model_dump())
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps({"arrivals": records}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def get_all(self) -> list[ArrivalRecord]:
        return [ArrivalRecord(**r) for r in self._load_raw()]

# ─── PostgreSQL 実装（将来用スタブ） ────────────────────────────────────────────

class PostgresArrivalRepository(AbstractArrivalRepository):
    """
    TODO: PostgreSQL 移行時に実装する。
    推奨: SQLAlchemy 2.x (async) + asyncpg

    テーブル例:
        CREATE TABLE home_arrivals (
            id         SERIAL PRIMARY KEY,
            arrived_at TIMESTAMPTZ NOT NULL,
            uid        TEXT,
            client_ip  TEXT,
            note       TEXT
        );
    """
    def __init__(self, dsn: str):
        raise NotImplementedError("PostgreSQL 実装はまだです。")

    def save(self, record: ArrivalRecord) -> None:
        raise NotImplementedError

    def get_all(self) -> list[ArrivalRecord]:
        raise NotImplementedError

# ─── DI ──────────────────────────────────────────────────────────────────────

def get_repository() -> AbstractArrivalRepository:
    # --- 今はこっち ---
    return JsonArrivalRepository(
        Path(__file__).parent / "data" / "home_arrivals.json"
    )
    # --- 将来はこっちに切り替える ---
    # return PostgresArrivalRepository(os.environ["DATABASE_URL"])

# ─── 認証・ヘルパー ────────────────────────────────────────────────────────────

def verify_auth(x_api_key: str = Header(..., alias="X-API-Key")):
    if not API_KEY:
        raise HTTPException(500, "HOME_API_KEY が設定されていません")
    if x_api_key != API_KEY:
        raise HTTPException(403, "Invalid API key")

def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

# ─── エンドポイント ────────────────────────────────────────────────────────────

class ArriveRequest(BaseModel):
    uid: Optional[str] = None
    note: Optional[str] = None

class ArrivalResponse(BaseModel):
    status: str
    arrived_at: str
    message: str


@app.get("/")
def root():
    return {"service": "home-tracker", "status": "ok"}


@app.post("/home/arrive", response_model=ArrivalResponse)
def arrive(
    body: ArriveRequest,
    request: Request,
    _auth=Depends(verify_auth),
    repo: AbstractArrivalRepository = Depends(get_repository),
):
    uid = body.uid.upper() if body.uid else None

    if ALLOWED_UIDS and uid not in ALLOWED_UIDS:
        raise HTTPException(403, f"Unknown card UID: {uid}")

    now_jst = datetime.now(JST)
    record = ArrivalRecord(
        arrived_at=now_jst.isoformat(),
        uid=uid,
        client_ip=_get_client_ip(request),
        note=body.note,
    )
    repo.save(record)

    return ArrivalResponse(
        status="ok",
        arrived_at=record.arrived_at,
        message=f"帰宅を記録しましたわ！ ({now_jst.strftime('%H:%M')} JST)",
    )


@app.get("/home/history")
def history(
    limit: int = 30,
    _auth=Depends(verify_auth),
    repo: AbstractArrivalRepository = Depends(get_repository),
):
    records = repo.get_all()
    return {
        "count": len(records),
        "arrivals": [r.model_dump() for r in reversed(records)][:limit],
    }


@app.get("/home/latest")
def latest(
    _auth=Depends(verify_auth),
    repo: AbstractArrivalRepository = Depends(get_repository),
):
    record = repo.get_latest()
    if not record:
        return {"status": "no_record", "arrived_at": None}
    return {"status": "ok", "arrived_at": record.arrived_at}

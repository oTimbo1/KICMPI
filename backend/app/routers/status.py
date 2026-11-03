"""Status + endpoint probes (PLAN §5.3).

``GET /status`` — app + Qdrant + both model endpoints, probed with a short
(1.5 s) timeout against ``{base}/v1/models``. The frontend header renders
three green/red dots from this; ``mock_mode`` renders the amber "demo-modus"
badge.

``POST /probe`` — the Settings tab's per-endpoint "Test verbinding": probes an
arbitrary (http/https) URL the user just typed, with a slightly longer (3 s)
timeout, so feedback reflects unsaved form values.
"""
from __future__ import annotations

import re
import time

import httpx
from fastapi import APIRouter

from .. import store
from ..config import settings
from ..pipeline.embedding import mock_mode
from ..schemas import EndpointStatus, ProbeRequest, ProbeResult, StatusResponse

router = APIRouter(tags=["status"])

STATUS_PROBE_TIMEOUT = 1.5
TEST_PROBE_TIMEOUT = 3.0
_URL_RE = re.compile(r"^https?://[^\s/$.?#][^\s]*$", re.IGNORECASE)


def _probe(url: str, timeout: float) -> EndpointStatus:
    url = (url or "").strip().rstrip("/")
    if not _URL_RE.match(url):
        return EndpointStatus(ok=False, url=url, reason="ongeldige URL (verwacht http://ip:port)")
    try:
        t0 = time.time()
        resp = httpx.get(f"{url}/v1/models", timeout=timeout)
        latency = int((time.time() - t0) * 1000)
        if resp.status_code == 200:
            return EndpointStatus(ok=True, url=url, latency_ms=latency)
        return EndpointStatus(ok=False, url=url, latency_ms=latency, reason=f"HTTP {resp.status_code}")
    except httpx.TimeoutException:
        return EndpointStatus(ok=False, url=url, reason="time-out (niet bereikbaar)")
    except Exception as e:  # connection refused, DNS, …
        return EndpointStatus(ok=False, url=url, reason=f"niet bereikbaar ({type(e).__name__})")


@router.get("/status", response_model=StatusResponse)
def status():
    try:
        store.ensure_collection()  # also creates the collection on first use
        qdrant = EndpointStatus(ok=True, url=store.collection())
    except Exception as e:
        qdrant = EndpointStatus(ok=False, url=store.collection(), reason=type(e).__name__)

    if mock_mode():
        embedding = EndpointStatus(ok=True, url="demo-modus (mock)", latency_ms=0)
    else:
        embedding = _probe(str(settings.get("embedding_base_url")), STATUS_PROBE_TIMEOUT)

    summary = _probe(str(settings.get("summary_base_url")), STATUS_PROBE_TIMEOUT)

    return StatusResponse(
        app="ok",
        mock_mode=mock_mode(),
        qdrant=qdrant,
        embedding=embedding,
        summary=summary,
    )


@router.post("/probe", response_model=ProbeResult)
def probe(body: ProbeRequest):
    url = (body.url or "").strip().rstrip("/")
    st = _probe(url, TEST_PROBE_TIMEOUT)
    models: list[str] | None = None
    if st.ok and _URL_RE.match(url):
        try:
            resp = httpx.get(f"{url}/v1/models", timeout=TEST_PROBE_TIMEOUT)
            if resp.status_code == 200:
                models = [m.get("name") for m in resp.json().get("models", []) if m.get("name")]
        except Exception:
            models = None
    return ProbeResult(ok=st.ok, url=url, latency_ms=st.latency_ms, reason=st.reason, models=models)

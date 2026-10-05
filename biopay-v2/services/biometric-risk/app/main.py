import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

app = FastAPI(title="BioPay Biometric & Risk Service", version="0.1.0", docs_url=None)
static_dir = Path(__file__).parent / "static"
app.mount("/assets", StaticFiles(directory=static_dir), name="assets")

@app.get("/docs", include_in_schema=False, response_class=HTMLResponse)
def docs():
    response = get_swagger_ui_html(openapi_url=app.openapi_url, title="BioPay · Risk explorer",
        swagger_ui_parameters={"displayRequestDuration": True, "defaultModelsExpandDepth": -1})
    html = response.body.decode("utf-8")
    html = html.replace("</head>", '<meta name="theme-color" content="#142c24"><link rel="stylesheet" href="/assets/globals.css"></head>')
    html = html.replace("<body>", "<body>" + (static_dir / "docs-shell.html").read_text(encoding="utf-8"))
    html = html.replace("</body>", '<script src="/assets/docs-title.js"></script></div><footer class="page-footer"><span>BioPay · Payments, made personal.</span><span>Local demo · KES</span></footer></main></div></div></body>')
    return HTMLResponse(html)

class RiskRequest(BaseModel):
    paymentId: str = Field(min_length=1, max_length=64)
    payerUserId: str = Field(min_length=1, max_length=64)
    merchantId: str = Field(min_length=1, max_length=64)
    deviceId: str = Field(max_length=64)
    amount: float = Field(gt=0, allow_inf_nan=False)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    liveness: bool
    recentAttemptCount: int = Field(default=0, ge=0)

class RiskResponse(BaseModel):
    riskScore: float
    decision: str
    reason: str

@app.get("/health", tags=["Service health"], summary="Check risk service health")
def health():
    return {"status": "ok", "service": "biometric-risk"}

@app.post("/v1/risk/score", response_model=RiskResponse, tags=["Risk scoring"], summary="Evaluate a payment's risk")
def score(req: RiskRequest):
    # Deterministic prototype policy. Replace with real signals/models later.
    score = 0.05
    reasons = []

    if not req.liveness:
        score += 0.90
        reasons.append("liveness_failed")
    if req.amount >= 100_000:
        score += 0.35
        reasons.append("high_amount")
    elif req.amount >= 50_000:
        score += 0.20
        reasons.append("elevated_amount")
    if req.recentAttemptCount >= 5:
        score += 0.35
        reasons.append("high_velocity")
    if not req.deviceId:
        score += 0.40
        reasons.append("missing_device")

    score = min(score, 1.0)
    threshold = float(os.getenv("BIOPAY_RISK_THRESHOLD", "0.80"))

    if score >= threshold:
        decision = "DECLINE"
    elif score >= 0.45:
        decision = "STEP_UP"
    else:
        decision = "APPROVE"

    return RiskResponse(
        riskScore=round(score, 6),
        decision=decision,
        reason=",".join(reasons) if reasons else "prototype_low_risk"
    )

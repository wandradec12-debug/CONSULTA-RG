import os, io, hashlib, secrets
from datetime import datetime, timezone
import pandas as pd
import jwt
from fastapi import FastAPI, Request, UploadFile, File, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import declarative_base, sessionmaker, Session

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./estoque.db")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

class ImportBatch(Base):
    __tablename__ = "import_batches"
    id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False)
    rows = Column(Integer, default=0)
    imported_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    checksum = Column(String(64), nullable=False)

class StockItem(Base):
    __tablename__ = "stock_items"
    id = Column(Integer, primary_key=True)
    rg = Column(String(120), index=True, nullable=False)
    produto = Column(String(255))
    lote = Column(String(120))
    validade = Column(String(50))
    posicao = Column(String(120))
    quantidade = Column(String(80))
    status = Column(String(120))
    import_id = Column(Integer, ForeignKey("import_batches.id"), index=True)

class Consultation(Base):
    __tablename__ = "consultations"
    id = Column(Integer, primary_key=True)
    rg = Column(String(120), index=True)
    found = Column(Integer, default=0)
    consulted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Consulta RG • Estoque")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.get("/health")
def health():
    return {"status": "ok"}

def db():
    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()

def token_for(user):
    return jwt.encode(
        {"sub": user, "exp": datetime.now(timezone.utc).timestamp() + 28800},
        SECRET_KEY,
        algorithm="HS256",
    )

def current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"]).get("sub")
    except Exception:
        return None

@app.get("/", response_class=HTMLResponse)
def home(request: Request, user=Depends(current_user)):
    if not user:
        return RedirectResponse("/login", 302)
    return templates.TemplateResponse("index.html", {"request": request, "user": user})

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    if secrets.compare_digest(username, ADMIN_USER) and secrets.compare_digest(password, ADMIN_PASSWORD):
        r = RedirectResponse("/", 302)
        r.set_cookie(
            "access_token",
            token_for(username),
            httponly=True,
            secure=COOKIE_SECURE,
            samesite="lax",
        )
        return r
    return RedirectResponse("/login?error=1", 302)

@app.get("/logout")
def logout():
    r = RedirectResponse("/login", 302)
    r.delete_cookie("access_token")
    return r

@app.get("/api/stats")
def stats(db: Session = Depends(db), user=Depends(current_user)):
    if not user:
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    last = db.query(ImportBatch).order_by(ImportBatch.id.desc()).first()
    return {
        "rg_count": db.query(func.count(StockItem.id)).scalar() or 0,
        "imports": db.query(func.count(ImportBatch.id)).scalar() or 0,
        "last_import": last.imported_at.isoformat() if last else None,
    }

ALIASES = {
    "rg": "rg",
    "registrogeral": "rg",
    "registro": "rg",
    "codigo": "rg",
    "codigorg": "rg",
    "produto": "produto",
    "item": "produto",
    "descricaoproduto": "produto",
    "lote": "lote",
    "validade": "validade",
    "posicao": "posicao",
    "localizacao": "posicao",
    "quantidade": "quantidade",
    "qtd": "quantidade",
    "qtdcx": "quantidade",
    "status": "status",
    "situacao": "status",
}

def norm(s):
    import unicodedata
    s = str(s).strip().lower()
    return "".join(
        c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)
    ).replace(" ", "").replace("_", "").replace("-", "")

@app.post("/api/import")
async def import_excel(file: UploadFile = File(...), db: Session = Depends(db), user=Depends(current_user)):
    if not user:
        return JSONResponse({"error": "unauthorized"}, status_code=401)

    raw = await file.read()
    checksum = hashlib.sha256(raw).hexdigest()

    try:
        if file.filename.lower().endswith(".csv"):
            df = pd.read_csv(io.BytesIO(raw), dtype=str)
        else:
            df = pd.read_excel(io.BytesIO(raw), dtype=str)
    except Exception as e:
        return JSONResponse({"error": f"Não foi possível ler o arquivo: {e}"}, status_code=400)

    mapped = {}
    for c in df.columns:
        key = norm(c)
        if key in ALIASES:
            mapped[ALIASES[key]] = c

    if "rg" not in mapped or "posicao" not in mapped:
        return JSONResponse(
            {"error": "A base precisa conter pelo menos as colunas RG e LOCALIZAÇÃO (posição)."},
            status_code=400,
        )

    batch = ImportBatch(filename=file.filename, checksum=checksum, rows=len(df))
    db.add(batch)
    db.flush()

    db.query(StockItem).delete(synchronize_session=False)

    for _, row in df.fillna("").iterrows():
        rg = str(row[mapped["rg"]]).strip()
        if not rg:
            continue

        db.add(
            StockItem(
                rg=rg,
                produto=str(row[mapped["produto"]]).strip() if "produto" in mapped else "",
                lote=str(row[mapped["lote"]]).strip() if "lote" in mapped else "",
                validade=str(row[mapped["validade"]]).strip() if "validade" in mapped else "",
                posicao=str(row[mapped["posicao"]]).strip(),
                quantidade=str(row[mapped["quantidade"]]).strip() if "quantidade" in mapped else "",
                status=str(row[mapped["status"]]).strip() if "status" in mapped else "",
                import_id=batch.id,
            )
        )

    db.commit()
    return {"ok": True, "rows": len(df), "filename": file.filename, "import_id": batch.id}

@app.get("/api/rg/{rg}")
def lookup(rg: str, db: Session = Depends(db), user=Depends(current_user)):
    if not user:
        return JSONResponse({"error": "unauthorized"}, status_code=401)

    clean = rg.strip()
    item = db.query(StockItem).filter(StockItem.rg == clean).first()
    db.add(Consultation(rg=clean, found=1 if item else 0))
    db.commit()

    if not item:
        return {"found": False, "rg": clean}

    return {
        "found": True,
        "rg": item.rg,
        "produto": item.produto,
        "lote": item.lote,
        "validade": item.validade,
        "posicao": item.posicao,
        "quantidade": item.quantidade,
        "status": item.status,
    }

@app.get("/api/imports")
def imports(db: Session = Depends(db), user=Depends(current_user)):
    if not user:
        return JSONResponse({"error": "unauthorized"}, status_code=401)

    return [
        {
            "id": x.id,
            "filename": x.filename,
            "rows": x.rows,
            "imported_at": x.imported_at.isoformat(),
        }
        for x in db.query(ImportBatch).order_by(ImportBatch.id.desc()).limit(20).all()
    ]

import os, pathlib, sys
from fastapi import FastAPI, UploadFile, File, Response
from fastapi.responses import FileResponse, JSONResponse
import shutil

# ---------- auto-find the HDD ----------
USER = os.environ.get("USER", "")
MEDIA = pathlib.Path("/media") / USER
candidates = [p for p in MEDIA.glob("*") if os.path.ismount(p)]
if not candidates:
    sys.exit(f"No mounted drive found under {MEDIA}. Plug in the HDD and restart.")
HDD = pathlib.Path(os.environ["HDD_PATH"]) if "HDD_PATH" in os.environ else candidates[0]
DEST = HDD / "iphone_uploads"
print(f"Uploads will go to: {DEST}")

# ---------- categories ----------
CATEGORIES = {
    "images":    {".jpg",".jpeg",".png",".gif",".heic",".heif",".webp",".bmp",
                  ".tiff",".tif",".dng",".svg",".raw",".cr2",".nef",".arw"},
    "videos":    {".mp4",".mov",".m4v",".avi",".mkv",".webm",".3gp",".mpg",".mpeg",".wmv"},
    "audio":     {".mp3",".m4a",".wav",".aac",".flac",".ogg",".opus",".wma"},
    "documents": {".pdf",".doc",".docx",".xls",".xlsx",".ppt",".pptx",".txt",".rtf",
                  ".csv",".md",".epub",".pages",".numbers",".key"},
    "archives":  {".zip",".rar",".7z",".tar",".gz",".bz2",".xz"},
}

def categorize(filename: str, content_type: str) -> str:
    ext = pathlib.Path(filename).suffix.lower()
    for cat, exts in CATEGORIES.items():
        if ext in exts:
            return cat
    main = (content_type or "").split("/")[0]        # fallback: trust the MIME type
    return {"image": "images", "video": "videos", "audio": "audio"}.get(main, "others")

def find_target(folder, name, size):
    """Skip exact duplicates (same name + size), else save as 'name (1).ext'."""
    target = folder / name
    if not target.exists():
        return target, False
    if target.stat().st_size == size:
        return target, True                          # already on HDD -> skip
    stem, suffix = target.stem, target.suffix
    i = 1
    while (folder / f"{stem} ({i}){suffix}").exists():
        i += 1
    return folder / f"{stem} ({i}){suffix}", False

app = FastAPI()

@app.get("/")
def home():
    return FileResponse("index.html")

@app.get("/favicon.ico")
def favicon():
    return Response(status_code=204)

@app.get("/health")
def health():
    mounted = os.path.ismount(HDD)
    return {"ok": True, "hdd": mounted,
            "free": shutil.disk_usage(HDD).free if mounted else None}

@app.post("/sync")
async def sync(files: list[UploadFile] = File(...)):
    if not os.path.ismount(HDD):
        return JSONResponse(status_code=503, content={
            "error": f"HDD not mounted at {HDD} — replug the USB cable and restart the server."})
    try:
        DEST.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        return JSONResponse(status_code=500, content={
            "error": "Permission denied on the drive (likely a read-only NTFS mount)."})

    saved, skipped, failed, counts = [], [], [], {}
    for f in files:
        try:
            f.file.seek(0, os.SEEK_END)              # get file size before writing
            size = f.file.tell()
            f.file.seek(0)

            name = pathlib.Path(f.filename or "file").name
            cat = categorize(name, f.content_type)
            folder = DEST / cat
            folder.mkdir(exist_ok=True)

            out, is_dup = find_target(folder, name, size)
            if is_dup:
                skipped.append(name)
                continue

            with out.open("wb") as w:
                while chunk := await f.read(1024 * 1024):
                    w.write(chunk)
            saved.append(f"{cat}/{out.name}")
            counts[cat] = counts.get(cat, 0) + 1
        except Exception as e:
            failed.append({"file": f.filename, "error": str(e)})

    return {"saved": saved, "skipped": skipped, "failed": failed, "counts": counts}

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from scipy.sparse import hstack
from email import policy
from email.parser import BytesParser
from email.header import decode_header, make_header
from html.parser import HTMLParser
import joblib

model_package = joblib.load("phishing_detector.joblib")

model = model_package["model"]
word_vectorizer = model_package["word_vectorizer"]
char_vectorizer = model_package["char_vectorizer"]

app = FastAPI(
    title="Phishing Email Detector API",
    description="API for detecting phishing emails using a machine learning model.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.ignore_content = False

    def handle_starttag(self, tag, attrs):
        if tag.lower() in {"script", "style"}:
            self.ignore_content = True

    def handle_endtag(self, tag):
        if tag.lower() in {"script", "style"}:
            self.ignore_content = False

    def handle_data(self, data):
        if not self.ignore_content:
            text = data.strip()
            if text:
                self.parts.append(text)

    def get_text(self):
        return " ".join(self.parts)


def extract_eml_content(data: bytes):
    msg = BytesParser(policy=policy.default).parsebytes(data)

    raw_subject = msg.get("subject", "")
    subject = str(make_header(decode_header(raw_subject))) if raw_subject else ""

    plain_body = ""
    html_body = ""

    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_disposition() == "attachment":
                continue

            content_type = part.get_content_type()

            if content_type == "text/plain" and not plain_body:
                try:
                    plain_body = part.get_content()
                except Exception:
                    pass

            elif content_type == "text/html" and not html_body:
                try:
                    html_body = part.get_content()
                except Exception:
                    pass
    else:
        content_type = msg.get_content_type()

        if content_type == "text/plain":
            try:
                plain_body = msg.get_content()
            except Exception:
                pass
        elif content_type == "text/html":
            try:
                html_body = msg.get_content()
            except Exception:
                pass

    if plain_body.strip():
        body = plain_body.strip()
    elif html_body.strip():
        parser = HTMLTextExtractor()
        parser.feed(html_body)
        body = parser.get_text().strip()
    else:
        body = ""

    return subject.strip(), body


class EmailRequest(BaseModel):
    subject: str = ""
    body: str = ""


@app.get("/")
def root():
    return {
        "message": "Phishing Email Detector API is running."
    }


@app.post("/predict")
def predict_email(email: EmailRequest):
    text = email.subject + " " + email.body

    word_features = word_vectorizer.transform([text])
    char_features = char_vectorizer.transform([text])

    combined_features = hstack([
        word_features,
        char_features
    ]).tocsr()

    prediction = int(model.predict(combined_features)[0])
    phishing_probability = float(
        model.predict_proba(combined_features)[0][1]
    )

    label = "Phishing" if prediction == 1 else "Benign"

    return {
        "prediction": label,
        "phishing_score": round(phishing_probability, 4),
        "phishing_percentage": round(phishing_probability * 100, 2)
    }


@app.post("/predict-eml")
async def predict_eml(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="A file is required."
        )

    if not file.filename.lower().endswith(".eml"):
        raise HTTPException(
            status_code=400,
            detail="Only .eml files are supported."
        )

    max_size = 5 * 1024 * 1024
    data = await file.read(max_size + 1)

    if len(data) > max_size:
        raise HTTPException(
            status_code=413,
            detail="File is too large. Maximum size is 5 MB."
        )

    try:
        subject, body = extract_eml_content(data)
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Could not parse the .eml file: {str(exc)}"
        )

    if not subject and not body:
        raise HTTPException(
            status_code=400,
            detail="No readable email content was found."
        )

    text = subject + " " + body

    word_features = word_vectorizer.transform([text])
    char_features = char_vectorizer.transform([text])

    combined_features = hstack([
        word_features,
        char_features
    ]).tocsr()

    prediction = int(model.predict(combined_features)[0])
    phishing_probability = float(
        model.predict_proba(combined_features)[0][1]
    )

    label = "Phishing" if prediction == 1 else "Benign"

    return {
        "filename": file.filename,
        "subject": subject,
        "prediction": label,
        "phishing_score": round(phishing_probability, 4),
        "phishing_percentage": round(phishing_probability * 100, 2)
    }

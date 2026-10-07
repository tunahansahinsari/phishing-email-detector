# Phishing Email Detector

A local machine learning application that classifies emails as **Benign** or **Phishing**. The project combines a scikit-learn text classification model with a FastAPI backend and a lightweight HTML/CSS/JavaScript frontend.

## Features

- Manual email analysis using subject and body text
- `.eml` file upload and parsing
- Word-level TF-IDF features
- Character-level TF-IDF features
- Logistic Regression classifier
- Phishing risk score
- Risk-based feedback messages
- Local FastAPI API with interactive Swagger documentation

## Architecture

```text
                     User
                      |
             +--------+--------+
             |                 |
        Manual Email       .eml Upload
             |                 |
             +--------+--------+
                      |
                      v
                FastAPI Backend
                      |
                EML parsing
                  (if needed)
                      |
                      v
            Subject + Email Body
                      |
              +-------+-------+
              |               |
        Word TF-IDF     Character TF-IDF
              |               |
              +-------+-------+
                      |
                      v
             Logistic Regression
                      |
                      v
             Benign / Phishing
```

## Machine Learning

### Dataset

The model was trained with the **MeAJOR: Merged email Assets from Joint Open-source Repositories** dataset published on Zenodo.

Dataset: https://zenodo.org/records/18471483
DOI: https://doi.org/10.5281/zenodo.18471483

The original dataset contains 108,685 samples. Duplicate email texts were removed before the final train/test split to reduce the risk of train/test leakage. One row with a missing label was also excluded during preprocessing.

Final dataset used for evaluation:

```text
Samples before deduplication: 108,684
Duplicate text rows removed:    3,751
Samples after deduplication:  104,933
```

The dataset was split using an 80/20 stratified train/test split.

### Final Feature Pipeline

The deployed model uses only email text because adding URL, attachment, and language metadata did not provide a meaningful improvement while making deployment more complicated.

**Word-level TF-IDF**

- `ngram_range=(1, 2)`
- `min_df=2`
- `max_features=200000`

**Character-level TF-IDF**

- `analyzer="char"`
- `ngram_range=(3, 5)`
- `min_df=2`
- `max_features=100000`
- `dtype=float32`

The two sparse feature matrices are concatenated and passed to a Logistic Regression classifier.

## Evaluation

The final model was evaluated on the deduplicated test set.

| Metric | Result |
|---|---:|
| Accuracy | **98.22%** |
| ROC-AUC | **99.81%** |
| Benign Precision | **~98%** |
| Benign Recall | **~98%** |
| Phishing Precision | **~98%** |
| Phishing Recall | **~98%** |
| Phishing F1-score | **~98%** |

Confusion matrix:

```text
                    Predicted
                 Benign  Phishing

Actual Benign     11430     188
Actual Phishing     185    9184
```

The model achieved these results after duplicate text samples were removed before splitting the data.

> **Risk score:** The score displayed by the application is a model estimate, not a guarantee.

## Technologies

**Machine Learning**

- Python
- Pandas
- NumPy
- scikit-learn
- SciPy
- Joblib

**Backend**

- FastAPI
- Uvicorn
- Pydantic
- Python standard-library email parser

**Frontend**

- HTML
- CSS
- JavaScript

## Project Structure

```text
phishing-detector/
|
├── backend/
│   ├── main.py
│   ├── phishing_detector.joblib
│   └── requirements.txt
│
├── frontend/
│   ├── index.html
│   ├── script.js
│   └── style.css
│
├── .gitignore
└── README.md
```

The trained model is included in `backend/phishing_detector.joblib`. The training dataset and Python virtual environment are intentionally not included in the repository.

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/phishing-email-detector.git
cd phishing-email-detector
```

### 2. Create the Python virtual environment

```powershell
cd backend
python -m venv .venv
```

On Windows PowerShell, activating the environment may be blocked by the execution policy. Activation is not required. The commands below call the environment's Python directly.

### 3. Install backend dependencies

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 4. Start the backend

```powershell
.venv\Scripts\python.exe -m uvicorn main:app --reload
```

The API will run at:

```text
http://127.0.0.1:8000
```

Interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

## Frontend

Open `frontend/index.html` using a local development server. In VS Code, the Live Server extension can be used.

The frontend communicates with the backend at:

```text
http://127.0.0.1:8000
```

Make sure the FastAPI backend is running before analyzing an email.

## API Endpoints

### `GET /`

Health check for the API.

Example response:

```json
{
  "message": "Phishing Email Detector API is running."
}
```

### `POST /predict`

Classifies a manually entered email.

Request:

```json
{
  "subject": "Urgent account verification",
  "body": "Your account has been suspended. Please verify your identity immediately."
}
```

Example response:

```json
{
  "prediction": "Phishing",
  "phishing_score": 0.9821,
  "phishing_percentage": 98.21
}
```

### `POST /predict-eml`

Accepts an `.eml` file, extracts a readable subject/body, and runs the same trained model pipeline.

The current implementation ignores attachments during text extraction. It accepts `.eml` files up to 5 MB.

## Risk Levels

The frontend maps the model score to the following messages:

| Score | Level |
|---|---|
| 0-20% | Very Low Risk |
| 20-40% | Low Risk |
| 40-60% | Suspicious |
| 60-80% | High Risk |
| 80-100% | Very High Risk |

These ranges are presentation rules used by the frontend and are not independently calibrated probability thresholds.

## Development Notes

Several approaches were evaluated during model development:

```text
Word TF-IDF + Logistic Regression
              |
              v
          ~97.77% accuracy

Word + Character TF-IDF + Logistic Regression
              |
              v
          ~98.36% accuracy before deduplication

Deduplicated Word + Character TF-IDF
              |
              v
          98.22% accuracy

Deduplicated Text + Metadata
              |
              v
          98.22% accuracy
```

The text-only model was selected for deployment because it provided essentially the same performance as the metadata-enhanced model while keeping inference and backend integration simpler.

## Limitations

- The model is trained on the MeAJOR dataset and may not generalize perfectly to new phishing campaigns.
- The risk score is a model estimate, not a security guarantee.
- The current classifier primarily evaluates email text.
- Attachments are not inspected for malicious content.
- Sender/domain reputation is not used by the deployed model.
- The application is designed for local educational and demonstration use rather than production email security.

## Dataset Attribution

MeAJOR: Merged email Assets from Joint Open-source Repositories. Zenodo, version 2.0, published February 2026.

Dataset page: https://zenodo.org/records/18471483
DOI: 10.5281/zenodo.18471483

Please refer to the original Zenodo record for the dataset's terms, citation, and attribution requirements.

## Disclaimer

This project is intended for educational and research purposes. Do not use it as the sole security mechanism for real-world email security decisions.

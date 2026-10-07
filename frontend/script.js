const analyzeButton = document.getElementById("analyzeButton");
const analyzeEmlButton = document.getElementById("analyzeEmlButton");

const subjectInput = document.getElementById("subject");
const bodyInput = document.getElementById("body");
const emlFileInput = document.getElementById("emlFile");

const loading = document.getElementById("loading");

const result = document.getElementById("result");
const prediction = document.getElementById("prediction");
const score = document.getElementById("score");
const resultIcon = document.getElementById("resultIcon");
const responseMessage = document.getElementById("responseMessage");

const error = document.getElementById("error");

analyzeButton.addEventListener("click", async () => {
    const subject = subjectInput.value.trim();
    const body = bodyInput.value.trim();

    if (!subject && !body) {
        showError("Please enter an email subject or body.");
        return;
    }

    await analyzeEmail(subject, body);
});

analyzeEmlButton.addEventListener("click", async () => {
    const file = emlFileInput.files[0];

    if (!file) {
        showError("Please select an .eml file.");
        return;
    }

    if (!file.name.toLowerCase().endsWith(".eml")) {
        showError("Only .eml files are supported.");
        return;
    }

    hideError();
    resetResult();
    setLoading(true);

    try {
        const formData = new FormData();
        formData.append("file", file);

        const response = await fetch(
            "http://127.0.0.1:8000/predict-eml",
            {
                method: "POST",
                body: formData
            }
        );

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || "Server error.");
        }

        const data = await response.json();

        displayResult(
            data.prediction,
            data.phishing_percentage
        );
    } catch (err) {
        console.error(err);
        showError(err.message || "Could not connect to the backend.");
    } finally {
        setLoading(false);
    }
});

async function analyzeEmail(subject, body) {
    hideError();
    resetResult();
    setLoading(true);

    try {
        const response = await fetch(
            "http://127.0.0.1:8000/predict",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    subject: subject,
                    body: body
                })
            }
        );

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || "Server error.");
        }

        const data = await response.json();

        displayResult(
            data.prediction,
            data.phishing_percentage
        );
    } catch (err) {
        console.error(err);
        showError(
            "Could not connect to the backend. " +
            "Make sure FastAPI is running."
        );
    } finally {
        setLoading(false);
    }
}

function displayResult(predictionValue, phishingPercentage) {
    const percentage = Number(phishingPercentage);

    prediction.textContent = predictionValue;
    score.textContent = `${percentage.toFixed(2)}%`;
    responseMessage.textContent = getRiskResponse(percentage);

    result.classList.remove(
        "safe",
        "low",
        "suspicious",
        "high",
        "danger"
    );

    if (percentage < 20) {
        result.classList.add("safe");
        resultIcon.textContent = "✓";
    } else if (percentage < 40) {
        result.classList.add("low");
        resultIcon.textContent = "✓";
    } else if (percentage < 60) {
        result.classList.add("suspicious");
        resultIcon.textContent = "⚠";
    } else if (percentage < 80) {
        result.classList.add("high");
        resultIcon.textContent = "⚠";
    } else {
        result.classList.add("danger");
        resultIcon.textContent = "⚠";
    }

    result.classList.remove("hidden");
}

function getRiskResponse(percentage) {
    if (percentage < 20) {
        return "Very low risk. No strong phishing signals were detected.";
    }

    if (percentage < 40) {
        return (
            "Low risk. The email appears mostly safe, " +
            "but remain cautious with unexpected messages."
        );
    }

    if (percentage < 60) {
        return (
            "Suspicious. The model detected some characteristics " +
            "commonly associated with phishing emails."
        );
    }

    if (percentage < 80) {
        return (
            "High risk. This email shows several characteristics " +
            "associated with phishing."
        );
    }

    return "Very high risk. This email strongly resembles phishing content.";
}

function setLoading(isLoading) {
    if (isLoading) {
        loading.classList.remove("hidden");
        analyzeButton.disabled = true;
        analyzeEmlButton.disabled = true;
    } else {
        loading.classList.add("hidden");
        analyzeButton.disabled = false;
        analyzeEmlButton.disabled = false;
    }
}

function resetResult() {
    result.classList.add("hidden");
    result.classList.remove(
        "safe",
        "low",
        "suspicious",
        "high",
        "danger"
    );
}

function showError(message) {
    error.textContent = message;
    error.classList.remove("hidden");
}

function hideError() {
    error.classList.add("hidden");
}

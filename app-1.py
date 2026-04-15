"""
Flask web server for the Resume Screening AI System.
Run:  python app.py
Then open http://localhost:5000
"""

from flask import Flask, request, jsonify, render_template_string
import json
import os

from resume_screener import ResumeScreener

app = Flask(__name__)

# ──────────────────────────────────────────────
# HTML template (single-file, no extra files needed)
# ──────────────────────────────────────────────

HTML = open(os.path.join(os.path.dirname(__file__), "templates", "index.html")).read()


@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/api/screen", methods=["POST"])
def screen():
    """
    POST JSON body:
    {
        "job_description": "...",
        "resumes": [{"name": "...", "email": "...", "text": "..."}, ...],
        "top_n": 10
    }
    """
    data = request.get_json(force=True)

    job_description = data.get("job_description", "").strip()
    resumes = data.get("resumes", [])
    top_n = int(data.get("top_n", len(resumes)))

    if not job_description:
        return jsonify({"error": "job_description is required"}), 400
    if not resumes:
        return jsonify({"error": "At least one resume is required"}), 400

    # Validate resume structure
    for i, r in enumerate(resumes):
        if "name" not in r or "text" not in r:
            return jsonify({"error": f"Resume #{i+1} must have 'name' and 'text' fields"}), 400

    screener = ResumeScreener()
    results = screener.screen(job_description, resumes, top_n=top_n)
    return jsonify({"results": results, "total": len(resumes)})


if __name__ == "__main__":
    app.run(debug=True, port=5000)

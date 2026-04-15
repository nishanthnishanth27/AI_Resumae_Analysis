"""
Resume Screening AI System
Ranks resumes by relevance to a job description using NLP similarity.
"""

import re
import json
import math
from collections import Counter
from typing import List, Dict, Tuple


# ──────────────────────────────────────────────
# Text Preprocessing
# ──────────────────────────────────────────────

STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "shall", "can", "need", "this",
    "that", "these", "those", "i", "you", "he", "she", "it", "we", "they",
    "as", "if", "then", "than", "so", "not", "no", "nor", "yet", "both",
    "either", "each", "more", "most", "other", "some", "such", "into",
    "through", "during", "before", "after", "above", "below", "between",
    "out", "off", "over", "under", "again", "further", "also", "just",
    "our", "your", "their", "its", "my", "his", "her", "about", "up",
    "any", "all", "very", "too", "only", "own", "same", "while", "am",
}


def clean_text(text: str) -> str:
    """Lowercase, remove punctuation, collapse whitespace."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenize(text: str) -> List[str]:
    """Split cleaned text into tokens, removing stop words."""
    return [w for w in clean_text(text).split() if w not in STOP_WORDS and len(w) > 1]


def get_ngrams(tokens: List[str], n: int = 2) -> List[str]:
    """Return bigrams from token list."""
    return [" ".join(tokens[i:i+n]) for i in range(len(tokens) - n + 1)]


def build_feature_vector(text: str) -> List[str]:
    """Unigrams + bigrams for richer matching."""
    tokens = tokenize(text)
    return tokens + get_ngrams(tokens)


# ──────────────────────────────────────────────
# TF-IDF Vectoriser (from scratch)
# ──────────────────────────────────────────────

class TFIDFVectorizer:
    def __init__(self):
        self.vocab: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}

    def fit(self, documents: List[str]):
        """Build vocabulary and IDF weights from a corpus."""
        all_features = [build_feature_vector(d) for d in documents]

        # Build vocab
        vocab_set = set()
        for feats in all_features:
            vocab_set.update(feats)
        self.vocab = {w: i for i, w in enumerate(sorted(vocab_set))}

        # IDF: log((N+1) / (df+1)) + 1
        N = len(documents)
        df: Dict[str, int] = Counter()
        for feats in all_features:
            for w in set(feats):
                df[w] += 1

        self.idf = {
            w: math.log((N + 1) / (df.get(w, 0) + 1)) + 1
            for w in self.vocab
        }

    def transform(self, text: str) -> Dict[str, float]:
        """Return a TF-IDF weighted sparse vector (dict)."""
        features = build_feature_vector(text)
        tf = Counter(features)
        total = max(len(features), 1)
        vector: Dict[str, float] = {}
        for w, count in tf.items():
            if w in self.vocab:
                vector[w] = (count / total) * self.idf[w]
        return vector


# ──────────────────────────────────────────────
# Similarity
# ──────────────────────────────────────────────

def cosine_similarity(vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
    """Cosine similarity between two sparse vectors."""
    if not vec_a or not vec_b:
        return 0.0
    common_keys = set(vec_a) & set(vec_b)
    dot = sum(vec_a[k] * vec_b[k] for k in common_keys)
    norm_a = math.sqrt(sum(v ** 2 for v in vec_a.values()))
    norm_b = math.sqrt(sum(v ** 2 for v in vec_b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def keyword_overlap_bonus(resume: str, job_desc: str) -> float:
    """
    Bonus score for exact keyword matches (skills, tools, certifications).
    Returns a value in [0, 0.2].
    """
    resume_tokens = set(tokenize(resume))
    job_tokens = set(tokenize(job_desc))
    if not job_tokens:
        return 0.0
    overlap = len(resume_tokens & job_tokens) / len(job_tokens)
    return min(overlap * 0.2, 0.2)


# ──────────────────────────────────────────────
# Core Screener
# ──────────────────────────────────────────────

class ResumeScreener:
    """
    Main screening engine.

    Usage
    -----
    screener = ResumeScreener()
    results  = screener.screen(job_description, resumes)
    """

    def __init__(self):
        self.vectorizer = TFIDFVectorizer()

    def screen(
        self,
        job_description: str,
        resumes: List[Dict[str, str]],
        top_n: int = None,
    ) -> List[Dict]:
        """
        Parameters
        ----------
        job_description : str
            Full text of the job posting.
        resumes : list of dict
            Each dict must have 'name' and 'text' keys.
            Optional extra keys (email, phone, …) are preserved.
        top_n : int | None
            Return only the top-N candidates. None → return all.

        Returns
        -------
        Sorted list of result dicts with 'score', 'grade', 'matched_keywords'.
        """
        if not resumes:
            return []

        # Fit vectorizer on all documents (job desc + resumes)
        corpus = [job_description] + [r["text"] for r in resumes]
        self.vectorizer.fit(corpus)

        job_vec = self.vectorizer.transform(job_description)

        results = []
        for resume in resumes:
            res_vec = self.vectorizer.transform(resume["text"])
            base_score = cosine_similarity(job_vec, res_vec)
            bonus = keyword_overlap_bonus(resume["text"], job_description)
            final_score = min(base_score + bonus, 1.0)

            matched = self._matched_keywords(resume["text"], job_description)

            result = {**resume}          # preserve all original fields
            result["score"] = round(final_score * 100, 2)   # percentage
            result["grade"] = self._grade(final_score)
            result["matched_keywords"] = matched
            results.append(result)

        results.sort(key=lambda x: x["score"], reverse=True)

        if top_n is not None:
            results = results[:top_n]

        # Add rank
        for i, r in enumerate(results):
            r["rank"] = i + 1

        return results

    # ── Helpers ──────────────────────────────

    @staticmethod
    def _matched_keywords(resume: str, job_desc: str) -> List[str]:
        """Return top-15 shared meaningful tokens."""
        r_tokens = set(tokenize(resume))
        j_tokens = set(tokenize(job_desc))
        shared = r_tokens & j_tokens
        # sort by length (longer = more specific) then alpha
        return sorted(shared, key=lambda w: (-len(w), w))[:15]

    @staticmethod
    def _grade(score: float) -> str:
        if score >= 0.75:
            return "Excellent"
        if score >= 0.55:
            return "Good"
        if score >= 0.35:
            return "Fair"
        return "Poor"


# ──────────────────────────────────────────────
# CLI helper
# ──────────────────────────────────────────────

def screen_from_json(job_description: str, resumes_json: str, top_n: int = 5) -> str:
    """
    Convenience wrapper used by the web app (JavaScript fetch).

    Parameters
    ----------
    job_description : str
    resumes_json    : JSON array – [{"name": "...", "text": "..."}, ...]
    top_n           : int

    Returns
    -------
    JSON string with ranked results.
    """
    resumes = json.loads(resumes_json)
    screener = ResumeScreener()
    results = screener.screen(job_description, resumes, top_n=top_n)
    return json.dumps(results, indent=2)


# ──────────────────────────────────────────────
# Demo / quick test
# ──────────────────────────────────────────────

if __name__ == "__main__":
    JOB = """
    We are looking for a Senior Python Developer with experience in machine learning,
    NLP, and REST API development. The ideal candidate should have strong skills in
    scikit-learn, TensorFlow or PyTorch, FastAPI, and SQL databases. Experience with
    Docker, Kubernetes, and cloud platforms (AWS/GCP) is a plus. Strong communication
    and teamwork skills required.
    """

    RESUMES = [
        {
            "name": "Alice Johnson",
            "email": "alice@example.com",
            "text": """
            Experienced Python developer with 6 years building machine learning pipelines.
            Proficient in scikit-learn, PyTorch, and NLP frameworks (spaCy, HuggingFace).
            Developed REST APIs using FastAPI and Flask. Worked with PostgreSQL and Redis.
            Docker and Kubernetes experience. Deployed models on AWS SageMaker.
            Strong communicator and team player.
            """,
        },
        {
            "name": "Bob Martinez",
            "email": "bob@example.com",
            "text": """
            Full-stack web developer with 4 years experience. JavaScript, React, Node.js expert.
            Some Python scripting. Built e-commerce platforms and content management systems.
            MySQL database management. Git version control. Agile methodology.
            """,
        },
        {
            "name": "Carol Lee",
            "email": "carol@example.com",
            "text": """
            Data scientist with Python, R, and SQL skills. Used scikit-learn and TensorFlow
            for predictive modelling. Built NLP text classification models. Experience with
            FastAPI for model serving. GCP and BigQuery user. Team collaboration and
            documentation skills. Some Docker knowledge.
            """,
        },
        {
            "name": "David Kim",
            "email": "david@example.com",
            "text": """
            Junior Python programmer, 1 year experience. Completed online courses in
            machine learning. Familiar with pandas and NumPy. Basic SQL queries.
            Eager to learn REST API development and cloud platforms.
            """,
        },
        {
            "name": "Eva Rossi",
            "email": "eva@example.com",
            "text": """
            DevOps engineer specializing in Docker, Kubernetes, AWS, and GCP infrastructure.
            Python scripting for automation. CI/CD pipelines. Terraform. Strong communication.
            Some FastAPI exposure in microservices architecture. SQL database administration.
            """,
        },
    ]

    screener = ResumeScreener()
    results = screener.screen(JOB, RESUMES, top_n=5)

    print("\n" + "=" * 60)
    print("  RESUME SCREENING RESULTS")
    print("=" * 60)
    for r in results:
        print(f"\n#{r['rank']}  {r['name']}  |  Score: {r['score']}%  |  Grade: {r['grade']}")
        print(f"     Keywords: {', '.join(r['matched_keywords'][:8])}")
    print("\n" + "=" * 60)

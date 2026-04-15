"""
Unit tests for Resume Screening AI System.
Run:  python -m pytest tests.py -v
  or:  python tests.py
"""

import json
import sys
import unittest

from resume_screener import (
    clean_text,
    tokenize,
    get_ngrams,
    build_feature_vector,
    TFIDFVectorizer,
    cosine_similarity,
    keyword_overlap_bonus,
    ResumeScreener,
    screen_from_json,
)


# ──────────────────────────────────────────────
class TestTextPreprocessing(unittest.TestCase):

    def test_clean_text_lowercases(self):
        self.assertEqual(clean_text("HELLO World"), "hello world")

    def test_clean_text_removes_punctuation(self):
        result = clean_text("Hello, World! It's a test.")
        self.assertNotIn(",", result)
        self.assertNotIn("!", result)
        self.assertNotIn(".", result)

    def test_clean_text_collapses_whitespace(self):
        result = clean_text("  hello   world  ")
        self.assertEqual(result, "hello world")

    def test_tokenize_removes_stop_words(self):
        tokens = tokenize("the cat sat on the mat")
        self.assertNotIn("the", tokens)
        self.assertNotIn("on", tokens)
        self.assertIn("cat", tokens)
        self.assertIn("mat", tokens)

    def test_tokenize_removes_short_words(self):
        tokens = tokenize("a i am at")
        self.assertEqual(tokens, [])  # all stop words or length 1

    def test_get_ngrams(self):
        tokens = ["machine", "learning", "python"]
        bigrams = get_ngrams(tokens, 2)
        self.assertIn("machine learning", bigrams)
        self.assertIn("learning python", bigrams)
        self.assertEqual(len(bigrams), 2)

    def test_build_feature_vector_includes_bigrams(self):
        features = build_feature_vector("machine learning python developer")
        self.assertIn("machine", features)
        self.assertIn("machine learning", features)


# ──────────────────────────────────────────────
class TestTFIDFVectorizer(unittest.TestCase):

    def setUp(self):
        self.docs = [
            "python machine learning developer",
            "javascript react frontend developer",
            "python data science analytics",
        ]
        self.vec = TFIDFVectorizer()
        self.vec.fit(self.docs)

    def test_vocab_populated(self):
        self.assertGreater(len(self.vec.vocab), 0)

    def test_idf_populated(self):
        self.assertGreater(len(self.vec.idf), 0)

    def test_transform_returns_dict(self):
        v = self.vec.transform("python developer")
        self.assertIsInstance(v, dict)

    def test_transform_contains_relevant_keys(self):
        v = self.vec.transform("python developer")
        # 'python' should appear in vocab (common in training)
        self.assertTrue(any("python" in k for k in v))

    def test_transform_empty_string(self):
        v = self.vec.transform("")
        self.assertIsInstance(v, dict)

    def test_rare_word_higher_idf(self):
        # 'analytics' appears in 1 doc, 'python' in 2 → analytics has higher IDF
        idf_python = self.vec.idf.get("python", 0)
        idf_analytics = self.vec.idf.get("analytics", 0)
        self.assertGreater(idf_analytics, idf_python)


# ──────────────────────────────────────────────
class TestCosineSimilarity(unittest.TestCase):

    def test_identical_vectors(self):
        v = {"a": 1.0, "b": 2.0}
        self.assertAlmostEqual(cosine_similarity(v, v), 1.0)

    def test_orthogonal_vectors(self):
        v1 = {"a": 1.0}
        v2 = {"b": 1.0}
        self.assertAlmostEqual(cosine_similarity(v1, v2), 0.0)

    def test_empty_vector(self):
        self.assertEqual(cosine_similarity({}, {"a": 1.0}), 0.0)
        self.assertEqual(cosine_similarity({"a": 1.0}, {}), 0.0)

    def test_partial_overlap(self):
        v1 = {"a": 1.0, "b": 1.0}
        v2 = {"a": 1.0, "c": 1.0}
        sim = cosine_similarity(v1, v2)
        self.assertGreater(sim, 0.0)
        self.assertLess(sim, 1.0)

    def test_symmetry(self):
        v1 = {"a": 1.0, "b": 0.5}
        v2 = {"a": 0.8, "c": 1.2}
        self.assertAlmostEqual(cosine_similarity(v1, v2), cosine_similarity(v2, v1))


# ──────────────────────────────────────────────
class TestKeywordOverlapBonus(unittest.TestCase):

    def test_perfect_overlap(self):
        text = "python machine learning developer"
        bonus = keyword_overlap_bonus(text, text)
        self.assertGreater(bonus, 0.0)
        self.assertLessEqual(bonus, 0.2)

    def test_no_overlap(self):
        bonus = keyword_overlap_bonus("javascript react", "python machine learning")
        self.assertAlmostEqual(bonus, 0.0, places=2)

    def test_bonus_capped_at_0_2(self):
        long_text = " ".join(["python"] * 100)
        bonus = keyword_overlap_bonus(long_text, long_text)
        self.assertLessEqual(bonus, 0.2)

    def test_empty_job_desc(self):
        bonus = keyword_overlap_bonus("some resume text", "")
        self.assertEqual(bonus, 0.0)


# ──────────────────────────────────────────────
class TestResumeScreener(unittest.TestCase):

    def setUp(self):
        self.job = """
        Senior Python Developer with machine learning, NLP, REST API, FastAPI,
        scikit-learn, Docker, Kubernetes, AWS. Strong communication skills.
        """
        self.resumes = [
            {
                "name": "Alice",
                "text": "Python developer, machine learning, NLP, FastAPI, scikit-learn, Docker, AWS.",
            },
            {
                "name": "Bob",
                "text": "JavaScript, React, Node.js, frontend development, HTML, CSS.",
            },
            {
                "name": "Carol",
                "text": "Python, data science, scikit-learn, REST API, SQL, some Docker.",
            },
        ]
        self.screener = ResumeScreener()

    def test_returns_list(self):
        results = self.screener.screen(self.job, self.resumes)
        self.assertIsInstance(results, list)

    def test_returns_all_candidates(self):
        results = self.screener.screen(self.job, self.resumes)
        self.assertEqual(len(results), 3)

    def test_top_n_limits_results(self):
        results = self.screener.screen(self.job, self.resumes, top_n=2)
        self.assertEqual(len(results), 2)

    def test_sorted_descending(self):
        results = self.screener.screen(self.job, self.resumes)
        scores = [r["score"] for r in results]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_most_relevant_ranked_first(self):
        results = self.screener.screen(self.job, self.resumes)
        # Alice is clearly most relevant
        self.assertEqual(results[0]["name"], "Alice")

    def test_least_relevant_ranked_last(self):
        results = self.screener.screen(self.job, self.resumes)
        # Bob (JS developer) should rank last
        self.assertEqual(results[-1]["name"], "Bob")

    def test_score_is_percentage(self):
        results = self.screener.screen(self.job, self.resumes)
        for r in results:
            self.assertGreaterEqual(r["score"], 0)
            self.assertLessEqual(r["score"], 100)

    def test_rank_field_present(self):
        results = self.screener.screen(self.job, self.resumes)
        for i, r in enumerate(results):
            self.assertEqual(r["rank"], i + 1)

    def test_grade_field_valid(self):
        results = self.screener.screen(self.job, self.resumes)
        valid_grades = {"Excellent", "Good", "Fair", "Poor"}
        for r in results:
            self.assertIn(r["grade"], valid_grades)

    def test_matched_keywords_is_list(self):
        results = self.screener.screen(self.job, self.resumes)
        for r in results:
            self.assertIsInstance(r["matched_keywords"], list)

    def test_empty_resumes(self):
        results = self.screener.screen(self.job, [])
        self.assertEqual(results, [])

    def test_preserves_extra_fields(self):
        resumes = [{"name": "Test", "text": "python developer", "email": "t@t.com"}]
        results = self.screener.screen(self.job, resumes)
        self.assertEqual(results[0]["email"], "t@t.com")

    def test_single_resume(self):
        results = self.screener.screen(self.job, [self.resumes[0]])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["rank"], 1)


# ──────────────────────────────────────────────
class TestScreenFromJson(unittest.TestCase):

    def test_returns_json_string(self):
        job = "Python developer machine learning"
        resumes = json.dumps([{"name": "X", "text": "Python developer"}])
        result = screen_from_json(job, resumes, top_n=1)
        parsed = json.loads(result)
        self.assertIsInstance(parsed, list)
        self.assertEqual(len(parsed), 1)

    def test_invalid_json_raises(self):
        with self.assertRaises(json.JSONDecodeError):
            screen_from_json("job", "not json")


# ──────────────────────────────────────────────
if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)

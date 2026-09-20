import tempfile
import unittest
from pathlib import Path

from recommend import (
    Movie,
    MovieCatalog,
    RecommendationEngine,
    ViewingHistory,
    ViewingHistoryRepository,
)


class MovieCatalogTests(unittest.TestCase):
    def test_from_file_parses_movies(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "movies.csv"
            path.write_text("1,Мстители: Финал\n2,Хатико\n", encoding="utf-8")

            catalog = MovieCatalog.from_file(path)

            self.assertEqual(catalog.title(1), "Мстители: Финал")
            self.assertEqual(catalog.title(2), "Хатико")

    def test_skips_empty_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "movies.csv"
            path.write_text("1,Дюна\n\n2,Хатико\n", encoding="utf-8")

            catalog = MovieCatalog.from_file(path)

            self.assertEqual(catalog.title(1), "Дюна")
            self.assertEqual(catalog.title(2), "Хатико")


class ViewingHistoryTests(unittest.TestCase):
    def test_unique_ids(self):
        history = ViewingHistory([2, 2, 2, 2, 2, 3])
        self.assertEqual(history.unique_ids, {2, 3})

    def test_overlap_ratio(self):
        history = ViewingHistory([1, 2, 3])
        self.assertEqual(history.overlap_ratio({2, 4}), 0.5)
        self.assertEqual(history.overlap_ratio({5, 6}), 0.0)
        self.assertEqual(history.overlap_ratio(set()), 0.0)

    def test_occurrences(self):
        history = ViewingHistory([2, 2, 3])
        self.assertEqual(history.occurrences(), {2: 2, 3: 1})


class RecommendationEngineTests(unittest.TestCase):
    SAMPLE_MOVIES = "1,Мстители: Финал\n2,Хатико\n3,Дюна\n4,Унесенные призраками\n"
    SAMPLE_HISTORIES = "2,1,3\n1,4,3\n2,2,2,2,2,3\n"

    def _build_engine(self, min_overlap_ratio: float = 0.5) -> RecommendationEngine:
        catalog = MovieCatalog(
            [
                Movie(1, "Мстители: Финал"),
                Movie(2, "Хатико"),
                Movie(3, "Дюна"),
                Movie(4, "Унесенные призраками"),
            ]
        )
        repository = ViewingHistoryRepository(
            [
                ViewingHistory([2, 1, 3]),
                ViewingHistory([1, 4, 3]),
                ViewingHistory([2, 2, 2, 2, 2, 3]),
            ]
        )
        return RecommendationEngine(catalog, repository, min_overlap_ratio)

    def test_example_from_spec(self):
        engine = self._build_engine()
        self.assertEqual(engine.recommend([2, 4]), "Дюна")

    def test_recommend_excludes_already_watched(self):
        engine = self._build_engine()
        recommendation = engine.recommend([2, 1, 3])
        self.assertEqual(recommendation, "Унесенные призраками")

    def test_no_similar_users_returns_none(self):
        catalog = MovieCatalog([Movie(1, "A"), Movie(2, "B")])
        repository = ViewingHistoryRepository([ViewingHistory([1])])
        engine = RecommendationEngine(catalog, repository)
        self.assertIsNone(engine.recommend([2]))

    def test_weighted_mode_favours_higher_overlap(self):
        catalog = MovieCatalog([Movie(1, "A"), Movie(2, "B"), Movie(3, "C"), Movie(4, "D")])
        repository = ViewingHistoryRepository(
            [
                ViewingHistory([1, 2, 3]),
                ViewingHistory([1, 4, 4]),
            ]
        )
        engine = RecommendationEngine(catalog, repository)

        self.assertEqual(engine.recommend([1, 2], weighted=False), "D")
        engine_weighted = engine
        self.assertIn(engine_weighted.recommend([1, 2], weighted=True), {"C", "D"})


if __name__ == "__main__":
    unittest.main()

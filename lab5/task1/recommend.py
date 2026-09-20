from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

MOVIES_FILE = "movies.csv"
HISTORIES_FILE = "histories.csv"
MIN_OVERLAP_RATIO = 0.5


@dataclass(frozen=True)
class Movie:
    movie_id: int
    title: str


class MovieCatalog:

    def __init__(self, movies: list[Movie]):
        self._by_id: dict[int, Movie] = {movie.movie_id: movie for movie in movies}

    @classmethod
    def from_file(cls, path: str | Path) -> "MovieCatalog":
        movies: list[Movie] = []
        with Path(path).open("r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue
                movie_id_str, title = line.split(",", 1)
                movies.append(Movie(int(movie_id_str), title.strip()))
        return cls(movies)

    def title(self, movie_id: int) -> str:
        return self._by_id[movie_id].title


class ViewingHistory:

    def __init__(self, movie_ids: list[int]):
        self.movie_ids = movie_ids

    @property
    def unique_ids(self) -> set[int]:
        return set(self.movie_ids)

    def overlap_ratio(self, target_ids: set[int]) -> float:
        if not target_ids:
            return 0.0
        common = len(self.unique_ids & target_ids)
        return common / len(target_ids)

    def occurrences(self) -> Counter:
        return Counter(self.movie_ids)


class ViewingHistoryRepository:

    def __init__(self, histories: list[ViewingHistory]):
        self.histories = histories

    @classmethod
    def from_file(cls, path: str | Path) -> "ViewingHistoryRepository":
        histories: list[ViewingHistory] = []
        with Path(path).open("r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue
                ids = [int(item) for item in line.split(",")]
                histories.append(ViewingHistory(ids))
        return cls(histories)


class RecommendationEngine:

    def __init__(
        self,
        catalog: MovieCatalog,
        repository: ViewingHistoryRepository,
        min_overlap_ratio: float = MIN_OVERLAP_RATIO,
    ):
        self._catalog = catalog
        self._repository = repository
        self._min_overlap_ratio = min_overlap_ratio

    def _similar_histories(self, target_ids: set[int]) -> list[tuple[ViewingHistory, float]]:
        result = []
        for history in self._repository.histories:
            ratio = history.overlap_ratio(target_ids)
            if ratio >= self._min_overlap_ratio:
                result.append((history, ratio))
        return result

    def recommend(self, watched_ids: list[int], weighted: bool = False) -> str | None:
        target_ids = set(watched_ids)
        similar = self._similar_histories(target_ids)

        scores: Counter = Counter()
        for history, ratio in similar:
            weight = ratio if weighted else 1.0
            for movie_id, count in history.occurrences().items():
                if movie_id in target_ids:
                    continue
                scores[movie_id] += count * weight

        if not scores:
            return None

        best_movie_id = max(scores, key=lambda movie_id: scores[movie_id])
        return self._catalog.title(best_movie_id)


def main() -> None:
    catalog = MovieCatalog.from_file(MOVIES_FILE)
    repository = ViewingHistoryRepository.from_file(HISTORIES_FILE)
    engine = RecommendationEngine(catalog, repository)

    user_input = input().strip()
    watched_ids = [int(item) for item in user_input.split(",") if item.strip()]

    recommendation = engine.recommend(watched_ids)
    print(recommendation if recommendation is not None else "")


if __name__ == "__main__":
    main()

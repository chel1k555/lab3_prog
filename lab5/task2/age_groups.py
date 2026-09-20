from __future__ import annotations

import sys
from dataclasses import dataclass

MAX_AGE = 123


@dataclass(frozen=True)
class Respondent:
    full_name: str
    age: int


class AgeGroup:

    def __init__(self, lower: int, upper: int | None):
        self.lower = lower
        self.upper = upper
        self.respondents: list[Respondent] = []

    @property
    def label(self) -> str:
        if self.upper is None:
            return f"{self.lower}+"
        return f"{self.lower}-{self.upper}"

    def contains(self, age: int) -> bool:
        if self.upper is None:
            return age >= self.lower
        return self.lower <= age <= self.upper

    def add(self, respondent: Respondent) -> None:
        self.respondents.append(respondent)

    def sorted_respondents(self) -> list[Respondent]:
        return sorted(self.respondents, key=lambda r: (-r.age, r.full_name))

    def format_line(self) -> str:
        people = ", ".join(f"{r.full_name} ({r.age})" for r in self.sorted_respondents())
        return f"{self.label}: {people}"


class AgeGroupBuilder:

    def __init__(self, boundaries: list[int]):
        if not boundaries:
            raise ValueError("At least one boundary is required")
        self._boundaries = boundaries

    def build(self) -> list[AgeGroup]:
        groups: list[AgeGroup] = []
        lower = 0
        for boundary in self._boundaries:
            groups.append(AgeGroup(lower, boundary))
            lower = boundary + 1
        groups.append(AgeGroup(lower, None))
        return groups


class Classifier:

    def __init__(self, groups: list[AgeGroup]):
        self._groups = groups

    def classify(self, respondent: Respondent) -> None:
        for group in self._groups:
            if group.contains(respondent.age):
                group.add(respondent)
                return
        raise ValueError(f"No group found for age {respondent.age}")

    def report_lines(self) -> list[str]:
        lines = []
        for group in reversed(self._groups):
            if group.respondents:
                lines.append(group.format_line())
        return lines


def read_respondents(lines) -> list[Respondent]:
    respondents = []
    for raw_line in lines:
        line = raw_line.strip()
        if line == "END":
            break
        if not line:
            continue
        full_name, age_str = line.rsplit(",", 1)
        respondents.append(Respondent(full_name.strip(), int(age_str.strip())))
    return respondents


def main() -> None:
    boundaries = [int(arg) for arg in sys.argv[1:]]
    groups = AgeGroupBuilder(boundaries).build()
    classifier = Classifier(groups)

    for respondent in read_respondents(sys.stdin):
        classifier.classify(respondent)

    for line in classifier.report_lines():
        print(line)


if __name__ == "__main__":
    main()

import unittest

from age_groups import (
    AgeGroup,
    AgeGroupBuilder,
    Classifier,
    Respondent,
    read_respondents,
)


class AgeGroupBuilderTests(unittest.TestCase):
    def test_build_groups_from_boundaries(self):
        builder = AgeGroupBuilder([18, 25, 35])
        groups = builder.build()

        labels = [g.label for g in groups]
        self.assertEqual(labels, ["0-18", "19-25", "26-35", "36+"])

    def test_empty_boundaries_raises(self):
        with self.assertRaises(ValueError):
            AgeGroupBuilder([]).build()


class AgeGroupTests(unittest.TestCase):
    def test_contains_bounded_group(self):
        group = AgeGroup(19, 25)
        self.assertFalse(group.contains(18))
        self.assertTrue(group.contains(19))
        self.assertTrue(group.contains(25))
        self.assertFalse(group.contains(26))

    def test_contains_open_ended_group(self):
        group = AgeGroup(101, None)
        self.assertTrue(group.contains(101))
        self.assertTrue(group.contains(123))
        self.assertFalse(group.contains(100))

    def test_sorted_respondents_by_age_desc_then_name_asc(self):
        group = AgeGroup(0, 100)
        group.add(Respondent("Борисов Борис", 30))
        group.add(Respondent("Аникин Антон", 30))
        group.add(Respondent("Васильев Иван", 40))

        ordered = [r.full_name for r in group.sorted_respondents()]
        self.assertEqual(
            ordered, ["Васильев Иван", "Аникин Антон", "Борисов Борис"]
        )

    def test_format_line(self):
        group = AgeGroup(0, 18)
        group.add(Respondent("Соколов Андрей Сергеевич", 15))
        group.add(Respondent("Егоров Алан Петрович", 7))

        self.assertEqual(
            group.format_line(),
            "0-18: Соколов Андрей Сергеевич (15), Егоров Алан Петрович (7)",
        )


class ReadRespondentsTests(unittest.TestCase):
    def test_stops_at_end_marker(self):
        lines = ["Иванов Иван,20", "Петров Петр,30", "END", "Сидоров Сидор,40"]
        respondents = read_respondents(lines)

        self.assertEqual(
            respondents,
            [Respondent("Иванов Иван", 20), Respondent("Петров Петр", 30)],
        )

    def test_skips_blank_lines(self):
        lines = ["Иванов Иван,20", "", "  ", "END"]
        respondents = read_respondents(lines)
        self.assertEqual(respondents, [Respondent("Иванов Иван", 20)])


class ClassifierIntegrationTests(unittest.TestCase):
    def test_example_from_spec(self):
        boundaries = [18, 25, 35, 45, 60, 80, 100]
        groups = AgeGroupBuilder(boundaries).build()
        classifier = Classifier(groups)

        respondents = [
            Respondent("Кошельков Захар Брониславович", 105),
            Respondent("Дьячков Нисон Иринеевич", 88),
            Respondent("Иванов Варлам Якунович", 88),
            Respondent("Старостин Ростислав Ермолаевич", 50),
            Respondent("Ярилова Розалия Трофимовна", 29),
            Respondent("Соколов Андрей Сергеевич", 15),
            Respondent("Егоров Алан Петрович", 7),
        ]
        for r in respondents:
            classifier.classify(r)

        expected = [
            "101+: Кошельков Захар Брониславович (105)",
            "81-100: Дьячков Нисон Иринеевич (88), Иванов Варлам Якунович (88)",
            "46-60: Старостин Ростислав Ермолаевич (50)",
            "26-35: Ярилова Розалия Трофимовна (29)",
            "0-18: Соколов Андрей Сергеевич (15), Егоров Алан Петрович (7)",
        ]
        self.assertEqual(classifier.report_lines(), expected)

    def test_empty_groups_are_omitted(self):
        boundaries = [18, 25, 35]
        groups = AgeGroupBuilder(boundaries).build()
        classifier = Classifier(groups)
        classifier.classify(Respondent("Иванов Иван", 10))

        self.assertEqual(classifier.report_lines(), ["0-18: Иванов Иван (10)"])


if __name__ == "__main__":
    unittest.main()

import unittest

from evaluator import evaluate_gear, parse_gear


class EvaluatorTests(unittest.TestCase):
    def test_parse_ocr_text(self):
        gear = parse_gear(
            "Level 85\nMain Stat: Attack%\nSpeed 5\nCritical Hit Chance 8%\nAttack 8%"
        )
        self.assertEqual(gear.level, 85)
        self.assertEqual(len(gear.substats), 3)
        self.assertEqual(gear.substats[0].name, "speed")

    def test_strong_gear_is_roll_recommendation(self):
        gear = parse_gear("Speed 5\nCritical Hit Chance 8%\nAttack 8%")
        evaluation = evaluate_gear(gear)
        self.assertEqual(evaluation.recommendation, "Roll")
        self.assertGreaterEqual(evaluation.score, 65)

    def test_game_screen_stat_layout_is_parsed(self):
        gear = parse_gear(
            "Health 540\n"
            "Critical Hit Damage 7%\n"
            "Defense 5%\n"
            "Health 6%\n"
            "Attack 8%"
        )
        self.assertEqual(
            [(stat.name, stat.value) for stat in gear.substats],
            [
                ("critical hit damage", 7.0),
                ("defense", 5.0),
                ("health", 6.0),
                ("attack", 8.0),
            ],
        )

    def test_missing_substats_are_explicit(self):
        evaluation = evaluate_gear(parse_gear("Level 85"))
        self.assertEqual(evaluation.recommendation, "Insufficient data")


if __name__ == "__main__":
    unittest.main()

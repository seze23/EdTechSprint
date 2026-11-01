from app.mathcheck import check, reference_solutions


def test_reference_solution_from_prompt():
    assert reference_solutions("Solve 3x + 7 = 22 for x") == [5.0]
    assert reference_solutions("Explain photosynthesis") is None


def test_check_scores():
    assert check("Solve 3x + 7 = 22 for x", ["x = 5", "4", "", "5.0"]) == [1.0, 0.0, 0.5, 1.0]
    assert check("Explain photosynthesis", ["light"]) == [0.5]

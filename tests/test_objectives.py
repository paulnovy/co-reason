from backend.app.api.objectives import ObjectiveSpec, ObjectiveKind, score_point


def test_objective_maximize_variable():
    obj = ObjectiveSpec(kind=ObjectiveKind.maximize_variable, variable_id=1)
    assert score_point({"1": 10.0}, obj) == 10.0


def test_objective_minimize_variable():
    obj = ObjectiveSpec(kind=ObjectiveKind.minimize_variable, variable_id=1)
    assert score_point({"1": 10.0}, obj) == -10.0

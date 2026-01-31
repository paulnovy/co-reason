from backend.app.api.objectives import LinearTerm, ObjectiveSpec, ObjectiveKind, score_point


def test_objective_maximize_variable():
    obj = ObjectiveSpec(kind=ObjectiveKind.maximize_variable, variable_id=1)
    assert score_point({"1": 10.0}, obj) == 10.0


def test_objective_minimize_variable():
    obj = ObjectiveSpec(kind=ObjectiveKind.minimize_variable, variable_id=1)
    assert score_point({"1": 10.0}, obj) == -10.0


def test_objective_linear():
    obj = ObjectiveSpec(
        kind=ObjectiveKind.linear,
        terms=[LinearTerm(variable_id=1, weight=2.0), LinearTerm(variable_id=2, weight=-1.0)],
    )
    # 2*x1 - 1*x2
    assert score_point({"1": 3.0, "2": 5.0}, obj) == 1.0


def test_objective_target_abs():
    obj = ObjectiveSpec(kind=ObjectiveKind.target, variable_id=1, target=10.0, loss="abs")
    assert score_point({"1": 13.0}, obj) == -3.0


def test_objective_target_squared():
    obj = ObjectiveSpec(kind=ObjectiveKind.target, variable_id=1, target=10.0, loss="squared")
    assert score_point({"1": 13.0}, obj) == -9.0

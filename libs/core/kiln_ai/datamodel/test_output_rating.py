import pytest
from kiln_ai.datamodel import TaskOutputRating, TaskOutputRatingType
from pydantic import ValidationError


def test_valid_task_output_rating():
    rating = TaskOutputRating(value=4.0, requirement_ratings={"req1": 5.0, "req2": 3.0})
    assert rating.type == TaskOutputRatingType.five_star
    assert rating.value == 4.0
    assert rating.requirement_ratings == {"req1": 5.0, "req2": 3.0}


def test_invalid_rating_type():
    with pytest.raises(ValidationError, match="Input should be"):
        TaskOutputRating(type="invalid_type", value=4.0)


def test_invalid_rating_value():
    with pytest.raises(
        ValidationError,
        match="Overall rating of type five_star must be an integer value",
    ):
        TaskOutputRating(value=3.5)


def test_rating_out_of_range():
    with pytest.raises(
        ValidationError,
        match="Overall rating of type five_star must be between 1 and 5 stars",
    ):
        TaskOutputRating(value=6.0)


def test_rating_below_range():
    with pytest.raises(
        ValidationError,
        match="Overall rating of type five_star must be between 1 and 5 stars",
    ):
        TaskOutputRating(value=0.0)


def test_valid_requirement_ratings():
    rating = TaskOutputRating(
        value=4.0, requirement_ratings={"req1": 5.0, "req2": 3.0, "req3": 1.0}
    )
    assert rating.requirement_ratings == {"req1": 5.0, "req2": 3.0, "req3": 1.0}


def test_invalid_requirement_rating_value():
    with pytest.raises(
        ValidationError,
        match="Requirement rating for req1 of type five_star must be an integer value",
    ):
        TaskOutputRating(value=4.0, requirement_ratings={"req1": 3.5})


def test_requirement_rating_out_of_range():
    with pytest.raises(
        ValidationError,
        match="Requirement rating for req1 of type five_star must be between 1 and 5 stars",
    ):
        TaskOutputRating(value=4.0, requirement_ratings={"req1": 6.0})


def test_empty_requirement_ratings():
    rating = TaskOutputRating(value=4.0)
    assert rating.requirement_ratings == {}


def test_invalid_id_type():
    with pytest.raises(ValidationError):
        TaskOutputRating(
            value=4.0,
            requirement_ratings={
                123: 4.0  # Assuming ID_TYPE is str
            },
        )


def test_valid_custom_rating():
    rating = TaskOutputRating(
        type=TaskOutputRatingType.custom,
        value=31.459,
        requirement_ratings={"req1": 42.0, "req2": 3.14},
    )
    assert rating.type == TaskOutputRatingType.custom
    assert rating.value == 31.459
    assert rating.requirement_ratings == {"req1": 42.0, "req2": 3.14}

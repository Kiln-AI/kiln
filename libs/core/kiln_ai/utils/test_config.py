import os

import pytest

from libs.core.kiln_ai.utils.config import Config, ConfigProperty


def TestConfig():
    return Config(
        properties={
            "example_property": ConfigProperty(
                str, default="default_value", env_var="EXAMPLE_PROPERTY"
            ),
        }
    )


@pytest.fixture
def reset_config():
    Config._shared_instance = None
    yield
    Config._shared_instance = None


def test_shared_instance(reset_config):
    config1 = Config.shared()
    config2 = Config.shared()
    assert config1 is config2


def test_separate_instances(reset_config):
    config1 = TestConfig()
    config2 = TestConfig()
    assert config1 is not config2


def test_property_default_value(reset_config):
    config = TestConfig()
    assert config.example_property == "default_value"


def test_property_env_var(reset_config):
    os.environ["EXAMPLE_PROPERTY"] = "env_value"
    config = TestConfig()
    assert config.example_property == "env_value"
    del os.environ["EXAMPLE_PROPERTY"]


def test_property_setter(reset_config):
    config = TestConfig()
    config.example_property = "new_value"
    assert config.example_property == "new_value"


def test_nonexistent_property(reset_config):
    config = TestConfig()
    with pytest.raises(AttributeError):
        config.nonexistent_property


def test_property_type_conversion(reset_config):
    Config._shared_instance = None

    config = Config(properties={"int_property": ConfigProperty(int, default="42")})
    assert isinstance(config.int_property, int)
    assert config.int_property == 42


def test_property_priority(reset_config):
    os.environ["EXAMPLE_PROPERTY"] = "env_value"
    config = TestConfig()

    # Environment variable takes precedence over default
    assert config.example_property == "env_value"

    # Setter takes precedence over environment variable
    config.example_property = "new_value"
    assert config.example_property == "new_value"

    del os.environ["EXAMPLE_PROPERTY"]


def test_lazy_loading(reset_config):
    config = TestConfig()
    assert "example_property" not in config._values
    _ = config.example_property
    assert "example_property" in config._values


def test_default_lambda(reset_config):
    Config._shared_instance = None

    def default_lambda():
        return "lambda_value"

    config = Config(
        properties={
            "lambda_property": ConfigProperty(str, default_lambda=default_lambda)
        }
    )

    assert config.lambda_property == "lambda_value"

    # Test that the lambda is only called once
    assert "lambda_property" in config._values
    config._properties["lambda_property"].default_lambda = lambda: "new_lambda_value"
    assert config.lambda_property == "lambda_value"


def test_user_id_default(reset_config):
    config = Config()
    # assert config.user_id == "scosman"
    assert len(config.user_id) > 0

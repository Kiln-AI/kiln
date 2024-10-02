import os
import pwd
from typing import Any, Callable, Dict, Optional


class ConfigProperty:
    def __init__(
        self,
        type_: type,
        default: Any = None,
        env_var: Optional[str] = None,
        default_lambda: Optional[Callable[[], Any]] = None,
    ):
        self.type = type_
        self.default = default
        self.env_var = env_var
        self.default_lambda = default_lambda


class Config:
    _shared_instance = None

    def __init__(self, properties: Dict[str, ConfigProperty] | None = None):
        self._values: Dict[str, Any] = {}
        self._properties: Dict[str, ConfigProperty] = properties or {
            "user_id": ConfigProperty(
                str,
                env_var="KILN_USER_ID",
                default_lambda=_get_user_id,
            ),
            "autosave_examples": ConfigProperty(
                bool,
                env_var="KILN_AUTOSAVE_EXAMPLES",
                default=True,
            ),
            "open_ai_api_key": ConfigProperty(
                str,
                env_var="OPENAI_API_KEY",
            ),
            "groq_api_key": ConfigProperty(
                str,
                env_var="GROQ_API_KEY",
            ),
        }

    @classmethod
    def shared(cls):
        if cls._shared_instance is None:
            cls._shared_instance = cls()
        return cls._shared_instance

    def __getattr__(self, name: str) -> Any:
        if name not in self._properties:
            raise AttributeError(f"Config has no attribute '{name}'")

        if name not in self._values:
            prop = self._properties[name]
            value = None
            if prop.env_var and prop.env_var in os.environ:
                value = os.environ[prop.env_var]
            elif prop.default is not None:
                value = prop.default
            elif prop.default_lambda is not None:
                value = prop.default_lambda()
            self._values[name] = prop.type(value) if value is not None else None

        return self._values[name]

    def __setattr__(self, name: str, value: Any) -> None:
        if name in ("_values", "_properties"):
            super().__setattr__(name, value)
        elif name in self._properties:
            self._values[name] = self._properties[name].type(value)
        else:
            raise AttributeError(f"Config has no attribute '{name}'")


def _get_user_id():
    try:
        return pwd.getpwuid(os.getuid()).pw_name or "unknown_user"
    except Exception:
        return "unknown_user"

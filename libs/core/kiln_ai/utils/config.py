import os
import pwd
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import yaml


class ConfigProperty:
    def __init__(
        self,
        type_: type,
        default: Any = None,
        env_var: Optional[str] = None,
        default_lambda: Optional[Callable[[], Any]] = None,
        sensitive: bool = False,
    ):
        self.type = type_
        self.default = default
        self.env_var = env_var
        self.default_lambda = default_lambda
        self.sensitive = sensitive


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
                sensitive=True,
            ),
            "groq_api_key": ConfigProperty(
                str,
                env_var="GROQ_API_KEY",
                sensitive=True,
            ),
            "ollama_base_url": ConfigProperty(
                str,
                env_var="OLLAMA_BASE_URL",
            ),
            "bedrock_access_key": ConfigProperty(
                str,
                env_var="AWS_ACCESS_KEY_ID",
                sensitive=True,
            ),
            "bedrock_secret_key": ConfigProperty(
                str,
                env_var="AWS_SECRET_ACCESS_KEY",
                sensitive=True,
            ),
            "open_router_api_key": ConfigProperty(
                str,
                env_var="OPENROUTER_API_KEY",
                sensitive=True,
            ),
            "projects": ConfigProperty(
                list,
                default_lambda=lambda: [],
            ),
            "current_project": ConfigProperty(
                str,
            ),
        }
        self._settings = self.load_settings()

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
            if name in self._settings:
                value = self._settings[name]
            elif prop.env_var and prop.env_var in os.environ:
                value = os.environ[prop.env_var]
            elif prop.default is not None:
                value = prop.default
            elif prop.default_lambda is not None:
                value = prop.default_lambda()
            self._values[name] = prop.type(value) if value is not None else None

        return self._values[name]

    def __setattr__(self, name: str, value: Any) -> None:
        if name in ("_values", "_properties", "_settings"):
            super().__setattr__(name, value)
        elif name in self._properties:
            self._values[name] = self._properties[name].type(value)
            self.save_setting(name, value)
        else:
            raise AttributeError(f"Config has no attribute '{name}'")

    @classmethod
    def settings_path(cls, create=True):
        settings_dir = os.path.join(Path.home(), ".kiln_ai")
        if create and not os.path.exists(settings_dir):
            os.makedirs(settings_dir)
        return os.path.join(settings_dir, "settings.yaml")

    @classmethod
    def load_settings(cls):
        if not os.path.isfile(cls.settings_path(create=False)):
            return {}
        with open(cls.settings_path(), "r") as f:
            settings = yaml.safe_load(f.read()) or {}
        return settings

    def settings(self, hide_sensitive=False):
        if hide_sensitive:
            return {
                k: "[hidden]"
                if k in self._properties and self._properties[k].sensitive
                else v
                for k, v in self._settings.items()
            }
        return self._settings

    def save_setting(self, name: str, value: Any):
        self.update_settings({name: value})

    def update_settings(self, new_settings: Dict[str, Any]):
        # fresh load so we don't clobber other instances
        self._settings = self.load_settings()
        self._settings.update(new_settings)
        for name, value in new_settings.items():
            if value is None:
                del self._settings[name]
        with open(self.settings_path(), "w") as f:
            yaml.dump(self._settings, f)
        self._settings = self.load_settings()


def _get_user_id():
    try:
        return pwd.getpwuid(os.getuid()).pw_name or "unknown_user"
    except Exception:
        return "unknown_user"

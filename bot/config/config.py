from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)

    API_ID: int
    API_HASH: str


    REF_LINK: str = "https://t.me/fabrika/app?startapp=ref_814151"
    SQUAD_ID: int = 646

    AUTO_TASK: bool = True

    AUTO_BOOST: bool = True
    AUTO_TAP: bool = True
    TAP_COUNT: list[int] = [30, 75]
    SLEEP_BY_MIN_ENERGY: int = 100
    SLEEP_BETWEEN_TAPS: list[int] = [15, 30]


    AUTO_MANAGE_FACTORY: bool = True
    AUTO_BUY_WORKER: bool = True
    MAX_NUMBER_OF_WORKER_TO_BUY: int = 10
    AUTO_BUY_WORKING_PLACE: bool = True
    MAX_NUMBER_OF_WORKING_PLACE_TO_BUY: int = 10 # Max is 20

    ADVANCED_ANTI_DETECTION: bool = True

    DELAY_EACH_ACCOUNT: list[int] = [20, 30]

    USE_PROXY_FROM_FILE: bool = False


settings = Settings()


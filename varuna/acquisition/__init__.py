"""VARUNA satellite acquisition package."""
from varuna.acquisition.cdse import (
    DiscoveredRadarScene,
    ScenePairRecommendation,
    CDSEDiscoveryService,
    CDSEDiscoveryError,
    IncompatibleScenePairError,
)
from varuna.acquisition.download import (
    CDSEDownloader,
    AuthenticationRequiredError,
    DownloadFailedError,
)

__all__ = [
    "DiscoveredRadarScene",
    "ScenePairRecommendation",
    "CDSEDiscoveryService",
    "CDSEDiscoveryError",
    "IncompatibleScenePairError",
    "CDSEDownloader",
    "AuthenticationRequiredError",
    "DownloadFailedError",
]

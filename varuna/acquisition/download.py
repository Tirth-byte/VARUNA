"""Copernicus Data Space Ecosystem (CDSE) Authentication & Scene Download.

Official Keycloak Identity & Download Endpoint:
- Token URL: https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token
- Download URL: https://catalogue.dataspace.copernicus.eu/odata/v1/Products({product_id})/$value
  or https://zipper.dataspace.copernicus.eu/odata/v1/Products({product_id})/$value
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import httpx

logger = logging.getLogger("varuna.acquisition.download")

CDSE_TOKEN_URL = os.getenv(
    "CDSE_TOKEN_URL",
    "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
)


class AuthenticationRequiredError(PermissionError):
    """Raised when Copernicus credentials are required but missing or invalid."""
    pass


class DownloadFailedError(RuntimeError):
    """Raised when an authentic download attempt fails."""
    pass


class CDSEDownloader:
    """Manages CDSE OAuth2 / Keycloak authentication and secure product download."""

    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        token_url: str = CDSE_TOKEN_URL,
    ):
        self.username = username or os.getenv("CDSE_USERNAME")
        self.password = password or os.getenv("CDSE_PASSWORD")
        self.client_id = client_id or os.getenv("CDSE_CLIENT_ID", "cdse-public")
        self.client_secret = client_secret or os.getenv("CDSE_CLIENT_SECRET")
        self.token_url = token_url
        self._access_token: Optional[str] = None

    def has_credentials(self) -> bool:
        """Check if sufficient credentials exist in environment or instance."""
        if self.username and self.password:
            return True
        if self.client_id and self.client_secret and self.client_id != "cdse-public":
            return True
        return False

    def acquire_token(self) -> str:
        """Exchange user credentials or client credentials for a Keycloak JWT access token."""
        if not self.has_credentials():
            raise AuthenticationRequiredError(
                "Missing CDSE credentials. To download authentic Sentinel imagery from Copernicus, "
                "set CDSE_USERNAME and CDSE_PASSWORD (or CDSE_CLIENT_ID and CDSE_CLIENT_SECRET) in .env. "
                "Register free at https://dataspace.copernicus.eu"
            )

        data: Dict[str, str] = {}
        if self.username and self.password:
            data = {
                "client_id": self.client_id or "cdse-public",
                "username": self.username,
                "password": self.password,
                "grant_type": "password",
            }
        elif self.client_secret:
            data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials",
            }

        try:
            with httpx.Client(timeout=20.0) as client:
                resp = client.post(self.token_url, data=data)
                resp.raise_for_status()
                token_data = resp.json()
                self._access_token = token_data.get("access_token")
                if not self._access_token:
                    raise AuthenticationRequiredError("CDSE token endpoint did not return an access_token.")
                return self._access_token
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (401, 403):
                raise AuthenticationRequiredError(
                    f"CDSE authentication failed (HTTP {e.response.status_code}): Invalid username or password."
                ) from e
            raise DownloadFailedError(f"CDSE token request failed: {e}") from e
        except Exception as e:
            raise DownloadFailedError(f"Could not connect to CDSE identity service: {e}") from e

    def download_product(
        self,
        cdse_id: str,
        output_directory: Path,
        product_name: Optional[str] = None,
    ) -> Path:
        """Download raw Sentinel-1 product zip from CDSE OData API.

        Strict rule: Never claim a file exists unless successfully downloaded.
        """
        token = self.acquire_token()
        output_dir = Path(output_directory)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"{product_name or cdse_id}.zip"
        dest_path = output_dir / filename

        # If already fully downloaded and non-empty, return path
        if dest_path.exists() and dest_path.stat().st_size > 1024:
            logger.info(f"Using already downloaded scene: {dest_path}")
            return dest_path

        download_url = f"https://catalogue.dataspace.copernicus.eu/odata/v1/Products({cdse_id})/$value"
        headers = {"Authorization": f"Bearer {token}"}

        try:
            with httpx.Client(timeout=300.0, follow_redirects=True) as client:
                with client.stream("GET", download_url, headers=headers) as stream_resp:
                    stream_resp.raise_for_status()
                    with open(dest_path, "wb") as f:
                        for chunk in stream_resp.iter_bytes(chunk_size=65536):
                            f.write(chunk)
            
            if not dest_path.exists() or dest_path.stat().st_size == 0:
                dest_path.unlink(missing_ok=True)
                raise DownloadFailedError(f"Downloaded file for product {cdse_id} was empty.")

            logger.info(f"Successfully downloaded product {cdse_id} ({dest_path.stat().st_size} bytes)")
            return dest_path
        except Exception as e:
            dest_path.unlink(missing_ok=True)
            raise DownloadFailedError(f"Failed to stream product {cdse_id} from CDSE: {e}") from e

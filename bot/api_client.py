from __future__ import annotations

import httpx


class ApiClient:
    def __init__(self, *, base_url: str, internal_token: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._internal_token = internal_token

    def _internal_headers(self) -> dict[str, str]:
        return {"X-Internal-Token": self._internal_token}

    async def upsert_user(self, *, user_id: int, username: str | None) -> dict:
        async with httpx.AsyncClient(base_url=self._base_url, timeout=10.0) as client:
            r = await client.post(
                "/internal/users/upsert",
                json={"user_id": user_id, "username": username},
                headers=self._internal_headers(),
            )
            r.raise_for_status()
            return r.json()

    async def get_user(self, *, user_id: int) -> dict:
        async with httpx.AsyncClient(base_url=self._base_url, timeout=10.0) as client:
            r = await client.get(f"/internal/users/{user_id}", headers=self._internal_headers())
            r.raise_for_status()
            return r.json()

    async def list_matches(self, *, status: str | None = None) -> list[dict]:
        params = {}
        if status:
            params["status"] = status
        async with httpx.AsyncClient(base_url=self._base_url, timeout=10.0) as client:
            r = await client.get("/matches", params=params)
            r.raise_for_status()
            return r.json()

    async def admin_create_match(self, *, team1: str, team2: str, start_time_iso: str) -> dict:
        async with httpx.AsyncClient(base_url=self._base_url, timeout=10.0) as client:
            r = await client.post(
                "/internal/admin/matches",
                json={"team1": team1, "team2": team2, "start_time": start_time_iso},
                headers=self._internal_headers(),
            )
            r.raise_for_status()
            return r.json()

    async def admin_set_live(self, *, match_id: int) -> dict:
        async with httpx.AsyncClient(base_url=self._base_url, timeout=10.0) as client:
            r = await client.post(
                f"/internal/admin/matches/{match_id}/live", headers=self._internal_headers()
            )
            r.raise_for_status()
            return r.json()

    async def admin_finish_match(self, *, match_id: int, winner_team: str) -> dict:
        async with httpx.AsyncClient(base_url=self._base_url, timeout=10.0) as client:
            r = await client.post(
                f"/internal/admin/matches/{match_id}/finish",
                params={"winner_team": winner_team},
                headers=self._internal_headers(),
            )
            r.raise_for_status()
            return r.json()


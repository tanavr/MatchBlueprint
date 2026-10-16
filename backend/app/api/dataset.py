"""Prepared dataset availability for the dashboard."""
from typing import Literal
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.api.football import get_service
from app.services.football import FootballService

router = APIRouter()


class DatasetSummary(BaseModel):
    competition: str
    season: str
    teams: int
    matches: int
    source: str
    data_kind: Literal["real", "sample"]


class DatasetStatus(BaseModel):
    prepared: bool
    seasons: list[DatasetSummary]


@router.get("/dataset", response_model=DatasetStatus)
def dataset(service: FootballService = Depends(get_service)) -> DatasetStatus:
    summaries = []
    for competition in service.competitions().competitions:
        for season in service.seasons(competition.id).seasons:
            scope = (competition.id, season.id)
            if scope not in service.prepared_profiles:
                continue
            profiles = service.prepared_profiles[scope]
            summaries.append(DatasetSummary(competition=competition.name, season=season.name,
                teams=len(profiles), matches=len({m for p in profiles for m in p.match_ids}),
                source=competition.provenance.source, data_kind=competition.provenance.data_kind))
    return DatasetStatus(prepared=bool(summaries), seasons=summaries)

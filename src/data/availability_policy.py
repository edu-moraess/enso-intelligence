"""Auditable information-time policy for ENSO source datasets.

This module intentionally does not invent row-level publication timestamps.
A dataset may be used for forecasting only when its availability is either
explicitly supplied by the source or mapped by an approved, documented rule.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class AvailabilityPolicy:
    """Document how information-time availability is established."""

    dataset: str
    source: str
    status: str
    method: str
    evidence_url: str
    notes: str
    default_available_at: Optional[str] = None

    def is_usable_for_temporal_training(self) -> bool:
        """Return True only for policies with a validated availability rule."""
        return self.status == "validated" and bool(self.method)


# Source-level documentation is useful even before row-level timestamps exist.
# ``unknown`` deliberately blocks accidental leakage in historical training.
AVAILABILITY_POLICIES: dict[str, AvailabilityPolicy] = {
    "roni": AvailabilityPolicy(
        dataset="RONI",
        source="NOAA CPC",
        status="validated",
        method="official_page_schedule",
        evidence_url="https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/roni/",
        notes=(
            "NOAA CPC states that RONI is updated by the 5th of each month. "
            "This is a publication schedule, not a reconstructed timestamp "
            "for every historical observation; row-level backtests must not "
            "assume a finer timestamp without evidence."
        ),
    ),
    "oni": AvailabilityPolicy(
        dataset="ONI",
        source="NOAA CPC",
        status="validated",
        method="official_page_schedule",
        evidence_url="https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt",
        notes=(
            "NOAA CPC publishes the operational ONI series on a monthly cycle. "
            "Exact historical information-time timestamps are not inferred here."
        ),
    ),
    "weekly_nino": AvailabilityPolicy(
        dataset="Weekly Niño region SSTA",
        source="NOAA CPC",
        status="unknown",
        method="none",
        evidence_url="https://www.cpc.ncep.noaa.gov/data/indices/wksst9120.for",
        notes=(
            "Observation dates are available, but a row-level publication/"
            "availability timestamp has not yet been established. Keep "
            "available_at unset for historical leakage-sensitive training."
        ),
    ),
    "monthly_nino": AvailabilityPolicy(
        dataset="Monthly Niño region indices",
        source="NOAA CPC",
        status="unknown",
        method="none",
        evidence_url="https://www.cpc.ncep.noaa.gov/data/indices/sstoi.indices",
        notes=(
            "Observation dates are available, but exact historical information-"
            "time mapping has not yet been established."
        ),
    ),
    "godas": AvailabilityPolicy(
        dataset="NCEP GODAS",
        source="NOAA PSL/NCEP",
        status="unknown",
        method="none",
        evidence_url="https://psl.noaa.gov/data/gridded/data.godas.html",
        notes=(
            "GODAS provides monthly ocean analysis and D20/heat-content fields, "
            "but this registry does not infer historical release timestamps from "
            "the observation month. A validated information-time mapping is still required."
        ),
    ),
}


def get_availability_policy(dataset: str) -> AvailabilityPolicy:
    """Return the policy for a canonical dataset name."""
    try:
        return AVAILABILITY_POLICIES[dataset.lower()]
    except KeyError as exc:
        raise KeyError(f"No availability policy registered for {dataset!r}") from exc


def require_temporal_approval(dataset: str) -> AvailabilityPolicy:
    """Fail closed unless the source has a validated availability policy."""
    policy = get_availability_policy(dataset)
    if not policy.is_usable_for_temporal_training():
        raise ValueError(
            f"{dataset}: availability policy is not validated; "
            "row-level available_at must be established before temporal training."
        )
    return policy

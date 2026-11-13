"""
Automated Integration Tests for the 5 Master Demonstration Scenarios.

Verifies:
- Scenario 1: Historical Media Reuse produces MISLEADING_CONTEXT with EXACT_FILE_MATCH.
- Scenario 2: Legitimate Archival Reuse produces SUPPORTED / LEGITIMATE_ARCHIVAL_REUSE.
- Scenario 3: Claim Verification & Source Independence detects wire repeats and refutes uncorroborated event.
- Scenario 4: Coordinated Distribution identifies multi-signal cluster with temporal burst.
- Scenario 5: Media Authenticity evaluates physical forensics, executes CPU models, and reports unavailable models.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from scripts.run_demo_scenarios import (
    run_scenario_1_historical_reuse,
    run_scenario_2_legitimate_archival,
    run_scenario_3_claim_verification,
    run_scenario_4_coordinated_distribution,
    run_scenario_5_media_authenticity
)


@pytest.mark.asyncio
async def test_scenario_1_historical_reuse(db_session: AsyncSession):
    success = await run_scenario_1_historical_reuse(db_session)
    assert success is True


@pytest.mark.asyncio
async def test_scenario_2_legitimate_archival(db_session: AsyncSession):
    success = await run_scenario_2_legitimate_archival(db_session)
    assert success is True


@pytest.mark.asyncio
async def test_scenario_3_claim_verification(db_session: AsyncSession):
    success = await run_scenario_3_claim_verification(db_session)
    assert success is True


@pytest.mark.asyncio
async def test_scenario_4_coordinated_distribution(db_session: AsyncSession):
    success = await run_scenario_4_coordinated_distribution(db_session)
    assert success is True


@pytest.mark.asyncio
async def test_scenario_5_media_authenticity(db_session: AsyncSession):
    success = await run_scenario_5_media_authenticity(db_session)
    assert success is True

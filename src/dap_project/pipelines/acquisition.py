"""Acquisition pipeline orchestration."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
import yaml

from dap_project.data.cafeland_crawler import CafeLandCrawler, CrawlConfig
from dap_project.data.organize import (
    build_processed,
    normalize_dataframe,
    quality_summary,
    save_multiformat,
)


def load_config(path: str | Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def run_acquisition(
    project_root: str | Path,
    max_records: int | None = None,
    enrich_details: bool = False,
    progress=None,
) -> dict:
    root = Path(project_root)
    cfg = load_config(root / "config.yaml")
    acq = cfg["acquisition"]

    crawler = CafeLandCrawler(CrawlConfig(
        base_url=acq["base_url"],
        first_page_url=acq["first_page_url"],
        page_url_template=acq["page_url_template"],
        user_agent=acq["user_agent"],
        timeout_seconds=acq["timeout_seconds"],
        min_delay_seconds=acq["min_delay_seconds"],
        max_delay_seconds=acq["max_delay_seconds"],
        max_pages=acq["max_pages"],
        save_every_pages=acq["save_every_pages"],
        respect_robots=acq["respect_robots"],
        robots_fail_closed=acq["robots_fail_closed"],
        include_expired=acq["include_expired"],
    ))

    target = max_records or int(acq["target_raw_records"])
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    checkpoint = root / "data/raw/cafeland_checkpoint.csv"

    raw = crawler.crawl_search_pages(
    target,
    checkpoint,
    progress=progress,
)
    if enrich_details:
        raw = crawler.enrich_details(
        raw,
        progress=progress,
    )

    raw["crawled_at"] = datetime.now().isoformat(timespec="seconds")
    raw_paths = save_multiformat(
        raw, root / f"data/raw/cafeland_raw_{stamp}"
    )

    interim = normalize_dataframe(
        raw, root / "docs/hcm_pre2025_scope_map.json"
    )
    interim_paths = save_multiformat(
        interim, root / f"data/interim/cafeland_normalized_{stamp}"
    )

    processed = build_processed(interim)
    processed_paths = save_multiformat(
        processed, root / f"data/processed/hcm_realestate_{stamp}"
    )

    return {
        "raw_paths": raw_paths,
        "interim_paths": interim_paths,
        "processed_paths": processed_paths,
        "raw_quality": quality_summary(raw),
        "processed_quality": quality_summary(processed),
        "gate_passed": (
            len(processed) >= int(acq["minimum_valid_records"])
            and processed.shape[1] >= 8
        ),
    }


def run_sample(project_root: str | Path) -> dict:
    """Run an offline smoke test from the committed HTML fixture."""
    root = Path(project_root)
    cfg = load_config(root / "config.yaml")
    acq = cfg["acquisition"]
    crawler = CafeLandCrawler(CrawlConfig(
        base_url=acq["base_url"],
        first_page_url=acq["first_page_url"],
        page_url_template=acq["page_url_template"],
        user_agent=acq["user_agent"],
        respect_robots=False,
    ))
    fixture = root / "tests/fixtures/sample_search.html"
    html = fixture.read_text(encoding="utf-8")
    raw = pd.DataFrame(crawler.parse_search_page(html, page=1))
    raw["crawled_at"] = "offline_fixture"

    interim = normalize_dataframe(
        raw, root / "docs/hcm_pre2025_scope_map.json"
    )
    processed = build_processed(interim)
    interim.to_csv(
        root / "data/interim/cafeland_pilot_normalized.csv",
        index=False, encoding="utf-8-sig"
    )
    processed.to_csv(
        root / "data/processed/cafeland_pilot_cleaned.csv",
        index=False, encoding="utf-8-sig"
    )
    return {
        "source": str(fixture),
        "raw_quality": quality_summary(raw),
        "interim_quality": quality_summary(interim),
        "processed_quality": quality_summary(processed),
    }

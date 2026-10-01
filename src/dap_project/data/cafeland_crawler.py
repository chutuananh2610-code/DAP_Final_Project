"""Responsible CafeLand crawler for academic use.

The default strategy crawls search-result cards first to minimize requests.
Detail enrichment is optional.
"""

from __future__ import annotations

import random
import re
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import pandas as pd
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .parsers import normalize_space, parse_card_text, parse_detail_html


LISTING_PATH_RE = re.compile(r"/[^/]+-\d+\.html$", re.I)


@dataclass
class CrawlConfig:
    base_url: str
    first_page_url: str
    page_url_template: str
    user_agent: str
    timeout_seconds: int = 30
    min_delay_seconds: float = 1.5
    max_delay_seconds: float = 3.0
    max_pages: int = 500
    save_every_pages: int = 10
    respect_robots: bool = True
    robots_fail_closed: bool = True
    include_expired: bool = False


class CafeLandCrawler:
    def __init__(self, config: CrawlConfig):
        self.config = config
        self.session = self._build_session()
        self._robots = self._load_robots()

    def _build_session(self) -> requests.Session:
        retry = Retry(
            total=5,
            connect=5,
            read=5,
            backoff_factor=1.0,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET",),
            respect_retry_after_header=True,
        )
        session = requests.Session()
        session.headers.update({
            "User-Agent": self.config.user_agent,
            "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.7",
        })
        session.mount("https://", HTTPAdapter(max_retries=retry))
        return session

    def _load_robots(self) -> RobotFileParser | None:
        if not self.config.respect_robots:
            return None

        robots_url = urljoin(self.config.base_url, "/robots.txt")
        rp = RobotFileParser()
        rp.set_url(robots_url)
        try:
            response = self.session.get(
                robots_url, timeout=self.config.timeout_seconds
            )
            if response.ok:
                rp.parse(response.text.splitlines())
                return rp
        except requests.RequestException:
            pass

        if self.config.robots_fail_closed:
            raise RuntimeError(
                "Không xác nhận được robots.txt. Pipeline đang fail-closed. "
                "Hãy kiểm tra robots.txt/điều khoản thủ công trước khi chạy."
            )
        return None

    def _allowed(self, url: str) -> bool:
        if self._robots is None:
            return True
        return self._robots.can_fetch(self.config.user_agent, url)

    def _sleep(self) -> None:
        time.sleep(random.uniform(
            self.config.min_delay_seconds,
            self.config.max_delay_seconds,
        ))

    def fetch(self, url: str) -> str:
        if not self._allowed(url):
            raise PermissionError(f"robots.txt không cho phép crawl URL: {url}")
        response = self.session.get(url, timeout=self.config.timeout_seconds)
        response.raise_for_status()
        self._sleep()
        return response.text

    def page_url(self, page: int) -> str:
        if page == 1:
            return self.config.first_page_url
        return self.config.page_url_template.format(page=page)

    def extract_listing_links(self, html: str) -> list[tuple[str, str, str]]:
        """Return [(url, title, card_text), ...] from a search-result page."""
        soup = BeautifulSoup(html, "lxml")
        seen: set[str] = set()
        items: list[tuple[str, str, str]] = []

        for a in soup.find_all("a", href=True):
            href = urljoin(self.config.base_url, a["href"])
            path = urlparse(href).path

            if not LISTING_PATH_RE.search(path):
                continue
            if "/ho-tro/" in path or "cafeland.vn/du-an" in href:
                continue

            title = normalize_space(a.get_text(" ", strip=True))
            if len(title) < 8 or href in seen:
                continue

            # Find a reasonably-sized ancestor that looks like a listing card.
            card = a
            card_text = title
            for _ in range(7):
                if card.parent is None:
                    break
                card = card.parent
                candidate = normalize_space(card.get_text(" ", strip=True))
                if (
                    re.search(r"\d+(?:[.,]\d+)?\s*(?:m2|m²)", candidate, re.I)
                    and re.search(r"tỷ|triệu|thỏa thuận|thoả thuận", candidate, re.I)
                ):
                    card_text = candidate
                    break

            seen.add(href)
            items.append((href, title, card_text))

        return items

    def parse_search_page(self, html: str, page: int) -> list[dict]:
        records = []
        for url, title, card_text in self.extract_listing_links(html):
            rec = parse_card_text(card_text, title=title, url=url)
            rec["crawl_page"] = page
            records.append(rec)
        return records

    def crawl_search_pages(
        self,
        max_records: int,
        checkpoint_csv: str | Path | None = None,
        progress=None,
    ) -> pd.DataFrame:
        records = []
        seen_urls = set()
        empty_pages = 0

        for page in range(1, self.config.max_pages + 1):
            html = self.fetch(self.page_url(page))
            page_records = self.parse_search_page(html, page)

            added = 0

            for record in page_records:
                url = record.get("url")

                if not url or url in seen_urls:
                    continue

                seen_urls.add(url)
                records.append(record)
                added += 1

                if len(records) >= max_records:
                    break

            empty_pages = empty_pages + 1 if added == 0 else 0

            if progress:
                progress(
                    stage="search",
                    current=len(records),
                    total=max_records,
                    page=page,
                    added=added,
                )

            if checkpoint_csv and (
                page % self.config.save_every_pages == 0
                or len(records) >= max_records
            ):
                pd.DataFrame(records).to_csv(
                    checkpoint_csv,
                    index=False,
                    encoding="utf-8-sig",
                )

            if len(records) >= max_records:
                break

            if empty_pages >= 3:
                break

        return pd.DataFrame(records).reset_index(drop=True)


    def enrich_details(
        self,
        df: pd.DataFrame,
        progress=None,
    ) -> pd.DataFrame:
        enriched = []
        total = len(df)

        for index, row in enumerate(
            df.to_dict("records"),
            start=1,
        ):
            html = self.fetch(row["url"])
            detail = parse_detail_html(
                html,
                row["url"],
            )

            if not (
                detail.get("is_expired")
                and not self.config.include_expired
            ):
                merged = row.copy()

                for key, value in detail.items():
                    if value not in ("", None):
                        merged[key] = value

                enriched.append(merged)

            if progress:
                progress(
                    stage="detail",
                    current=index,
                    total=total,
                    page=0,
                    added=0,
                )

        return pd.DataFrame(enriched)
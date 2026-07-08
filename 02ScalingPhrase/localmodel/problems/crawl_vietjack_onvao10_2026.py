"""Crawl VietJack grade-10 entrance math test metadata and embedded questions.

The crawler extracts the normal HTML links from the public listing page and the
embedded ``window.INIT_QUES`` JSON from each test page.
"""

from __future__ import annotations

import csv
import html
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


BASE_URL = "https://khoahoc.vietjack.com"
LISTING_URL = (
    "https://khoahoc.vietjack.com/trac-nghiem/on-vao-10/mon-Toan/"
    "de-thi-thu-vao-lop-10-mon-toan-nam-2026?type=test"
)
OUTPUT_DIR = Path("vietjack_onvao10_2026")
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


def fetch(url: str, retries: int = 3, sleep_seconds: float = 0.8) -> str:
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=45) as response:
                return response.read().decode("utf-8", "replace")
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            time.sleep(sleep_seconds * (attempt + 1))
    raise RuntimeError(f"Failed to fetch {url}: {last_error}") from last_error


def strip_html(value: str) -> str:
    value = html.unescape(value or "")
    value = re.sub(r"<br\s*/?>", "\n", value, flags=re.I)
    value = re.sub(r"</p\s*>", "\n", value, flags=re.I)
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    return re.sub(r"[ \t\r\f\v]+", " ", value).replace("\xa0", " ").strip()


def page_title(page: str) -> str:
    match = re.search(r"<title>(.*?)</title>", page, flags=re.I | re.S)
    if not match:
        return ""
    return html.unescape(re.sub(r"\s+", " ", match.group(1))).strip()


def extract_exam_id(page: str) -> str:
    match = re.search(r'data-examid="([^"]+)"', page)
    if match:
        return match.group(1)
    match = re.search(r'data-id="([^"]+)"[^>]*data-totalquestions=', page)
    return match.group(1) if match else ""


def extract_total_questions(page: str) -> str:
    match = re.search(r'data-totalquestions="([^"]+)"', page)
    return match.group(1) if match else ""


def title_from_slug(url: str) -> str:
    slug = urllib.parse.urlparse(url).path.rstrip("/").split("/")[-1]
    slug = re.sub(r"/\d+$", "", slug)
    return slug.replace("-", " ").strip()


def extract_section_links(
    listing_html: str, start_marker: str, end_marker: str, section: str
) -> list[dict[str, str]]:
    start = listing_html.find(start_marker)
    end = listing_html.find(end_marker)
    if start < 0:
        return []
    if end < 0 or end <= start:
        end = len(listing_html)
    chunk = listing_html[start:end]
    links: list[dict[str, str]] = []
    seen: set[str] = set()
    href_re = re.compile(r'href=["\']([^"\']*?/thi-online/[^"\']+)["\']', flags=re.I)
    for match in href_re.finditer(chunk):
        href = urllib.parse.urljoin(LISTING_URL, html.unescape(match.group(1)))
        if href in seen:
            continue
        seen.add(href)
        context = strip_html(chunk[max(0, match.start() - 500) : match.start() + 500])
        title_match = re.search(
            r"((?:\d+\.\s*)?(?:Đề|Đề)[^.]*?(?:có đáp án|Đề \d+))",
            context,
            flags=re.I,
        )
        label = title_match.group(1).strip() if title_match else title_from_slug(href)
        number_match = re.match(r"^\s*(\d+)\.", label)
        links.append(
            {
                "index": str(len(links) + 1),
                "source_number": number_match.group(1) if number_match else "",
                "section": section,
                "title": label,
                "url": href,
            }
        )
    return links


def extract_links(listing_html: str) -> list[dict[str, str]]:
    section_specs = [
        ("courses_of_lesson_28641", "courses_of_lesson_28642", "minh_hoa_2026"),
        ("courses_of_lesson_28642", "courses_of_lesson_30210", "truong_so_2026"),
        ("courses_of_lesson_30210", "courses_of_lesson_28409", "da_nang_2026"),
    ]
    combined: list[dict[str, str]] = []
    seen: set[str] = set()
    for start_marker, end_marker, section in section_specs:
        for item in extract_section_links(listing_html, start_marker, end_marker, section):
            if item["url"] in seen:
                continue
            seen.add(item["url"])
            item["index"] = str(len(combined) + 1)
            combined.append(item)
    return combined


def extract_questions(page: str) -> list[dict[str, Any]]:
    match = re.search(r"window\.INIT_QUES\s*=\s*", page)
    if not match:
        return []
    decoder = json.JSONDecoder()
    data, _ = decoder.raw_decode(page[match.end() :])
    questions: list[dict[str, Any]] = []
    for question in data:
        content_html = question.get("content") or ""
        reason_html = question.get("reason") or ""
        answers = question.get("get_answer") or []
        normalized_answers = []
        for answer in answers:
            if not isinstance(answer, dict):
                normalized_answers.append(answer)
                continue
            normalized = dict(answer)
            if "content" in normalized:
                normalized["content_text"] = strip_html(str(normalized["content"]))
            normalized_answers.append(normalized)
        questions.append(
            {
                "id": question.get("id"),
                "slug": question.get("slug"),
                "type": question.get("type"),
                "index": (question.get("pivot") or {}).get("index"),
                "content_html": content_html,
                "content_text": strip_html(content_html),
                "reason_html": reason_html,
                "reason_text": strip_html(reason_html),
                "answers": normalized_answers,
            }
        )
    return questions


def crawl() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    listing_html = fetch(LISTING_URL)
    links = extract_links(listing_html)

    index_path = OUTPUT_DIR / "index.csv"
    with index_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["index", "source_number", "section", "title", "url"]
        )
        writer.writeheader()
        writer.writerows(links)

    tests_path = OUTPUT_DIR / "tests.jsonl"
    failures_path = OUTPUT_DIR / "failures.csv"
    total_questions = 0
    failures: list[dict[str, str]] = []

    with tests_path.open("w", encoding="utf-8") as output:
        for item in links:
            try:
                page = fetch(item["url"])
                questions = extract_questions(page)
                total_questions += len(questions)
                record = {
                    **item,
                    "page_title": page_title(page),
                    "exam_id": extract_exam_id(page),
                    "total_questions_declared": extract_total_questions(page),
                    "question_count": len(questions),
                    "questions": questions,
                }
                output.write(json.dumps(record, ensure_ascii=False) + "\n")
                print(
                    f"{item['index']}/{len(links)} "
                    f"{len(questions)} questions - {item['title']}"
                )
                time.sleep(0.35)
            except Exception as exc:  # noqa: BLE001 - keep crawl moving.
                failures.append(
                    {
                        "index": item["index"],
                        "title": item["title"],
                        "url": item["url"],
                        "error": str(exc),
                    }
                )
                print(f"FAILED {item['index']}/{len(links)} {item['url']}: {exc}")

    with failures_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["index", "title", "url", "error"])
        writer.writeheader()
        writer.writerows(failures)

    summary = {
        "listing_url": LISTING_URL,
        "listing_title": page_title(listing_html),
        "test_count": len(links),
        "question_count": total_questions,
        "failure_count": len(failures),
        "index_csv": str(index_path),
        "tests_jsonl": str(tests_path),
        "failures_csv": str(failures_path),
    }
    (OUTPUT_DIR / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    crawl()

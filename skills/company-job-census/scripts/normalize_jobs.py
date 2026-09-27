#!/usr/bin/env python3
"""Union, normalize, deduplicate and audit extracted career-site job JSON.

This helper performs no network access. It accepts one or more UTF-8 JSON files.
It recursively collects lists under common job-list keys, unions records across
pages/entrances, normalizes common fields, and deduplicates by a scoped stable
identifier. Optionally compare the final census count with an official expected
count using --expected-count.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "company": ("company", "company_name", "companyName"),
    "campaign": ("campaign", "project", "project_name", "projectName"),
    "job_id": ("job_id", "jobId", "position_id", "positionId", "post_id", "postId", "id"),
    "title": ("title", "job_title", "jobTitle", "position_name", "positionName", "post_name", "postName", "name"),
    "location": ("location", "locations", "city", "cities", "work_place", "workPlace", "workplace"),
    "department": ("department", "department_name", "departmentName", "org", "org_name", "orgName"),
    "business_unit": ("business_unit", "businessUnit", "business_unit_name", "businessUnitName"),
    "category": ("category", "job_category", "jobCategory", "post_type", "postType", "position_type", "positionType"),
    "headcount": ("headcount", "recruits", "recruit_count", "recruitCount", "number"),
    "education": ("education", "education_requirement", "educationRequirement", "degree"),
    "major": ("major", "majors", "major_requirement", "majorRequirement"),
    "description": ("description", "job_description", "jobDescription", "responsibilities", "duty", "duties"),
    "requirements": ("requirements", "requirement", "job_requirements", "jobRequirements", "qualification_text"),
    "qualification": ("qualification", "qualifications"),
    "skills": ("skills", "skill_requirements", "skillRequirements"),
    "certificates": ("certificates", "certificate_requirements", "certificateRequirements"),
    "deadline": ("deadline", "closing_date", "closingDate", "end_date", "endDate"),
    "url": ("url", "job_url", "jobUrl", "detail_url", "detailUrl", "href"),
    "source_url": ("source_url", "sourceUrl", "page_url", "pageUrl"),
    "source_type": ("source_type", "sourceType"),
    "extraction_method": ("extraction_method", "extractionMethod"),
    "captured_at": ("captured_at", "capturedAt", "verified_at", "verifiedAt"),
    "application_status": ("application_status", "applicationStatus"),
}

LIST_KEYS = {"jobs", "data", "items", "positions", "pageData", "records", "list", "rows", "result"}
HTML_TAG_RE = re.compile(r"<[^>]+>")
WHITESPACE_RE = re.compile(r"\s+")


def first_value(record: dict[str, Any], aliases: tuple[str, ...]) -> Any:
    for key in aliases:
        value = record.get(key)
        if value not in (None, "", [], {}):
            return value
    return ""


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    text = html.unescape(str(value))
    text = HTML_TAG_RE.sub(" ", text)
    return WHITESPACE_RE.sub(" ", text).strip()


def normalize_locations(value: Any) -> list[str]:
    if value in (None, ""):
        return []
    raw = value if isinstance(value, list) else re.split(r"[、,，;/；|]+", str(value))
    cleaned: list[str] = []
    for item in raw:
        if isinstance(item, dict):
            item = item.get("name") or item.get("nameCh") or item.get("label") or item.get("value") or ""
        text = clean_text(item)
        if text and text not in cleaned:
            cleaned.append(text)
    return cleaned


def looks_like_job(record: dict[str, Any]) -> bool:
    keys = set(record)
    title_keys = set(FIELD_ALIASES["title"])
    id_or_url_keys = set(FIELD_ALIASES["job_id"]) | set(FIELD_ALIASES["url"])
    job_context_keys = (
        set(FIELD_ALIASES["location"])
        | set(FIELD_ALIASES["department"])
        | set(FIELD_ALIASES["category"])
        | set(FIELD_ALIASES["description"])
        | set(FIELD_ALIASES["requirements"])
    )
    return bool(keys & title_keys) and bool((keys & id_or_url_keys) or (keys & job_context_keys))


def collect_job_records(payload: Any, under_job_key: bool = False) -> list[dict[str, Any]]:
    """Recursively collect job-like records from all common list branches."""
    out: list[dict[str, Any]] = []
    if isinstance(payload, list):
        for item in payload:
            if isinstance(item, dict) and (under_job_key or looks_like_job(item)):
                out.append(item)
                continue
            if isinstance(item, (dict, list)):
                out.extend(collect_job_records(item, under_job_key=False))
        return out
    if isinstance(payload, dict):
        for key, value in payload.items():
            if isinstance(value, list):
                out.extend(collect_job_records(value, under_job_key=(key in LIST_KEYS)))
            elif isinstance(value, dict):
                out.extend(collect_job_records(value, under_job_key=False))
        if looks_like_job(payload):
            out.append(payload)
    return out


def normalize_job(record: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for field, aliases in FIELD_ALIASES.items():
        value = first_value(record, aliases)
        result[field] = normalize_locations(value) if field == "location" else clean_text(value)
    result.update({
        "application_status_evidence": record.get("application_status_evidence", []) if isinstance(record.get("application_status_evidence", []), list) else [],
        "jd_evidence": record.get("jd_evidence", []) if isinstance(record.get("jd_evidence", []), list) else [],
        "fact_tags": record.get("fact_tags", {}) if isinstance(record.get("fact_tags", {}), dict) else {},
        "gaps": record.get("gaps", []) if isinstance(record.get("gaps", []), list) else [],
        "source_urls": record.get("source_urls", []) if isinstance(record.get("source_urls", []), list) else [],
    })
    return result


def dedupe_key(job: dict[str, Any], reused_ids: set[tuple[str, str, str]]) -> tuple[str, ...]:
    scope = (job["company"].casefold(), job["campaign"].casefold())
    if job["job_id"]:
        id_scope = (*scope, job["job_id"].casefold())
        if id_scope in reused_ids:
            return ("reused_id", *id_scope, job["department"].casefold(), job["business_unit"].casefold())
        return ("id", *scope, job["job_id"].casefold())
    if job["url"]:
        return ("url", *scope, job["url"].rstrip("/"))
    return ("composite", *scope, job["department"].casefold(), job["business_unit"].casefold(), "|".join(sorted(part.casefold() for part in job["location"])), job["title"].casefold())


def merge_missing(existing: dict[str, Any], incoming: dict[str, Any]) -> None:
    for key, value in incoming.items():
        if existing.get(key) in (None, "", [], {}) and value not in (None, "", [], {}):
            existing[key] = value
        elif key in ("jd_evidence", "source_urls", "application_status_evidence", "gaps") and isinstance(value, list):
            for item in value:
                if item not in existing[key]:
                    existing[key].append(item)


def normalize(payloads: list[Any], expected_count: int | None = None) -> dict[str, Any]:
    raw_jobs: list[dict[str, Any]] = []
    for payload in payloads:
        raw_jobs.extend(collect_job_records(payload))

    normalized = [normalize_job(raw) for raw in raw_jobs]
    id_units: dict[tuple[str, str, str], set[tuple[str, str]]] = {}
    for job in normalized:
        if job["job_id"]:
            id_scope = (job["company"].casefold(), job["campaign"].casefold(), job["job_id"].casefold())
            unit = (job["department"].casefold(), job["business_unit"].casefold())
            if any(unit):
                id_units.setdefault(id_scope, set()).add(unit)
    reused_ids = {key for key, units in id_units.items() if len(units) > 1}

    unique: dict[tuple[str, ...], dict[str, Any]] = {}
    for job in normalized:
        if not job["title"]:
            continue
        key = dedupe_key(job, reused_ids)
        if key in unique:
            merge_missing(unique[key], job)
        else:
            unique[key] = job

    jobs = list(unique.values())
    missing_stable_id = sum(1 for j in jobs if not j["job_id"] and not j["url"])
    missing_location = sum(1 for j in jobs if not j["location"])
    location_counts = Counter(loc for j in jobs for loc in j["location"])
    department_counts = Counter(j["department"] for j in jobs if j["department"])

    result: dict[str, Any] = {
        "raw_collected_count": len(raw_jobs),
        "deduplicated_count": len(jobs),
        "missing_stable_id_count": missing_stable_id,
        "missing_location_count": missing_location,
        "counts_by_location": dict(location_counts.most_common()),
        "counts_by_department": dict(department_counts.most_common()),
        "reused_job_ids_across_units": len(reused_ids),
        "jobs": jobs,
    }
    if expected_count is not None:
        result["official_expected_count"] = expected_count
        result["count_difference"] = len(jobs) - expected_count
        result["count_match"] = len(jobs) == expected_count
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path, help="One or more UTF-8 JSON files containing extracted jobs")
    parser.add_argument("-o", "--output", type=Path, help="Output JSON file; stdout when omitted")
    parser.add_argument("--expected-count", type=int, default=None, help="Official current-project job count for census reconciliation")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        payloads = [json.loads(path.read_text(encoding="utf-8-sig")) for path in args.inputs]
        result = normalize(payloads, expected_count=args.expected_count)
        result["source_file_count"] = len(args.inputs)
        result["source_files"] = [str(path) for path in args.inputs]
        rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.write_text(rendered, encoding="utf-8")
        else:
            sys.stdout.write(rendered)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"normalize_jobs: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

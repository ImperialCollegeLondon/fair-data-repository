"""Fetch awards from Symplectic API and save to CSV."""

import csv
import os
import time
import xml.etree.ElementTree as ET

import requests

API_URL = os.environ.get("SYMPLECTIC_API_URL")
SUBSCRIPTION_KEY = os.environ.get("SYMPLECTIC_API_SUBSCRIPTION_KEY")

headers = {"subscription-key": SUBSCRIPTION_KEY, "content-type": "text/xml"}

NS = {"api": "http://www.symplectic.co.uk/publications/api"}


def fetch_all_results(initial_url, max_results):
    """Fetch and combine all results up to max_results."""
    session = requests.Session()
    all_results = []
    url = initial_url
    total_results = 0

    while url and total_results < max_results:
        print(f"Fetching: {url}")
        try:
            response = session.get(url, headers=headers, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            break

        try:
            root = ET.fromstring(response.text)
        except ET.ParseError as e:
            print(f"Failed to parse XML: {e}")
            break

        # Extract results
        result_list = root.find(
            ".//{http://www.symplectic.co.uk/publications/api}result-list"
        )
        if result_list is None:
            print("No result-list found")
            break

        results = result_list.findall(
            ".//{http://www.symplectic.co.uk/publications/api}result"
        )
        for r in results:
            if total_results >= max_results:
                break
            all_results.append(ET.tostring(r, encoding="unicode"))
            total_results += 1

        print(f"Appended {len(results)} results, total so far: {total_results}")

        # Get next URL
        pagination = root.find(
            ".//{http://www.symplectic.co.uk/publications/api}pagination"
        )
        if pagination is not None:
            next_page = pagination.find(
                './/{http://www.symplectic.co.uk/publications/api}page[@position="next"]'  # noqa:E501
            )
            if next_page is not None:
                next_href = next_page.get("href")
                old_base = "https://testsymplectic.imperial.ac.uk:8091/secure-api/v6.13"
                url = next_href.replace(old_base, API_URL)
            else:
                print("No next page")
                break
        else:
            print("No pagination found")
            break

        time.sleep(2)  # Rate limit

    return all_results


def extract_csv_data(results):
    """Extract required fields from results and return CSV-ready data."""

    def _format_date(field: ET.Element) -> str:
        date = field.find(".//api:date", NS)
        if date is None:
            return ""
        day = date.findtext("api:day", default="", namespaces=NS)
        month = date.findtext("api:month", default="", namespaces=NS)
        year = date.findtext("api:year", default="", namespaces=NS)
        return (
            f"{year}-{month.zfill(2)}-{day.zfill(2)}" if year and month and day else ""
        )

    csv_data = []
    required_keys = [
        "title",
        "institution-reference",
        "funder-reference",
        "funder-type",
        "start-date",
        "end-date",
    ]

    for result_xml in results:
        root = ET.fromstring(result_xml)
        fields: dict[str, str] = {}
        native = root.find(".//api:native", NS)
        if native is not None:
            for field in native.findall(".//api:field", NS):
                name = field.get("name")
                if name in required_keys:
                    if field.get("type") == "date":
                        fields[name] = _format_date(field)
                    else:
                        text = field.findtext(".//api:text", default="", namespaces=NS)
                        fields[name] = text.strip()

        # Check if funder-reference is "n/a" and try to replace with funder-name
        if fields.get("funder-reference") in ["n/a", "N/A"]:
            funder_name_field = (
                native.find(".//api:field[@name='funder-name']", NS)
                if native is not None
                else None
            )
            if funder_name_field is not None:
                text = funder_name_field.findtext(
                    ".//api:text", default="", namespaces=NS
                )
                fields["funder-reference"] = text.strip()

        if all(fields.get(key, "").strip() for key in required_keys):
            csv_data.append([fields[key] for key in required_keys])

    return csv_data


initial_url = f"{API_URL}/grants?detail=full&per-page=25"
# Change max_results as needed
results = fetch_all_results(initial_url, max_results=100)
csv_data = extract_csv_data(results)

if csv_data:
    with open("test.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "AwardShortTitle",
                "AwardNumber",
                "Award Funder Reference",
                "FunderGroup",
                "AwardStartDate",
                "AwardEndDate",
            ]
        )
        writer.writerows(csv_data)
    print("Data saved to symplectic_awards_data.csv")
else:
    print("No complete records found")

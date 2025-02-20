import os
import requests
from datetime import datetime, timedelta
from dateutil.parser import parse
import argparse
import json


# CLI
parser = argparse.ArgumentParser(prog="Notion-Working Hours")
parser.add_argument("-m", "--month", nargs="*", type=int, default=datetime.now().month)
parser.add_argument("-y", "--year", nargs="*", type=int, default=datetime.now().year)
parser.add_argument("-c", "--company", nargs="*", type=str, required=True)

defaultConfigPath = f"{os.getenv("LOCALAPPDATA")}\\notion-working-hours\\config.json"
parser.add_argument("-s", "--settings", "--config", type=str, nargs="?", default=defaultConfigPath)

args = parser.parse_args()

if os.path.exists(args.settings):
    with open(args.settings, "r") as file:
        config = json.load(file)
elif os.path.exists(defaultConfigPath):
    with open(defaultConfigPath, "r") as file:
        config = json.load(file)
else:
    raise Exception("Config file missing")

NOTION_KEY = config["NOTION_KEY"]
db_id = config["DB_ID"]
list_id = config["LIST_ID"]

# Setup
headers = {'Authorization': f"Bearer {NOTION_KEY}", 
           'Content-Type': 'application/json', 
           'Notion-Version': '2022-06-28'}

months = {1: "Januar", 
          2: "Februar",
          3: "März",
          4: "April",
          5: "Mai",
          6: "Juni",
          7: "Juli",
          8: "August",
          9: "September",
          10: "Oktober",
          11: "November",
          12: "Dezember"}




def create_summary_page(company, month=datetime.now().month, year=datetime.now().year):
    page_exist_params = {"filter": {"and": [
        {"property": "Company", "select": {"equals": company}},
        {"property": "Month", "select": {"equals": months[month]}},
        {"property": "Year", "number": {"equals": year}}
    ]}}


    page_exist_response = requests.post(
        f'https://api.notion.com/v1/databases/{list_id}/query',json=page_exist_params, 
        headers=headers)
    
    page_exist_json = page_exist_response.json()["results"]

    if len(page_exist_json) != 0:
        for page in page_exist_json:
            res = requests.patch(
                f"https://api.notion.com/v1/pages/{page["id"]}",
                headers=headers,
                json= {"archived": True})

    search_params = {
        "filter":{
            "and": [
                {"property": "Company", "select": {"equals": company}},
                  {"property": "Date", "date": {"on_or_after": get_date_range(month - 1, year)[0]}},
                  {"property": "Date", "date": {"on_or_before": get_date_range(month - 1, year)[1]}}
                  ]},
        "sorts": [{"property": "Date", "direction": "ascending"}]
                  }
    
    search_response = requests.post(
        f'https://api.notion.com/v1/databases/{db_id}/query',json=search_params, 
        headers=headers)
    
    res_json = search_response.json()["results"]

    if len(res_json) == 0:
        print(f"Keine Stunden eingetragen für {company} im {months[month]} {year}")
        return

    total_hours = 0

    children = [{
            "object": "block",
            "type": "table_row",
            "table_row": {
                "cells": [
                    [{"type": "text", "text": {"content": "Datum"}}],
                    [{"type": "text", "text": {"content": "Start"}}],
                    [{"type": "text", "text": {"content": "Ende"}}],
                    [{"type": "text", "text": {"content": "Dauer"}}]
                ]
            }
            }]

    for res in res_json:
        start = res["properties"]["Date"]["date"]["start"]
        end = res["properties"]["Date"]["date"]["end"]
        duration = res["properties"]["Duration"]["formula"]["number"]

        total_hours += duration

        child = {
            "object": "block",
            "type": "table_row",
            "table_row": {
                "cells": [
                    [{"type": "text", "text": 
                      {"content": parse(start).date().strftime("%d.%m.%Y")}}],
                    [{"type": "text", "text": 
                      {"content": parse(start).time().strftime("%H:%M")}}],
                    [{"type": "text", "text": 
                      {"content": parse(end).time().strftime("%H:%M")}}],
                    [{"type": "text", "text": {"content": f"{duration}"}}]
                ]
            }
            }
        children.append(child)

    create_page_body = {
        "parent": {"type": "database_id","database_id": list_id},
        "properties": {
            "title": {
                "title": [{
                    "type": "text",
                    "text": {"content": f"Ben Engelhard - {company} - {months[month]}"}
                }]
            },
            "Company": {
                "select": {"name": company}
            },
            "Month": {
                "select": {"name": months[month]}
            },
            "Year": {
                "number": year
            }
        },
        "children": [
            {
            "object": "block",
            "type": "table",
            "table": {
                "table_width": 4,
                "has_column_header": True,
                "children": children
                }
            },
            {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{
                    "type": "text",
                    "text": {"content": f"Insgesamt: {total_hours}h"}
                }]
            }
        }
        ]   
    }

    create_response = requests.post(
        "https://api.notion.com/v1/pages",
        json=create_page_body, 
        headers=headers)
    print(create_response.json()["url"])

def get_date_range(month: int, year: int = None):
    if month == 0:
        month = 12

    if year is None:
        year = datetime.today().year  # Default to current year

    start_date = datetime(year, month, 20).strftime("%Y-%m-%d")

    # Handle December correctly by rolling over to the next year
    if month == 12:
        next_month, next_year = 1, year + 1
    else:
        next_month, next_year = month + 1, year

    end_date = datetime(next_year, next_month, 19).strftime("%Y-%m-%d")

    return start_date, end_date

for company in args.company:
    print(company)
    for year in args.year:
        print(year)
        for month in args.month:
            print(month)
            create_summary_page(company, month, year)
import os
from dotenv import load_dotenv, dotenv_values 
import requests
import json
from datetime import datetime, timedelta
from dateutil.parser import parse

load_dotenv() 

NOTION_KEY = os.getenv("API_KEY")
page_id = os.getenv("PAGE_ID")
db_id = os.getenv("DB_ID")
list_id = os.getenv("LIST_ID")

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

# search_params = {"filter": {"value": "database", "property": "object"}}

# search_response = requests.post(f'https://api.notion.com/v1/search', 
#     json=search_params, headers=headers)

# res_json = search_response.json()["results"]

# for res in res_json:
#     print(res["id"], res["url"])


def create_summary_page(month, company):
    page_exist_params = {"filter": {"and": [
        {"property": "Company", "select": {"equals": company}},
        {"property": "Month", "select": {"equals": months[month]}},
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
                  {"property": "Date", "date": {"on_or_after": get_date_range(month)[0]}},
                  {"property": "Date", "date": {"on_or_before": get_date_range(month)[1]}}
                  ]},
        "sorts": [{"property": "Date", "direction": "ascending"}]
                  }
    
    search_response = requests.post(
        f'https://api.notion.com/v1/databases/{db_id}/query',json=search_params, 
        headers=headers)
    
    res_json = search_response.json()["results"]

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
                    "text": {"content": f"Insgesamt: {int(total_hours)}h"}
                }]
            }
        }
        ]   
    }

    create_response = requests.post(
        "https://api.notion.com/v1/pages",
        json=create_page_body, 
        headers=headers)
    print(create_response.json())




def get_date_range(month: int, year: int = None):
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


create_summary_page(1, "eea")
# -*- coding: UTF-8 -*-
import json
from pathlib import Path
import json_repair

from rich import print

from client import Client


def load_data(filename: str):
    data_dir = Path(__file__).parent.parent / 'data1'
    with open(data_dir / filename, 'r', encoding='utf8') as f:
        data = [json.loads(line) for line in f]
        data = [{'id': d['custom_id'], 'messages': d['body']['messages']} for d in data]
    return data


def save(data: list[dict[str, str]], filename: str):
    output_dir = Path(__file__).parent.parent / 'output'
    output_dir.mkdir(exist_ok=True)
    with open(output_dir / filename, 'w', encoding='utf8') as f:
        for item in data:
            item['content'] = item['content'].replace('\n', '').strip('```json')
            item['content'] = json_repair.loads(item['content'])
            f.write(json.dumps(item, ensure_ascii=False) + '\n')



if __name__ == '__main__':
    data = load_data('data1-1.jsonl')
    client = Client(batch_size=100, max_workers=15)
    response = client.extract(data)
    save(response, 'data1-1.jsonl')

# -*- coding: UTF-8 -*-
import json
import threading
import time
from concurrent import futures
from pathlib import Path
from typing import TypeAlias

import json_repair
from loguru import logger
from tqdm import tqdm
from zhipuai import ZhipuAI

Sample: TypeAlias = dict[str, str]


def timer(func):
    def wrapper(*args, **kwargs):
        logger.info(f"Start {func.__name__}")
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        logger.info(f"End {func.__name__} spending {(end - start):.2f} seconds")
        return result
    return wrapper


class Client:

    def __init__(self, batch_size=2, max_workers=10):
        self.client = ZhipuAI(api_key='ba802c1855ebdba8235bf095766f104e.oAwCWXo3QFwHuAi7')
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.thread_positions = {}

    @timer
    def extract(self, texts: list[Sample]) -> list[Sample]:
        results = []
        texts = [texts[i:i + self.batch_size] for i in range(0, len(texts), self.batch_size)]
        tasks = {}
        with futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for i, batch in enumerate(texts):
                future = executor.submit(self.__chat, i, batch)
                tasks[future] = (i, batch)

        for future in futures.as_completed(tasks):
            try:
                results.extend(future.result())
            except Exception as e:
                logger.error(e)

        return results


    def __chat(self, i: int, batch: list[Sample]) -> list[dict[str, str]]:
        thread_id = threading.get_ident()
        position = self.__get_position(thread_id)
        pbar = tqdm(total=len(batch), desc=f'Batch-{i + 1}', leave=False, position=position)
        task_texts: dict[str, str] = {}
        for sample in batch:
            task = self.client.chat.asyncCompletions.create(model='GLM-4-Flash', messages=sample['messages'])
            task_texts[task.id] = sample['id']

        results = []
        processing_ids = set(task_texts.keys())
        while len(processing_ids) > 0:
            for task_id, id_ in task_texts.items():
                if task_id not in processing_ids:
                    continue
                response = self.client.chat.asyncCompletions.retrieve_completion_result(task_id)
                if response.task_status != 'PROCESSING':
                    processing_ids.remove(task_id)
                    pbar.update(1)
                    if response.task_status == 'SUCCESS':
                        results.append({
                            'id': id_,
                            'content': response.choices[0].message.content
                        })
                time.sleep(2)

        pbar.close()
        return results


    def __get_position(self, thread_id):
        with threading.Lock():
            if thread_id not in self.thread_positions:
                self.thread_positions[thread_id] = len(self.thread_positions)
            return self.thread_positions[thread_id]


def load_data(filename: str):
    data_dir = Path(__file__).parent.parent / 'data'
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
    data = load_data('data_prompt1.jsonl')
    client = Client(batch_size=100, max_workers=20)
    response = client.extract(data)
    save(response, 'data_prompt1.jsonl')

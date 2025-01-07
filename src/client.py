# -*- coding: UTF-8 -*-
from typing import TypeAlias

from zhipuai import ZhipuAI
from concurrent import futures
from loguru import logger
from tqdm import tqdm
import time

Sample: TypeAlias = dict[str, str]


def timer(func):
    def wrapper(*args, **kwargs):
        logger.info(f"Start {func.__name__}")
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        logger.info(f"End {func.__name__} spending {(end - start):2f} seconds")
        return result
    return wrapper


class Client:

    def __init__(self, batch_size=2, max_workers=10):
        self.client = ZhipuAI(api_key='ba802c1855ebdba8235bf095766f104e.oAwCWXo3QFwHuAi7')
        self.batch_size = batch_size
        self.max_workers = max_workers

    @timer
    def extract(self, texts: list[Sample]) -> list[Sample]:
        results = []
        texts = [texts[i:i + self.batch_size] for i in range(0, len(texts), self.batch_size)]
        processing_bars = []
        tasks = {}
        with futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for i, batch in enumerate(texts):
                pbar = tqdm(total=len(batch), desc=f'Batch-{i + 1}', position=i, dynamic_ncols=True)
                processing_bars.append(pbar)
                future = executor.submit(self.__chat, batch, pbar)
                tasks[future] = (batch, pbar)

        for future in futures.as_completed(tasks):
            try:
                results.extend(future.result())
            except Exception as e:
                logger.error(e)

        for bar in processing_bars:
            bar.close()

        return results


    def __chat(self, batch: list[Sample], pbar) -> list[dict[str, str]]:
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

        return results


    def __batch_process(self, batch: list[Sample], pbar) -> list[dict[str, str]]:
        pass

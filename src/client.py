# -*- coding: UTF-8 -*-
from zhipuai import ZhipuAI
from concurrent import futures
from loguru import logger
from tqdm import tqdm
import time

class Client:

    def __init__(self):
        self.client = ZhipuAI(api_key='e10a6f5e200c866e7b2e95b28be44fe3.48jeVvIcKr7pplj1')
        self.batch_size = 2
        self.max_workers = 10
        self.prompt = '''
        你好，你是一个实体和关系提取的专家，你需要从以下给定的文本中提取出命名实体以及它们的关系，并严格按照给定的json格式输出
        要求：提取的命名实体类型尽量分为研究问题(Problem)、研究方法(Method)、实验结果(Result)、结论(Conclusion)，对于同义关系，应该有相同的名称
        输入：#{0}#
        输出：
        {{
            'entities': [
                {{'id': '', 'type': '', 'name': ''}},
            ],
            'relations': [
                {{'type': '', 'from_entity_id': '', 'to_entity_id': ''}}
            ]
        }}
        '''


    def extract(self, texts: list[str]) -> list[str]:
        results = []
        texts = [texts[i:i + self.batch_size] for i in range(0, len(texts), self.batch_size)]
        processing_bars = []
        tasks = {}
        with futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for i, batch in enumerate(texts):
                pbar = tqdm(total=self.batch_size, desc=f'Batch-{i + 1}', position=i)
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

    def __chat(self, batch: list[str], pbar) -> list[dict[str, str]]:
        task_texts: dict[str, str] = {}
        for text in batch:
            task = self.client.chat.asyncCompletions.create(
                model='GLM-4-Flash',
                messages=[{'role': 'user', 'content': self.prompt.format(text)}]
            )
            task_texts[task.id] = text

        results = []
        processing_ids = set(task_texts.keys())
        while len(processing_ids) > 0:
            for task_id, text in task_texts.items():
                if task_id not in processing_ids:
                    continue
                response = self.client.chat.asyncCompletions.retrieve_completion_result(task_id)
                if response.task_status != 'PROCESSING':
                    processing_ids.remove(task_id)
                    pbar.update(1)
                    if response.task_status == 'SUCCESS':
                        results.append({text: response.choices[0].message.content})
                time.sleep(2)

        return results

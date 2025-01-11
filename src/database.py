# -*- coding: UTF-8 -*-
import json
import threading
from concurrent import futures
from typing import Any, Annotated

import loguru
import typer
from py2neo import Graph, Node, Relationship
from tqdm import tqdm


class Database:

    def __init__(self, batch_size=1000, max_workers=10):
        self.graph = Graph('neo4j://localhost:7687', auth=('neo4j', 'rootrootroot'))
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.thread_positions = {}


    def batch_insert_entities(self, entities: list[dict[str, Any]]):
        def insert(i: int, entities: list[dict[str, Any]]):
            thread_id = threading.get_ident()
            position = self.__get_position(thread_id)
            for entity in tqdm(entities, total=len(entities), position=position, leave=False, desc=f'Batch-{i}'):
                if 'properties' not in entity:
                    entity['properties'] = {}
                node = Node(entity['type'], id=entity['id'], name=entity['name'], **entity['properties'])
                self.graph.merge(node, entity['type'], 'id')


        self.__batch_process(entities, insert)


    def batch_insert_relations(self, relations: list[dict[str, str]]):
        def insert(i: int, relations: list[dict[str, str]]):
            thread_id = threading.get_ident()
            position = self.__get_position(thread_id)
            for relation in tqdm(relations, total=len(relations), position=position, leave=False, desc=f'Batch-{i}'):
                from_entity_id = relation['from_entity_id']
                to_entity_id = relation['to_entity_id']
                from_entity_type = relation['from_entity_type']
                to_entity_type = relation['to_entity_type']
                from_node = self.graph.nodes.match(from_entity_type, id=from_entity_id).first()
                to_node = self.graph.nodes.match(to_entity_type, id=to_entity_id).first()
                if from_node and to_node:
                    relationship = Relationship(from_node, relation['type'], to_node)
                    self.graph.merge(relationship, relation['type'], 'id')


        self.__batch_process(relations, insert)


    def __batch_process(self, elements, method):
        total = len(elements)
        batches = [elements[i:i + self.batch_size] for i in range(0, len(elements), self.batch_size)]
        batch_num = len(batches)
        print(f'Batch number: {batch_num}, total: {total}')
        tasks = {}
        with futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for i, batch in enumerate(batches):
                future = executor.submit(method, i, batch)
                tasks[future] = batch

        for future in futures.as_completed(tasks):
            try:
                future.result(300)
            except Exception as e:
                loguru.logger.exception(e)


    def __get_position(self, thread_id):
        with threading.Lock():
            if thread_id not in self.thread_positions:
                self.thread_positions[thread_id] = len(self.thread_positions)
            return self.thread_positions[thread_id]


def insert(
    filename: Annotated[str, typer.Argument(help='jsonl file')],
    type_: Annotated[str, typer.Argument()],
):
    db = Database(batch_size=2500, max_workers=15)
    with open(filename, 'r', encoding='utf-8') as f:
        data = [json.loads(line) for line in f]
    if type_ == 'relation':
        db.batch_insert_relations(data)
    elif type_ == 'entity':
        db.batch_insert_entities(data)


if __name__ == '__main__':
    typer.run(insert)

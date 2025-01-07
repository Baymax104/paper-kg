# -*- coding: utf-8 -*-
from zhipuai import ZhipuAI
import json

client = ZhipuAI(api_key="e10a6f5e200c866e7b2e95b28be44fe3.48jeVvIcKr7pplj1")  # 替换为你的APIKey


def get_paragraph_prompt(paragraph):
    paragraph_prompt = rf"""
    ## 任务：
    根据论文的id、title、abstract、author，提取出命名实体以及它们的关系。
    ## 任务要求：
    提取的命名实体类型尽量分为研究问题(Problem)、研究方法(Method)、实验结果(Result)、结论(Conclusion)，对于同义关系，应该有相同的名称。并严格按照JSON格式输出。
    ## 输入内容：
    {paragraph}
    ## 定义输出格式：
    {{
        "id": "6552e01f939a5f40823b85c6",
        "content": {{
            "entities": [
                {{
                    "id": "1",
                    "type": "Problem",
                    "name": "noisy speech emotion recognition (NSER)"
                }},
                {{
                    "id": "2",
                    "type": "Method",
                    "name": "conventional NSER approaches"
                }},
                
            ],
            "relations": [
                {{
                    "type": "SolutionToProblem",
                    "from_entity_id": "1",
                    "to_entity_id": "2"
                }},
                {{
                    "type": "ApplicationOf",
                    "from_entity_id": "2",
                    "to_entity_id": "3"
                }}
            ]
        }}
    }},
    {{
        "id": "66f619a301d2a3fbfcdc6034",
        "content": {{
            "entities": [
                {{
                    "id": "1",
                    "type": "Problem",
                    "name": "CNNs make decisions based on narrow, specific regions of input images"
                }},
                {{
                    "id": "2",
                    "type": "Problem",
                    "name": "Model's generalization capabilities are compromised"
                }}
            ],
            "relations": [
                {{
                    "type": "addresses",
                    "from_entity_id": "1",
                    "to_entity_id": "4"
                }},
                {{
                    "type": "addresses",
                    "from_entity_id": "2",
                    "to_entity_id": "4"
                }}
            ]
        }}
    }}
    ## 注意事项
    1.id与论文中的id一致
    2.并严格按照JSON格式输出
    """
    return paragraph_prompt


def create_glm_prompt(paragraph_prompt, paper_id):
    jsonl_data = {
        "custom_id": paper_id,  # 每个请求必须包含custom_id且是唯一的
        "method": "POST",
        "url": "/v4/chat/completions",
        "body": {
            "model": "glm-4-flash",
            "messages": [
                {"role": "system", "content": "你是一个专门从输入的段落中提取实体和关系的专家"},
                {
                    "role": "user",
                    "content": paragraph_prompt
                }
            ]
        }
    }
    return jsonl_data


def generate_query(paragraph, paper_id):
    paragraph_prompt = get_paragraph_prompt(paragraph)
    jsonl_data = create_glm_prompt(paragraph_prompt, paper_id)
    return jsonl_data


if __name__ == "__main__":
    all_query = []
    with open('CCF.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
        count = 0
        for item in data:
            paragraph = 'id:' + item.get('_id', {}) + '\ntitle:' + item.get('title', {}) + '\nabstract:' + item.get('abstract', {}) + '\nauthor:' + item.get('author', {})
            print(item.get('_id', {}))
            all_query.append(generate_query(paragraph, item.get('_id', {})))
            count += 1  # 增加计数器
            if count >= 1000:  # 测试1000条数据
                break
    with open('test.jsonl', 'w') as file:
        for item in all_query:
            file.write(json.dumps(item) + '\n')

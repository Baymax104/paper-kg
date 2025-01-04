# -*- coding: utf-8 -*-
from zhipuai import ZhipuAI
import json
from docx import Document

client = ZhipuAI(api_key="e10a6f5e200c866e7b2e95b28be44fe3.48jeVvIcKr7pplj1")  # 替换为你的APIKey



def extract_entities_and_relations():
    research_problem = ["Degradation prediction", "Rolling predictive maintenance policy", "Multi-sensor systems",
                        "Remaining useful life (RUL) prediction"]
    research_method = ["Two-dimensional self-attention (TDSA) method", "Division of degradation process into intervals",
                       "Calculation of maintenance cost rate"]
    experimental_results = ["Cost rate of RPdM policy is lower than preventive maintenance policy",
                            "27.7% higher than ideal maintenance policy",
                            "Good robustness under different out-of-stock costs and corrective costs"]
    core_conclusion = [
        "The proposed RPdM policy effectively reduces maintenance costs compared to traditional preventive maintenance",
        "The policy shows robustness against variations in out-of-stock and corrective costs"]
    source_code_link = "Not provided"

    return {
        "research_problem": research_problem,
        "research_method": research_method,
        "experimental_results": experimental_results,
        "core_conclusion": core_conclusion,
        "source_code_link": source_code_link
    }


def get_paragraph_prompt(paragraph):
    example = extract_entities_and_relations()

    # 将 JSON 对象转换为字符串
    knowledge_graph_json = json.dumps(example, ensure_ascii=False, indent=2)

    paragraph_prompt = f"""
    你好，你是一个专门从输入的段落中提取实体和关系的专家，根据论文的id、title、abstract、author，提取论文的研究问题（以关键词形式呈现）、研究方法、实验结果、核心结论、开源地址或代码链接等信息，保持抽取信息和文献ID之间的关联关系。并严格按照JSON格式输出。
    输入：{paragraph}
    JSON 输出：
    {knowledge_graph_json}
    
    """
    return paragraph_prompt


def ask_chatglm(paragraph_prompt):
    response = client.chat.completions.create(
        model="GLM-4-Flash",  # 替换为需要调用的模型名称
        messages=[
            {"role": "user", "content": paragraph_prompt},
        ],
    )
    return response.choices[0].message.content


def one_turn(paragraph):
    paragraph_prompt = get_paragraph_prompt(paragraph)
    glm_response = ask_chatglm(paragraph_prompt)
    return glm_response


if __name__ == "__main__":
    with open('CCF.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
        count = 0
        for item in data:
            paragraph = 'id:' + item.get('_id', {}) + '\ntitle:' + item.get('title', {}) + '\nabstract:' + item.get('abstract', {}) + '\nauthor:' + item.get('author', {})
            # print(paragraph)
            response = one_turn(paragraph)
            print(response)
            count += 1  # 增加计数器
            if count >= 5:  # 检查是否已经处理了50个字典
                break

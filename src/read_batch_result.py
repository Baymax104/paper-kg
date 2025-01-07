import json


def save_to_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


all_paper = []
# 打开 JSONL 文件
with open('output_202501071545.jsonl', 'r', encoding='utf-8') as file:
    # 逐行读取
    for line in file:
        try:
            # 解析 JSON 字符串为字典
            data = json.loads(line)
            content = data['response']['body']['choices'][0]['message']['content']
            json_response = json.loads(content[content.find('{'): content.rfind('}') + 1])
            all_paper.append(json_response)
            print(json_response)
        except:
            pass
print(len(all_paper))
save_to_json(all_paper, 'result.json')

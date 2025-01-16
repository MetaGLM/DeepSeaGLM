import json
import concurrent.futures as cf
import ai_brain
import time


def process_one(question_json):
    line = question_json
    query = line["question"]
    try:
        print(f"Processing question ID {line['id']}: {query}")
        answer = ai_brain.get_answer(question=query)
        ans = str(answer)
        print(f"Answer for question ID {line['id']}: {ans}")
        return {"id": line["id"], "question": query, "answer": ans}
    except Exception as e:
        print(f"Error processing question ID {line['id']}: {e}")
        return {"id": line["id"], "question": query, "answer": "Error: " + str(e)}


def main():
    q_path = "../../assets/question.jsonl"
    result_path = "result.jsonl"
    result_json_list = []

    # 读取问题文件
    with open(q_path, "r", encoding="utf-8") as f:
        q_json_list = [json.loads(line.strip()) for line in f]
    # q_json_list=q_json_list[:1]
    # 使用 ThreadPoolExecutor 处理问题
    with cf.ThreadPoolExecutor(max_workers=20) as executor:
        future_list = [executor.submit(process_one, q_json) for q_json in q_json_list]
        for future in cf.as_completed(future_list):
            result_json_list.append(future.result())

    # 按 ID 排序结果
    result_json_list.sort(key=lambda x: x["id"])

    # 写入结果文件
    with open(result_path, "w", encoding="utf-8") as f:
        for result in result_json_list:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    start_time = time.time()  # 记录开始时间
    main()
    end_time = time.time()  # 记录结束时间
    elapsed_time = end_time - start_time  # 计算耗时
    elapsed_time_minutes = elapsed_time / 60  # 将秒转换为分钟
    print(f"程序运行时间: {elapsed_time_minutes:.2f} 分钟")

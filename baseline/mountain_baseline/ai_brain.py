import json
from zhipuai import ZhipuAI
import tools
import api
import os

folders = ["database_in_use", "data"]
if any(not os.path.exists(folder) for folder in folders):
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
    import data_process # for data process using
else:
    print("所有文件夹均已存在。不再重新预处理数据。")
    print("需要预处理数据，请删除文件夹后重新运行。")


def create_chat_completion(messages, model="glm-4-plus-0111"):
    client = ZhipuAI()
    response = client.chat.completions.create(
        model=model, stream=False, messages=messages
    )
    return response


# In[4]:


# choose_table
def choose_table(question):
    with open("dict.json", "r", encoding="utf-8") as file:
        context_text = str(json.load(file))
    prompt = f"""我有如下数据表：<{context_text}>
    现在基于数据表回答问题：{question}。
    分析需要哪些数据表。
    仅返回需要的数据表名，无需展示分析过程。
    """
    messages = [{"role": "user", "content": prompt}]
    response = create_chat_completion(messages)
    return str(response.choices[0].message.content)


# In[5]:


def glm4_create(max_attempts, messages, tools, model="glm-4-plus-0111"):
    client = ZhipuAI()
    for attempt in range(max_attempts):
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
        )
        print(attempt)
        print(response.choices[0].message.content)
        if (
                response.choices
                and response.choices[0].message
                and response.choices[0].message.content
        ):
            if "```python" in response.choices[0].message.content:
                # 如果结果包含字符串'python'，则继续下一次循环
                continue
            else:
                # 一旦结果不包含字符串'python'，则停止尝试
                break
        else:
            return response
    return response


function_map = {
    "calculate_uptime": api.calculate_uptime,
    "compute_operational_duration": api.compute_operational_duration,
    "get_table_data": api.get_table_data,
    "load_and_filter_data": api.load_and_filter_data,
    "calculate_total_energy": api.calculate_total_energy,
    "calculate_total_deck_machinery_energy": api.calculate_total_deck_machinery_energy,
    "query_device_parameter": api.query_device_parameter,
    "get_device_status_by_time_range": api.get_device_status_by_time_range,
}


def get_answer_2(question, tools, api_look: bool = True):
    filtered_tools = tools
    try:
        messages = [
            {
                "role": "system",
                "content": "不要假设或猜测传入函数的参数值。如果用户的描述不明确，请要求用户提供必要信息。",
            },
            {"role": "user", "content": question},
        ]
        # 第一次调用模型
        response = glm4_create(6, messages, filtered_tools)
        messages.append(response.choices[0].message.model_dump())
        function_results = []
        # 最大迭代次数
        max_iterations = 6
        for _ in range(max_iterations):
            if not response.choices[0].message.tool_calls:
                break
            # 获取工具调用信息
            tool_call = response.choices[0].message.tool_calls[0]
            args = json.loads(tool_call.function.arguments)

            function_name = tool_call.function.name
            # 执行工具函数
            if function_name in function_map:
                function_result = function_map[function_name](**args)
                # print(**args)
                function_results.append(function_result)
                messages.append(
                    {
                        "role": "tool",
                        "content": f"{function_result}",
                        "tool_call_id": tool_call.id,
                    }
                )
                response = glm4_create(8, messages, filtered_tools)
            else:
                print(f"未找到对应的工具函数: {function_name}")
                break
        return response.choices[0].message.content, str(function_results)
    except Exception as e:
        print(f"Error generating answer for question: {question}, {e}")
        return None, None


# In[6]:
def select_api_based_on_question(question, tools):
    # 根据问题内容选择相应的 API
    if "甲板机械设备" in question and "能耗" in question:
        api_list_filter = ["calculate_total_deck_machinery_energy"]
    elif "总能耗" in question:
        api_list_filter = ["calculate_total_energy"]

    elif "动作" in question:
        api_list_filter = ["get_device_status_by_time_range"]
        question = question + "动作直接引用不要修改,如【A架摆回】"
    elif "开机时长" in question:
        api_list_filter = ["calculate_uptime"]
        if "运行时长" in question:
            question = question.replace("运行时长", "开机时长")
    elif "运行时长" in question and "实际运行时长" not in question:
        api_list_filter = ["calculate_uptime"]
        question = question.replace("运行时长", "开机时长")
    else:
        # 如果问题不匹配上述条件，则根据表名选择 API
        table_name_string = choose_table(question)
        with open("dict.json", "r", encoding="utf-8") as file:
            table_data = json.load(file)
        table_name = [
            item for item in table_data if item["数据表名"] in table_name_string
        ]

        if "设备参数详情表" in [item["数据表名"] for item in table_name]:
            api_list_filter = ["query_device_parameter"]
            content_p_1 = str(table_name) + question  # 补充 content_p_1
        else:
            api_list_filter = ["get_table_data"]
            content_p_1 = str(table_name) + question
    # 过滤工具列表
    filtered_tools = [
        tool
        for tool in tools
        if tool.get("function", {}).get("name") in api_list_filter
    ]
    # 返回结果
    if "content_p_1" in locals():
        return content_p_1, filtered_tools
    else:
        return question, filtered_tools


def enhanced(prompt, context=None, instructions=None, modifiers=None):
    """
    增强提示词函数
    """
    enhanced_prompt = prompt.replace("XX小时XX分钟", "XX小时XX分钟，01小时01分钟格式")
    enhanced_prompt = prompt.replace(
        "发生了什么", "什么设备在进行什么动作，动作直接引用不要修改,如【A架摆回】"
    )
    return enhanced_prompt


def run_conversation_xietong(question):
    question = enhanced(question)
    content_p_1, filtered_tool = select_api_based_on_question(
        question, tools.tools_all
    )  # 传入 question
    # print('---------------------')
    # print(content_p_1,filtered_tool)
    answer, select_result = get_answer_2(
        question=content_p_1, tools=filtered_tool, api_look=False
    )
    return answer


def get_answer(question):
    try:
        print(f"Attempting to answer the question: {question}")
        last_answer = run_conversation_xietong(question)
        last_answer = last_answer.replace(" ", "")
        return last_answer
    except Exception as e:
        print(f"Error occurred while executing get_answer: {e}")
        return "An error occurred while retrieving the answer."


# In[7]:


if __name__ == "__main__":
    question = "在2024年8月24日，小艇最后一次落座是什么时候（请以XX:XX输出）？"
    question = "在2024年8月24日，A架第二次开机是什么时候（请以XX:XX输出）？"
    question = "统计2024/8/23上午A架的运行时长（以整数分钟输出）？"
    question = "24年8月27日下午17点16分发生了什么？"
    question = "2024/8/23 19:05什么设备在进行什么动作？"
    aa = get_answer(question)
    print("*******************最终答案***********************")
    print(aa)
    # 文件路径
    """
    question_path = "assets/question.jsonl"
    result_path = "./result.jsonl"
    intermediate_result_path = "./result_zj.jsonl"
    # 读取问题文件
    with open(question_path, "r", encoding="utf-8") as f:
        questions = [json.loads(line.strip()) for line in f]
    # 处理每个问题并保存结果
    questions=questions[:1] # 注释掉这一行以逐个回答全部问题
    results = []
    for question in questions:
        query = question["question"]
        # 调用AI模块获取答案
        try:
            answer =get_answer(question=query)
            answer_str = str(answer)
            print(f"Question: {query}")
            print(f"Answer: {answer_str}")
            result = {
                "id": question["id"],
                "question": query,
                "answer": answer_str
            }
            results.append(result)
            # 将中间结果写入文件
            with open(intermediate_result_path, "w", encoding="utf-8") as f:
                f.write("\n".join([json.dumps(res, ensure_ascii=False) for res in results]))
        except Exception as e:
            print(f"Error processing question {question['id']}: {e}")
    # 将最终结果写入文件
    with open(result_path, "w", encoding="utf-8") as f:
        f.write("\n".join([json.dumps(res, ensure_ascii=False) for res in results]))

"""

# Day 20｜演示与面试素材

下面保留项目的真实运行轨迹和面试讲解提纲；视频留到面试复习时补录。

## 三分钟项目演示

- 视频文件位置或链接：面试复习时补录，录完填写
- 录制日期：面试复习时补录，录完填写

| 时间段 | 准备展示什么 | 我实际运行的命令与屏幕结果 | 我准备怎么讲 |
|---|---|---|---|
| 0:00–0:30 | 一句话说明项目能做什么 | 运行 `app.py --help` | 这是一个可以分别选择 extract 和 ask 两个模式的小工具 |
| 0:30–1:15 | `extract` 抽取一段文本 | 命令与结果见项目 README | extract 模式可以将文本输出成标准 JSON 文本 |
| 1:15–2:15 | `ask` 调用计算器 | 见下方「计算器调用」 | ask 模式可以调用三个小工具对问题进行回答 |
| 2:15–3:00 | 展示错误回填和轮数上限 | 见下方「模拟天气调用」 | 模型收到错误后尝试修改参数；到达轮数上限时会停止 |

### 计算器调用

```text
.venv\Scripts\python.exe weeks\week02_tools\info_toolbox\app.py ask "100 ** 2？"
     [第 1 轮] 它点了 calculator
        id        = call_00_RBBwcnPwrnOzaZvX6xKd2420
        arguments = {"expression": "100 * 100"}
        → 本地执行 = 10000
100 ** 2 = 100 × 100 = **10000**
```

模型把问题中的幂运算改写成乘法参数；本地计算器只支持加减乘除和括号。

### 模拟天气调用

```text
.venv\Scripts\python.exe weeks\week02_tools\info_toolbox\app.py ask "南京模拟天气如何？"
     [第 1 轮] 它点了 get_weather
        id        = call_00_7R3lhxObisHgBQqdyTX84878
        arguments = {"city": "南京"}
        → 本地执行 = 工具执行失败：ValueError: 不支持城市名南京
     [第 2 轮] 它点了 get_weather
        id        = call_00_8HsENjjrj6DmplFyCYrz5683
        arguments = {"city": "Nanjing"}
        → 本地执行 = 工具执行失败：ValueError: 不支持城市名Nanjing
     [第 3 轮] 它点了 get_weather
        id        = call_00_5sYsQVZug1PZ59TNpbqf4358
        arguments = {"city": "北京"}
        → 本地执行 = {'city': '北京', 'temperature_c': 18, 'condition': '小雨'}
达到最大轮数！
```

以上工具调用轨迹和答复来自学员的真实运行；命令中的路径分隔符与引号统一为便于复制的写法。

## 面试可讲素材

每题用自己的话写 1～3 句，并指向项目里的相应函数或一次真实运行。讲不清的地方留作 Day 21 复盘。

1. 这个项目为什么有 `extract` 和 `ask` 两种模式？
   - 我的说法：能够使用结构化输出和工具调用两大核心功能
   - 对应代码或运行：app.py extract，app.py ask
2. 模型返回工具调用后，谁真正执行本地函数？结果怎样回到模型？
   - 我的说法：execute_tool_call执行，结果在下一轮通过chat_with_tools回到模型
   - 对应代码或运行：`tool_calling.py` 中的 `tool_result_or_error(...)` 执行工具，随后 `messages.append(...)` 保存带 `tool_call_id` 的结果；下一轮 `chat_with_tools(...)` 把消息发给模型。
3. 本地工具报错时，为什么要把错误回填？怎样防止无限循环？
   - 我的说法：让模型知道哪里错了，下一轮可以改正；设置最大轮数限制
   - 对应代码或运行：for round_no in range(1, max_rounds + 1):
4. 模拟天气与 SQLite 订单数据有哪些限制？向用户怎么说明？
   - 我的说法：查天气只能模拟天气快照输出，无法查看真实天气；查订单也只能查询固定假订单
   - 对应代码或运行："description": "得到一个城市的天气情况，数据是模拟快照。",
   - "description": "查固定报表的已支付订单情况,按城市返回已支付笔数和总金额。",

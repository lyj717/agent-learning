# 失败案例记录

用途：把每个真实的故障记下来。面试被问「你踩过什么坑」时，这是你最实在的素材。
每条控制在 5 行以内：现象 → 原因 → 修复 → 学到什么。

---

## 模板

### YYYY-MM-DD｜一句话描述现象

- **现象**：报什么错 / 表现什么异常
- **原因**：真正的原因（不是最表面的那个）
- **修复**：改了什么
- **学到**：下次怎么避免

---

## 记录

### 2026-09-30｜删掉脚手架里的 raise 之后，函数悄悄返回 None，报错反而跑到 main 里

- **现象**：`TypeError: 'NoneType' object is not iterable`，报错行指向 main 里的 `for doc in search("任意问题")`，而 search 本身看起来没毛病
- **原因**：把脚手架的 `raise NotImplementedError` 删掉、实现又还没写，函数体只剩注释；执行到底没碰到 return，Python 就隐式返回 None。原来那行 raise 会大声报错，删掉之后错误被推迟到调用它的地方才暴露
- **修复**：把「筛选 → 排序 → 截断」四步写完，最后统一 return 一份列表
- **学到**：报错现场常常不是错误源头，看到 NoneType 就顺着「谁返回了 None」往上找；自己写的函数保证每条路径都有 return

### 2026-09-30｜可变默认参数在多次调用之间串数据

- **现象**：`add_to_basket_wrong('苹果')` 返回 `['苹果']`，紧接着 `add_to_basket_wrong('香蕉')` 返回 `['苹果', '香蕉']`，第二次带着上一次的结果
- **原因**：默认值 `[]` 在函数**定义时**求值一次，作为默认值挂在函数对象上（`__defaults__` 里能直接看到），之后每个不传参的调用用的都是同一个列表。真正出事的条件是两条同时成立：默认值是可变对象，而且函数在调用中**原地修改**了它（append、extend、sort 之类）。字符串、数字、元组改不动，对它们做 `+=` 是新建一个再重新绑定名字，所以不会串；但列表的 `+=` 本身就是原地修改（走 `__iadd__`），照样出事，只有 `a = a + [1]` 这种写法才会新建
- **修复**：默认值写 `None` 当哨兵，函数体内 `if basket is None: basket = []` 再新建。判断用 `is None`，不要用 `== None`；也尽量不要用 `not basket`，否则调用者显式传进来的空列表会被丢掉
- **学到**：可变的默认值一律写 None，进函数再建；ruff 的 B006 规则专门抓这个，Pydantic 的 `Field(default_factory=list)` 是同一件事的自动挡

### 2026-09-30｜注解里的小写 any 不报错，但它是错的

- **现象**：`-> list[dict[str, any]]` 跑得好好的，`ruff check` 也说全过；只有类型检查器会报 `Function 'any' is not valid as a type`
- **原因**：小写 `any` 是内置函数（`any([True, False])` 里那个），大写的 `Any` 才是类型；而注解在运行时不做校验，写错也不会崩
- **修复**：改成 `Any`，文件顶部的 `from typing import Any` 已经导入了
- **学到**：注解不参与运行，「不报错」不等于「写对了」；写工具函数时这些注解会变成模型看到的参数 schema，写错会直接改变模型的行为

### 2026-10-04｜temperature 填 0，同一个问题问 5 次照样得到 3 种答案

- **现象**：prompt 一个字没改、`temperature=0.0` 跑 5 次，结果出现 3 种不同答案
- **原因**：这个模型默认开着思考模式（`thinking: enabled`、`reasoning_effort: high`），而官方文档在 `temperature` 那行写着「思考模式下不生效」——真正带随机性的是那段看不见的思考，温度管不到它
- **修复**：不再把「可复现」押在 temperature 上；要稳就自己缓存结果、对输出做校验
- **学到**：参数的作用域要看官方文档，不能靠旧模型的直觉；「温度 0 就该一模一样」已经不成立了

### 2026-10-05｜max_tokens 从 512 调到 1024，起名字还是空回答

- **现象**：让模型起名字，10 次调用全部 `finish=length`，输出 1024 个 token 全是思考，正文一个字没有，钱照付
- **原因**：`max_tokens` 限的是「思考 + 正文」的总量；思考把额度吃光，正文还没开始就被截断
- **修复**：把 `max_tokens` 调大（官方说思考模式默认输出预算是 64K），或者用 `thinking` / `reasoning_effort` 控制思考强度
- **学到**：推理模型的 token 账要把思考算进去；`finish_reason=length` 是判断依据，`content` 为空不一定代表请求失败

### 2026-10-05｜PyCharm 报「未解析的引用 'Conversation'」，可 pytest 明明能跑

- **现象**：测试文件里 `from conversation import Conversation` 被标红，命令行跑 `pytest` 一切正常
- **原因**：让这个导入成立的是 `pytest.ini` 里的 `pythonpath = .`；pytest 会读这一行，PyCharm 的静态检查不读，它只认「源码根」
- **修复**：右键 `chat_cli` 目录 → Mark Directory as → Sources Root（标记只存在 `.idea/`，换机器要重做一次）
- **学到**：IDE 标红不等于运行错误；先跑一遍再下结论，别急着改代码

### 2026-10-05｜一次提问发了三次请求，屏幕上的回答和账单都对不上

- **现象**：问一句话，实际发出 3 次请求；屏幕上显示的回答和历史里存下来的回答不是同一段（三次生成的文本并不一样）；`/cost` 只记了 1 次，账单少算三分之二
- **原因**：为了分别取到「返回的两个值」，把同一个调用写了三遍——`add_assistant(chat(...)[0])`、`usage = chat(...)[1]`、`print(chat(...)[0])`，于是每取一次就重新请求一次
- **修复**：一次调用、接住整个元组再分发——`text, usage = chat(payload, model=args.model)`，后面 `add_assistant(text)`、`usage_log.append(...)`、`print(text)` 都用这一份
- **学到**：`return a, b` 返回的是一个元组，解包接住就行，不用为了拿第二个值再调一次；远程调用是「有副作用、要花钱」的操作，一次业务动作只该调一次

### 2026-10-05｜改成流式之后，最简用法一跑就崩：「可选参数」默认是 None，却直接当列表用

- **现象**：不传 `usage_box` 调 `stream_chat`，正文全部打完、最后一块到达时才抛 `AttributeError: 'NoneType' object has no attribute 'append'`；另外收尾的空串被当成一块 yield 出去，回答后面还忘了换行，下一个提示符黏在同一行
- **原因**：从非流式改成流式，等于换了一整套数据形状，有三处「必须跟着改」的地方漏了——usage 只在最后一块上有、`content` 可能是 `None` 或空串、`print(end="")` 之后得自己补一个换行
- **修复**：`if usage_box is not None and chunk.usage is not None`、`if piece:`（挡掉空串）、循环结束后补一个 `print()`
- **学到**：换调用方式（非流式 → 流式）比换参数动的地方多；交付前至少跑三种输入——不传可选参数、内容为空、正常一条，缺一种就会漏

### 2026-10-06｜range(-1, -4) 是空的：日志说「已裁剪 6 条」，历史一条没少

- **现象**：`trim(2)` 返回 6、屏幕上打出「已裁剪6条记录」，可 `messages()` 还是 11 条、`turns()` 还是 5
- **原因**：`range(-1, -reserved)` 里起点比终点大、步长又是默认的 +1，得到的是**空序列**（`list(range(-1, -4)) == []`），`pop()` 一次都没跑；而那句日志在循环**外面**，照样打
- **修复**：别用 `pop()` 循环数数，一行切片就够：`self.history = self.history[-reserved:]`
- **学到**：日志要反映真实状态（打在真正改动的地方，或者打印「改前/改后长度」这种数得出来的值）；`range` 的步长方向是个默认坑

### 2026-10-06｜「删 N 条」和「删哪 N 条」是两件事

- **现象**：裁剪的条数完全正确（5 轮裁到 2 轮，真删了 6 条），可留下的是**最早**的 2 轮，正好和「保留最近」相反
- **原因**：`list.pop()` 不传参数时删的是最后一个元素（最新的那条），而裁剪要删的是最旧的
- **修复**：`del self.history[:len_del]`（或 `self.history = self.history[len_del:]`）；要删开头就别用 `pop()`
- **学到**：断言别只验数量，要验内容——测试里 `messages[1] == "问 4"` 那句才是真正钉住行为的；只写 `turns() == 2` 的话，这个 bug 能骗过测试

### 2026-10-06｜重构 main 时把末尾的 return 0 弄丢了，函数开始返回 None

- **现象**：pytest 报 `assert None == 0`；可命令行直接跑却看不出问题（`SystemExit(None)` 的退出码也是 0）
- **原因**：给 `while` 套 `try/except` 的时候，循环后面那句 `return 0` 被删掉了，函数走到末尾自然返回 None
- **修复**：`try/except` 之后补回 `return 0`
- **学到**：加一层 try 是重构，重构完要回头确认函数**每条路径**的返回值；自己手动跑没事不代表对——测试里那句 `assert code == 0` 就是干这个的

### 2026-10-06｜`line[8:]` 少切一位，存进去的事实前面多了个字母

- **现象**：`/remember 我叫刘小明` 之后，`facts.json` 里存的是 `"r我叫刘小明"`——多了一个 `r`
- **原因**：`"/remember"` 这串命令本身有 **9** 个字符（`/ r e m e m b e r`），写 `line[8:]` 就把命令自己的最后一个字母留在了内容里；数错一位
- **修复**：别数字符，用 `line.removeprefix("/remember").strip()`（切不错），或者 `line[len("/remember"):]`
- **学到**：硬编码下标是「数数」类 bug 的温床；标准库里有名字就叫「去掉前缀」的方法时，用它比自己数踏实

### 2026-10-06｜「追加写 + dump 一条」，把整份记忆写成了非法 JSON

- **现象**：`add_fact` 用 `"a"`（追加）+ `json.dump(text, ...)`，写一条时文件是 `"我叫刘小明"`（带引号的字符串，不是列表），写第二条变成 `"我叫刘小明""我在学 Agent"` —— `json.loads` 报 `JSONDecodeError: Extra data`，而代码里的 `except` 把它悄悄兜成「没有记忆」，**记忆全丢还不报错**
- **原因**：JSON 是「整个文件算一个文档」的格式，往尾巴上再接一个文档就坏；而且 dump 的对象该是**整个列表**，不是「一条」
- **修复**：读出来 → `append` 进列表 → 整份覆盖写回（`"w"` 或 `path.write_text`），三件事缺一不可
- **学到**：**格式决定模式**——「整个文档」配「读-改-写」，追加只适合 JSONL（一行一条）；另外 `except` 兜底时别顺手把「解析失败」当成「还没有数据」，否则错误会销声匿迹

### 2026-10-06｜`"\n-".join(facts)` 的第一条没有前缀（join 只插在元素之间）

- **现象**：拼出来的 system 是 `你记得关于用户的这些事实：\n我叫刘小明\n-我在学 Agent`——第一条没有 `- `，连字符后面还少个空格
- **原因**：`分隔符.join(列表)` 的分隔符**只插在元素之间**，不会出现在第一个元素前面（`"\n-".join(["a","b"]) == "a\n-b"`）
- **修复**：把前缀放进每个元素：`"\n".join(f"- {fact}" for fact in facts)`
- **学到**：要「每条都带前缀」，前缀就得属于元素；另外测试当时只查了「包含刘小明」，所以这个格式错照样绿——断言越具体，越能钉住真实行为

### 2026-10-06｜测试依赖了本机文件，红绿跟着本地状态变

- **现象**：`test_resilience.py` 里断言 system 内容正好是 `"测试"`；本机 `facts.json` 一有内容（手测留下的），三条测试立刻全红——看着像程序坏了，其实是被测试自己的环境搞的
- **原因**：测试跑了真实代码路径，而那条路径会读本机的 `FACTS_PATH`；测试没有把外部状态隔离
- **修复**：`monkeypatch.setattr(chat_cli, "FACTS_PATH", tmp_path / "facts.json")`，把文件指到临时目录
- **学到**：**测试必须自足**——凡是会读本地文件、环境变量、当前时间的地方，要么注入参数，要么在测试里替换掉；不然「昨天还绿今天就红」会让人怀疑人生

### 2026-10-07｜开了 JSON 模式，服务商却回 400 拒收整条请求

- **现象**：请求里带了 `response_format={"type": "json_object"}`，但 system 和 user 里都没提过「json」两个字，接口直接报 `BadRequestError: 400 - Prompt must contain the word 'json' in some form to use 'response_format' of type 'json_object'`，一次都没生成
- **原因**：JSON 模式在这家服务商这里是**契约式**的——你开这个开关，就必须在提示词里明确要 JSON。文档提过「要同时要求模型输出 JSON」，但没讲清不写会直接 400；我原以为最多是输出不稳定
- **修复**：system 里写死「只输出 JSON」并列出字段名与类型，一句话同时满足两个要求
- **学到**：接口的「开关」与「提示词」可能是绑定的；文档里那句轻描淡写的「你必须同时……」往往就是硬性校验，别当建议听

### 2026-10-07｜JSON 模式把 max_tokens 调小，返回的 content 是空串，`json.loads` 报 char 0

- **现象**：同一段文本、同一个提示词，`max_tokens=150` 与 `200` 时 `finish_reason=length`、`content` 是空字符串，`json.loads('')` 报 `JSONDecodeError: Expecting value (char 0)`；调到 `240` 就正常返回 JSON
- **原因**：思考 token 和正文共用 `max_tokens` 的额度（`completion_tokens=150` 全是思考），额度在思考阶段就用光了，正文一个字都没开始写。这和 2026-10-05 那条「起名字得到空回答」是同一个机制，只是这次被 `json.loads` 抢先暴露成了「JSON 解析失败」
- **修复**：看到 `finish_reason=length` 就不解析、直接加额度重试；把判断顺序定成「先看 finish_reason，再解析」
- **学到**：报错信息会骗人——`char 0` 的 JSON 解析失败，根因可能是「根本没有内容」；错误类型（JSON 格式错）和错误原因（输出被截断）经常隔着一层

### 2026-10-07｜ruff 拦下「列表里拼接字符串」，和沙箱里 .git 只读

- **现象**：写材料时在列表元素里用两段相邻字符串拼一句话，`ruff check` 报 `ISC004 Unparenthesized implicit string concatenation in collection`（它怀疑你漏了逗号，两段字符串本该是两个元素）；另外 AI 在沙箱里跑 `git add` / `git commit` 报 `Unable to create .../.git/index.lock: Permission denied`
- **原因**：ISC004 是「显式拼接要加括号」的规则——不加括号时，人看不出你是有意把两段接起来还是少打了逗号；git 那半是我这边沙箱把 `.git` 挂成只读，和仓库内容无关
- **修复**：把相邻的两段字符串包进一层括号 `("前半句" "后半句")`，意图就明确了；git 命令申请写权限后再跑
- **学到**：这类「防歧义」规则，防的就是写代码的人自己手滑；而环境权限类报错要先分清「谁在写、写到哪」，别急着去改代码

### 2026-10-07｜该填 null 的字段模型给了空串，`is not None` 把它算成了「解析成功」

- **现象**：第 9 条（气象台降温预报，压根没有姓名）抽出来的 `name` 有时是 `null`、有时是 `""`；`parse_or_none` 只判「拿到的是不是 dict」，两种写法都算成功，于是成功率照样是 100%，但「字段正确率」里这条是错的
- **原因**：提示词里四个字段的交代不一致——`phone` / `city` / `job` 都写了「原文里没有就填 null」，只有 `name` 写成「姓名，字符串」，没说缺失怎么办。真实抓到的思考原文里它就在纠结这件事（`reasoning_content`：「Schema says name 姓名，字符串. If not present? It doesn't sp…」），于是它在 `""` 和 `null` 之间掷骰子：同一条文本连跑 4 次，3 次 `null`、1 次 `""`
- **修复**：把「没有怎么办」写进**每一个**字段的交代，不留例外；判定也不能只看「拿没拿到 dict」，要对每个字段的值单独校验（Day 16 用 Pydantic 正面做）
- **学到**：**提示词里没交代的位置，模型不会报错，它会自己定一条规则**，而且每次定的可能不一样；「格式过关」和「值过关」是两关，成功率必须分开算——只报解析成功率，等于把这类错误藏起来了

### 2026-10-07｜装饰器顺序写反，校验器不报错、只是静默失效

- **现象**：把 `@classmethod` 写到 `@field_validator("name")` **外面**（顺序反过来），程序照常跑、模型照常创建，但传空串进去得到的是 `{'name': ''}`——校验器根本没执行；正确顺序得到 `{'name': None}`
- **原因**：装饰器从下往上套。正确顺序是「先包成类方法，再登记到字段上」，Pydantic 拿到的就是它认识的对象；反过来变成「先登记到裸函数，再包成类方法」，Pydantic 收集校验器时认不出来，**跳过它**，不抛任何异常。PyCharm 那句「此装饰器不会收到所预期的可调用对象；内置装饰器返回了特殊对象」说的正是这件事（虽然它标在了正确写法上，属于误报）
- **修复**：顺序按文档写（`@field_validator(...)` 在外、`@classmethod` 在内）；改完必须喂一个空串看它有没有变成 `None`
- **学到**：**「没报错」不等于「生效了」**——顺序类的错误经常走静默失效这条路，症状是脏数据一路流到下游才被发现；验证方式得是行为验证（喂输入、看输出），不是「有没有报错」

### 2026-10-07｜`.pytest_tmp` 被 SYSTEM 建走，AI 再跑 pytest 就报 [WinError 5]

- **现象**：AI 跑 `pytest --basetemp=.pytest_tmp` 时，pytest 在会话开始清空这个目录就报 `PermissionError: [WinError 5] 拒绝访问`，6 条用 `tmp_path` 的测试直接 error（另外 3 条照常通过）
- **原因**：`icacls .pytest_tmp` 显示它的权限只有 `NT AUTHORITY\SYSTEM` 和 `Administrators`——既不是学员的账号，也不是 AI 的沙箱账号，多半是某次从管理员权限的终端/PyCharm 里跑 pytest 时建下的。和 AGENTS 里说的「名字是你的、权限是别人的」是同一类问题，只是这次的建主是 SYSTEM
- **修复**：换一个新的 basetemp 立刻就好——`pytest -p no:cacheprovider --basetemp=.pytest_tmp_ai tests` 跑出 9 passed；想清掉旧的那个，用**管理员** PowerShell 执行 README「排错」那节的 `Remove-Item`
- **学到**：临时目录的权限跟着「谁建的」走，跟目录名无关；遇到 WinError 5 别去动代码，先看 `icacls` 判归属，再决定换目录还是清目录

### 2026-10-07｜AI 新加了 llm_client.py，却没在练习里交代它是什么

- **现象**：Day 16 练习的第 3 题 docstring 里写着「用 `make_client()`」「用 `chat_json(...)`」，但学员压根不知道这两个名字来自哪个文件、里面还有什么、为什么要用——他直接问「你都没告诉过我你写了 llm_client 文件，后面要做的事情我也看不懂」
- **原因**：AI 把「共用的请求层」当成基础设施自己建了，只在 `weeks/week02_tools/README.md` 的材料表里留了一行；而学员读的是**练习文件本身**。这正是 AGENTS 里那条「文档里提到的任何名字，都要说清怎么拿到」的翻版——上次是 `llm.BadRequestError`，这次是整个模块
- **修复**：把说明写进练习文件的头部 docstring：本目录有哪些文件、`llm_client.py` 是从 Week 01 的 `chat_cli/llm.py` 搬来的、三个函数各自干什么（含参数与返回值形状）、怎么 import、PyCharm 标红怎么办；第 3 题再补一段「先大白话说要干什么，再列 1~6 步」的流程
- **学到**：**新加的脚手架文件，必须在学员会打开的那个文件里自我介绍**——写进 README 不算，写进另一个文件的注释也不算。判据：学员只看手上这个文件，能不能知道每个陌生名字从哪来

### 2026-10-07｜AI 改学员文件时误删了他写的一行，`ruff --fix` 又删掉了一个 import

- **现象**：改写第 3 题 docstring 时，顺手把学员已经写下的 `client = make_client()` 一起删掉了；随后跑 `ruff check --fix`，它把「导入了但还没用到」的 `chat_json` 从 import 行里删掉——学员写到第 3 步会直接 `NameError`
- **原因**：两件事都是「用整块替换的方式改别人正在写的文件」导致的：替换块里带了学员的代码行、而 `--fix` 对「还没写到」的 import 一律当垃圾清理
- **修复**：补回 `client = make_client()`，把 `chat_json` 加回 import 并在旁边写明「第 3 题第 3 步会用到，别对这个文件跑 ruff --fix」；改动后用 `git diff` 逐行确认没带走别的东西
- **学到**：**改学员的文件要按「外科手术」标准**——替换块只包住自己写的字，改完必须看 diff；`ruff --fix` 这种自动清理工具别用在「写了一半」的文件上，它分不清「没用」和「还没用到」

### 2026-10-08｜Windows 上用 `zoneinfo` 报 `ModuleNotFoundError: No module named 'tzdata'`

- **现象**：演示里写 `datetime(..., tzinfo=ZoneInfo("Asia/Shanghai"))`，跑起来抛 `zoneinfo._common.ZoneInfoNotFoundError: 'No time zone found with key Asia/Shanghai'`，根因是它先去找 `tzdata` 包没找到；这个仓库的依赖里没有它
- **原因**：Linux/macOS 上时区数据由系统提供，`zoneinfo` 直接读得到；**Windows 没有这套东西**，CPython 会退回去 import 第三方的 `tzdata` 包——没装就用不了。这和代码写错无关，是平台差异
- **修复**：改用标准库自带的固定偏移：`CHINA_TZ = timezone(timedelta(hours=8))`，`datetime(..., tzinfo=CHINA_TZ)` 照样能输出 `+08:00`，不用装任何东西；确实需要夏令时规则时才去 `pip install tzdata`
- **学到**：**「标准库」不等于「在 Windows 上一定能用」**——`zoneinfo` 就是典型；报 `ModuleNotFoundError` 时先看它要的那个模块是不是「数据包」而不是「你写的模块」，这类缺的往往不是依赖写错，而是平台自带的东西在 Windows 上要另装

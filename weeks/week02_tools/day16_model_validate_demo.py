"""Day 16 加餐：`PersonExtract.model_validate_json(raw)` 到底执行了哪些工作。

你卡住的不是语法，是「PersonExtract 是什么、那一行在干嘛」。这个脚本把黑盒拆开：
每一步都打印一句话，跑一遍就看清了。完全离线，不花钱。

跑法：
    .venv\\Scripts\\python.exe weeks\\week02_tools\\day16_model_validate_demo.py
"""

import json

from pydantic import BaseModel, ValidationError, field_validator


def section(title: str) -> None:
    print(f"\n{'=' * 62}\n{title}\n{'=' * 62}")


# ============================================================
section("第 0 步：先看清楚 PersonExtract 到底是什么东西")
# ============================================================


class PersonExtract(BaseModel):
    """从一段文本里抽出来的一个人。四个字段都可能缺失，缺失就记 None。"""

    name: str | None = None
    phone: str | None = None
    city: str | None = None
    job: str | None = None

    @field_validator("name", "phone", "city", "job", mode="before")
    @classmethod
    def blank_to_none(cls, value):
        # 打印这一行，是为了让你看见「校验器什么时候被调用、拿到什么」
        print(f"          [before] 收到 {value!r}")
        if isinstance(value, str) and value.strip() == "":
            return None
        return value

    @field_validator("phone")
    @classmethod
    def phone_must_be_11_digits(cls, value):
        print(f"          [after ] 检查 {value!r}")
        if value is not None and not (value.isdigit() and len(value) == 11):
            raise ValueError(f"手机号必须是 11 位数字，收到 {value!r}")
        return value


print(f"  PersonExtract 本身是：{PersonExtract}")
print(f"  它的类型：{type(PersonExtract).__name__}  ← 它是个**类**（Class）")
print(f"  它声明了哪几个字段：{list(PersonExtract.model_fields)}")
print("  每个字段的类型和默认值：")
for field_name, field in PersonExtract.model_fields.items():
    print(f"      {field_name:<6} 类型={field.annotation}  默认={field.default!r}")


# ============================================================
section("第 1 步：model_validate_json 拿到一段**文本**")
# ============================================================

raw = '{"name": "刘小明", "phone": "13800138000", "city": "杭州", "job": "后端"}'
print(f"  传进去的东西：{raw!r}")
print(f"  它的类型：{type(raw).__name__}  ← 是字符串，不是 dict")
print("  所以第一步必然是：先把这段文本解析成 dict")
print("  （Pydantic 内部用自己的解析器，效果和 json.loads 一样）")
print(f"      json.loads 的结果：{json.loads(raw)}")


# ============================================================
section("第 2 步：拿 dict 里的值，**逐个字段**过检查")
# ============================================================

print("  下面这一段是同一个 raw 再跑一次，专门看校验顺序（看打印的缩进）：")
person = PersonExtract.model_validate_json(raw)
print("  顺序是：先 before 校验器 → 再类型检查 → 再 after 校验器。")
print("  每个字段都走一遍；四个字段走完，谁都没报警，才轮到第 3 步。")


# ============================================================
section("第 3 步：全过了，就造一个 PersonExtract 实例返回")
# ============================================================

print(f"  model_validate_json 返回的东西：{person}")
print(f"  它的类型：{type(person).__name__}  ← 是个**实例**（对象），不是 dict！")
print(
    f"  所以可以点出来用：person.name = {person.name!r}，person.city = {person.city!r}"
)
print(f"  想变回 dict：person.model_dump() = {person.model_dump()}")
print(f"  想变回 JSON 文本：person.model_dump_json() = {person.model_dump_json()}")


# ============================================================
section("失败时：任何一步不过，就不造实例，改成抛 ValidationError")
# ============================================================

CASES = [
    ("JSON 语法坏", '{"name": "李娜"', "连 dict 都没解析出来，所以 loc 是「整体」"),
    (
        "类型不对",
        '{"name": "张伟", "phone": 18600001111}',
        "类型检查就拦下了，after 校验器没轮到",
    ),
    (
        "格式不对（我们的规矩）",
        '{"name": "王芳", "phone": "138-0013-8000"}',
        "类型过了，卡在我们自己写的 after 校验器上",
    ),
    (
        "字段缺失",
        '{"city": "北京"}',
        "它**通过了**——因为四个字段我们都给了默认值 None（没有默认值的字段缺失才会报 missing）",
    ),
    (
        "多了没声明的字段",
        '{"name": "刘小明", "phone": "13800138000", "age": 30}',
        "也**通过了**——默认策略是「忽略没声明的字段」，age 被丢掉，不会报错",
    ),
]

for label, text, note in CASES:
    print(f"\n  ── {label}：{text}")
    try:
        result = PersonExtract.model_validate_json(text)
    except ValidationError as error:
        # error.errors()：一条条结构化的报错，见 Day 16 练习第 2 题
        for item in error.errors():
            where = ".".join(str(part) for part in item["loc"]) or "整体"
            print(f"      失败 @ {where}｜{item['type']}｜{item['msg']}")
    else:
        print(f"      通过：{result.model_dump()}")
    print(f"      说明：{note}")


# ============================================================
section("对比：字段没有默认值时，「缺失」就成了错误")
# ============================================================


class StrictPerson(BaseModel):
    """把必填字段写成「没有默认值」，缺了就是错。"""

    name: str
    phone: str | None = None


try:
    StrictPerson.model_validate_json('{"phone": "13800138000"}')
except ValidationError as error:
    item = error.errors()[0]
    print(f"  缺了没有默认值的字段 -> {item['type']}｜{item['msg']}")

print(
    "  所以「字段可不可以缺」，是由**模型定义**决定的：写了默认值就允许缺，没写就必须给。"
)


# ============================================================
section("dump 到底是什么意思：把几个 dump 摆在一起看")
# ============================================================

# 这几个 import 放在这里而不是文件顶部，是为了让上面几节先讲完（纯演示顺序，没别的意思）
from datetime import datetime, timedelta, timezone
from enum import Enum


class Level(str, Enum):
    """职级。枚举：把「只能是这几个值」写进类型里。"""

    junior = "初级"
    senior = "高级"


class Record(BaseModel):
    """一条带时间的记录，专门用来暴露「Python 对象」和「JSON 文本」的区别。"""

    name: str
    created_at: datetime
    level: Level


# timezone(timedelta(hours=8))：东八区的固定偏移，用来给时间带上时区。
#   timedelta(参数)：表示「一段时长」，timedelta(hours=8) 就是 8 小时；
#   timezone(偏移)：把这段偏移做成时区对象。
# 不写时区的话，datetime 是「裸的」，转成 JSON 只有 "2026-10-08T09:30:00"，
# 读的人不知道是哪个地方的时间。
# （也可以用 ZoneInfo("Asia/Shanghai")，但那要求装 tzdata 包，Windows 上默认没有——
#   这里用固定偏移，够用且不用装东西。）
CHINA_TZ = timezone(timedelta(hours=8))
record = Record(
    name="刘小明",
    created_at=datetime(2026, 10, 8, 9, 30, tzinfo=CHINA_TZ),
    level=Level.senior,
)

dumped = record.model_dump()
dumped_types = {key: type(value).__name__ for key, value in dumped.items()}
print(f"  record.model_dump()        -> {dumped}")
print(f"  里面每个值是什么类型：{dumped_types}")
print(
    "  注意：created_at 还是 datetime 对象，level 还是枚举——**这是 Python 原生对象，不是 JSON**"
)

jsoned = record.model_dump(mode="json")
jsoned_types = {key: type(value).__name__ for key, value in jsoned.items()}
print(f"\n  record.model_dump(mode='json') -> {jsoned}")
print(f"  里面每个值是什么类型：{jsoned_types}")
print("  还是 dict，但里面的值都换成 JSON 能表达的形式了（datetime → ISO 字符串）")

print(f"\n  record.model_dump_json()   -> {record.model_dump_json()}")
print(f"  类型：{type(record.model_dump_json()).__name__}  ← 这一步才是文本")

print("\n  那直接拿 model_dump() 的结果去喂 json.dumps 行不行？")
try:
    json.dumps(dumped)
except TypeError as error:
    print(f"      不行：TypeError: {error}")
print("  因为 json.dumps 只认识基础类型（dict/str/int/float/bool/None/它们的列表），")
print("  datetime 和枚举它不认识——要转文本就得用 model_dump_json()，或者 mode='json'。")

print(
    """\n  所以 dump 这个词的意思不是「转成 JSON」，而是「把内存里的对象**倒出来**」，
  倒成什么，看名字/参数：

      json.dump(对象, 文件)          倒进一个文件
      json.dumps(对象)               倒成字符串（s = string）
      model.model_dump()             倒成 **Python 原生对象**（dict、list、datetime 保持原样）
      model.model_dump(mode="json")  倒成 Python 对象，但值已换成 JSON 能表达的
      model.model_dump_json()        倒成 **JSON 文本**（一步到位）

  对照着记：读进来是 validate（validate_json 吃文本、validate 吃 dict），
            倒出去是 dump（dump_json 给文本、dump 给 Python 对象）。"""
)


# ============================================================
section("一句话总结：这些名字是同一个东西的不同入口")
# ============================================================

print(
    """  PersonExtract                     是类本身，不能直接用来看数据
  PersonExtract(name="刘小明")       直接给关键字参数，走同一套校验
  PersonExtract.model_validate(d)    给一个 dict，校验后返回实例
  PersonExtract.model_validate_json(s)  给一段 JSON 文本，校验后返回实例  ← 你用的这个
  PersonExtract.model_json_schema()  把「字段长什么样」导成 JSON Schema（给模型看的那份）

  所以那一行读成大白话就是：
      「喂给 PersonExtract 这套规矩一段 JSON 文本；
        合规矩就还我一个装好的对象，不合就把哪里不合告诉我（抛 ValidationError）。」"""
)

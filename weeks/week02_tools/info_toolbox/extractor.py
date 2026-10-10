"""结构化抽取：从 Day 16 已完成的校验与重试代码迁入。"""

from llm import chat_json, make_client
from pydantic import BaseModel, Field, ValidationError, field_validator

hint = (
    "name（姓名，字符串）、phone（手机号，字符串）、"
    "city（城市，字符串）、job（岗位，字符串）"
)


class PersonExtract(BaseModel):
    """从一段文本里抽出来的一个人：四个字段都可能缺失，缺失就记 None。"""

    name: str | None = Field(default=None, description="姓名；原文没有就填 null")
    phone: str | None = Field(
        default=None, description="11 位手机号；原文没有就填 null"
    )
    city: str | None = Field(default=None, description="城市；原文没有就填 null")
    job: str | None = Field(default=None, description="岗位；原文没有就填 null")

    @field_validator("name", "phone", "city", "job", mode="before")
    @classmethod
    def blank_to_none(cls, value):
        """把空串和「未知」这类的占位符归一成 None（在类型校验之前跑）。"""
        if isinstance(value, str):
            text = value.strip()
            if text in {"", "未知", "null", "N/A", "无"}:
                return None
            return text
        return value

    @field_validator("phone")
    @classmethod
    def phone_must_be_11_digits(cls, value):
        """电话要么是 None，要么是 11 位数字；不合规就抛 ValueError。"""
        if value is not None and not (value.isdigit() and len(value) == 11):
            raise ValueError("手机号必须是11位数字！")
        return value


def errors_to_hint(error: ValidationError) -> str:
    """把 Pydantic 的报错整理成一句给模型看的话，一条错一行。"""
    lines = []
    for item in error.errors():
        loc = ".".join(str(part) for part in item["loc"]) or "整体"
        lines.append(f"- 字段 {loc}：{item['msg']}（收到的值：{item['input']!r}）")
    return "\n".join(lines)


def extract_with_retry(
    text: str, *, attempts: int = 2, first_reply: str | None = None
) -> PersonExtract | None:
    """抽一次；不合格就回填错误重试，试满 attempts 次仍不合格返回 None。"""
    client = make_client()
    messages = [
        {"role": "system", "content": f"你是信息抽取助手，只输出 JSON。字段：{hint}"},
        {"role": "user", "content": f"从下面这段话里抽取字段，输出 JSON：{text}"},
    ]
    for round_no in range(attempts):
        if round_no == 0 and first_reply is not None:
            raw = first_reply
        else:
            raw, _ = chat_json(messages, client=client)
        try:
            return PersonExtract.model_validate_json(raw)
        except ValidationError as error:
            messages = [
                *messages,
                {"role": "assistant", "content": raw},
                {
                    "role": "user",
                    "content": f"你刚才的输出没通过校验：\n{errors_to_hint(error)}\n"
                    "请只输出修正后的 JSON，缺失的字段填 null。",
                },
            ]
    return None

"""Day 39：独立认识 PointStruct、point 编号和 payload，不打开数据库。"""

from qdrant_client.models import PointStruct


def main() -> None:
    """用已知正文和人工向量构造一条 point，说明字段用途和边界。"""
    print("Day 39｜向量和原文怎样放进同一条数据库记录？")
    print("\n这份演示在本周目标中的作用")
    print("本周做带出处的 RAG 问答，需要找回相关片段及其原始来源。")
    print("本演示对应向量存储：认识准备写入 Qdrant 的一条记录长什么样。")
    print("学完应能创建 PointStruct，区分数据库编号、向量和附带资料。")
    print("后续练习再把你已有的片段与真实向量装成记录，写入集合并查询。")

    print("\n1. 这是什么")
    print("collection 叫集合，是采用相同向量配置的一组记录，例如约定每条向量几维。")
    print("集合中的一条记录叫 point，可以先记成 id + vector + payload。")
    print("id 是数据库用来识别这条记录的编号；vector 是用于比较的向量。")
    print("payload 是附带资料，用字典保存原文、来源和片段编号等信息。")
    print("PointStruct 是 Qdrant Python 客户端提供的类，用来表示准备写入的 point。")

    print("\n2. 为什么需要它")
    print("只有向量数字，找到相近记录后仍不知道该读哪段原文、显示哪个出处。")
    print("把正文与来源放进 payload，后面取回命中记录时才能继续核对。")
    print("数据库编号和原片段编号用途不同，需要在记录里明确保存它们的对应。")

    print("\n3. 场景")
    print("手里已有一条设备说明，给它准备一个 point。本演示不连接或打开数据库。")
    print("下面正文是 AI 教学文本，二维数字也是人工指定，不是真实 embedding。")
    text = "归还设备前请核对电源线。"
    teaching_vector = [0.2, 0.8]
    print(f"已知正文：{text}")
    print(f"人工向量：{teaching_vector}，共 {len(teaching_vector)} 维")

    print("\n4. 代码与实际结果")
    print("导入：from qdrant_client.models import PointStruct")
    print("本课构造方式：PointStruct(id=编号, vector=向量, payload=附带资料)")
    print("id、vector 必填；本课 id 传正整数，vector 传普通 list[float]。")
    print("payload 可选，传 dict 或 None；构造后返回一个 PointStruct 对象。")
    # PointStruct(id=编号, vector=向量, payload=可选字典)：创建准备写入的一条记录。
    point = PointStruct(
        id=7,
        vector=teaching_vector,
        payload={
            "chunk_id": "equipment.txt#L2-L2",
            "source": "equipment.txt",
            "text": text,
        },
    )
    print(f"\n返回对象类型：{type(point).__name__}")
    print(f"point.id：{point.id!r}")
    print(f"point.vector：{point.vector!r}")
    print(f"point.payload：{point.payload!r}")
    print("本例的对应：数据库编号 7 → 原片段 equipment.txt#L2-L2。")
    print("原片段的路径编号放在 payload['chunk_id']，没有拿它直接当数据库编号。")

    without_payload = PointStruct(id=8, vector=[0.2, 0.8])
    print(f"省略可选 payload：{without_payload.payload!r}；期望 None。")
    print("省略后对象仍可创建，但这条对象没有本例需要的正文和来源资料。")

    print("\n5. 注意什么")
    print("Qdrant 的 point 编号支持整数或 UUID；本课选正整数，不另学 UUID。")
    print("任意路径字符串不是 UUID，不能把 Day 37 的路径式片段编号直接用于入库。")
    print("PointStruct 的构造与数据库接收记录是两步；创建对象不等于已经存入集合。")
    print("向量仍需符合目标集合配置；这里的人工二维向量不能放进本课的 512 维集合。")
    print("chunk_id、source、text 都是我们自己选择的 payload 键，不会自动生成。")
    print("库不会替我们核验正文和来源是否相符，仍需沿用原文回查来确认。")
    print("本例只教记录结构，payload 还可按需求增加字段；实际片段仍需保留原行范围。")
    print("本文件没有真实编码、批量转换或查询，也没有修改学员的资料和数据库。")


if __name__ == "__main__":
    main()

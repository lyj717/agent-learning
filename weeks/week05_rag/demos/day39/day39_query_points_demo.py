"""Day 39：认识 Qdrant 查询参数与带分数候选，为 RAG 检索保留出处。

用独立内存库和人工二维向量讲 query_points，不调用 embedding 或生成模型。
"""

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams


def main() -> None:
    """对照返回外层、候选字段、limit 与 payload 开关。"""
    print("Day 39｜数据库找回来的是什么？")
    print("\n这份演示在本周目标中的作用")
    print("本周要做带出处的 RAG 问答，存好向量后，需要根据问题取回候选原文。")
    print("本演示讲 query_points：传什么、结果分几层、从哪里取分数与出处。")
    print("学完应能读取候选，理解 limit 是最多几条，并保留 payload 中的来源。")
    print("练习 B 会把结果恢复成你熟悉的 Document；今天还不生成回答。")

    print("\n1. 这是什么")
    print("query_points 是 QdrantClient 的方法，根据查询向量查找库中接近的记录。")
    print("返回 QueryResponse 对象；它的 .points 是候选列表，每项叫 ScoredPoint。")
    print("候选的 .id 是数据库编号，.score 是分数，.payload 是随记录保存的信息。")
    print("这些是返回对象的属性，读取时不用另行构造 ScoredPoint。")

    print("\n2. 为什么需要它")
    print("原文和向量入库后，要根据一个问题选择少量候选，再交给后面的回答环节。")
    print("只拿分数会丢掉原文与出处，返回时需要把 payload 一起取出。")

    print("\n3. 场景")
    print(
        "下面使用本文件自己的内存库；三个二维向量由 AI 手工指定，不是真实 embedding。"
    )
    print("向量只用于看清排序，文本标签不代表它们经过了模型语义判断。")
    print(
        "先调用本文件末尾的 create_teaching_environment：建内存库并写入三条人工记录。"
    )
    # 数据来路见本文件末尾：手写 PointStruct → upsert 入库 → 返回这个客户端。
    client = create_teaching_environment()
    try:
        print("\n4. 代码与实际结果")
        print(
            "导入：from qdrant_client import QdrantClient；先取得已准备好的客户端对象。"
        )
        print(
            "本课调用：client.query_points(collection_name, query=向量, limit=最多条数,"
        )
        print("                              with_payload=True, with_vectors=False)")
        print("collection_name 必填：本例为 query_demo；query 本例传两维 float 列表。")
        print(
            "query 在 API 中可省略或传其他查询形式，但本课的相似度查询必须给出问题向量。"
        )
        print(
            "limit 可选，默认 10；with_payload 可选，当前版本默认 True，显式写明更清楚。"
        )
        print(
            "with_vectors 可选，默认 False：取回正文与出处就够时，不重复返回整条向量。"
        )
        query_vector = [1.0, 0.0]
        print(
            f"\n本次查询向量={query_vector}，也是手工指定；从刚才的 query_demo 集合找两条。"
        )
        # query_points(集合名, query=向量, limit=最多条数, ...)：返回 QueryResponse。
        response = client.query_points(
            collection_name="query_demo",
            query=query_vector,
            limit=2,
            with_payload=True,
            with_vectors=False,
        )
        print(
            f"外层类型={type(response).__name__}；.points 类型={type(response.points).__name__}"
        )
        print(f"本次候选数={len(response.points)}，最多 2 条。")
        for hit in response.points:
            print(
                f"候选类型={type(hit).__name__}；数据库 id={hit.id}；余弦分数={hit.score:.6f}"
            )
            print(f"  原文={hit.payload['text']}；来源={hit.payload['source']}")
            print(f"  vector={hit.vector}；本次没有要求返回向量。")
        print(
            "编号和 payload 来自先前写入的记录；score 是库比较查询向量与记录向量后算出的。"
        )
        print(
            "人工标签甲/乙只是手写标签；example_a.txt 等是手写来源名，本例没有读取这些文件。"
        )
        print(
            "vector=None 只表示返回结果没有附带向量；计算分数仍使用了库里保存的向量。"
        )

        no_payload = client.query_points(
            collection_name="query_demo",
            query=query_vector,
            limit=1,
            with_payload=False,
        )
        print(
            f"对照：with_payload=False 时，第一条候选的 payload={no_payload.points[0].payload}"
        )
        all_hits = client.query_points(
            collection_name="query_demo", query=query_vector, limit=5
        ).points
        print(f"库中只有三条，limit=5 实际也只返回 {len(all_hits)} 条。")
        print("本例未设置分数门槛，所以余弦很低甚至负分的记录仍可能作为候选返回。")

        print("\n5. 注意什么")
        print("本集合使用 COSINE，因此分数越大，按这种向量比较越接近；返回按分数降序。")
        print(
            "并列分数的候选不能靠先后顺序判谁更正确，limit 也不保证每条都有回答价值。"
        )
        print("取得候选不等于原文包含答案，是否支持结论仍要读原文；本课不设通用阈值。")
        print("查询向量应与入库向量采用兼容模型和生成方式，维度也要与集合配置相符。")
        print(".id 是数据库 point id；片段原来的编号要从自己保存的 payload 字段取回。")
        print("本演示库仅在内存中，不保存文件；练习会另测磁盘重开后的查询。")
    finally:
        client.close()


# ===== 运行环境：沿用前两份演示的集合与记录接口，不是本课 B 的实现 =====
def create_teaching_environment() -> QdrantClient:
    """提供本文件独立的三条人工记录，不依赖其他演示。"""
    # QdrantClient(':memory:')：创建只在内存中存在的本地数据库，无需服务器。
    client = QdrantClient(":memory:")
    # VectorParams(size=数字个数, distance=距离类型)：本集合固定两维，比较余弦。
    client.create_collection(
        "query_demo", vectors_config=VectorParams(size=2, distance=Distance.COSINE)
    )
    # PointStruct(id, vector, payload)：组装一条数据库记录；这里每个值都由 AI 手工给出。
    teaching_points = [
        PointStruct(
            id=11,
            vector=[2.0, 0.0],
            payload={"text": "人工标签甲", "source": "example_a.txt"},
        ),
        PointStruct(
            id=22,
            vector=[0.0, 1.0],
            payload={"text": "人工标签乙", "source": "example_b.txt"},
        ),
        PointStruct(
            id=33,
            vector=[-1.0, 0.0],
            payload={"text": "人工标签丙", "source": "example_c.txt"},
        ),
    ]
    print("\n准备入库的数据如下：编号、向量、正文和来源名都在本函数中手工写明。")
    for point in teaching_points:
        print(
            f"  id={point.id}；人工向量={point.vector}；"
            f"正文={point.payload['text']}；来源名={point.payload['source']}"
        )
    # upsert(集合名, points=记录列表, wait=True)：把上面已展示的记录写入集合。
    client.upsert(
        "query_demo",
        points=teaching_points,
        wait=True,
    )
    print("上面三条已写入内存集合 query_demo；下面才调用 query_points 查询。")
    return client


if __name__ == "__main__":
    main()

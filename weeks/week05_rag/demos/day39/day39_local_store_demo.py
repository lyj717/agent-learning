"""Day 39：认识本地向量库的保存、同 ID 覆盖与重开，为 RAG 保留正文和出处。"""

from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams


def main() -> None:
    """用一条人工二维记录，观察磁盘保存和按编号取回。"""
    print("Day 39｜程序关掉以后，向量、正文和出处还在吗？")
    print("\n这份演示在本周目标中的作用")
    print("本周要做带出处的 RAG 问答。Day 38 已把文字变成向量，今天学习存储和检索。")
    print("本演示只负责保存：把向量与正文、来源一起写入本地库，并验证关闭后仍能取回。")
    print("学完应能建立集合、写入记录、关闭并重开；练习会把这些操作用于资料片段。")
    print("下面使用 AI 手工指定的二维数字，没有 embedding 模型，也没有语义检索。")

    print("\n1. 这是什么")
    print("Qdrant 是向量数据库；qdrant-client 是 Python 调用库，这里使用它的本地模式。")
    print("collection（集合）是一组记录的容器，有名称，并约定向量维度与比较方式。")
    print("每条 point（记录）有 id、vector、payload：编号、向量、附带的普通数据。")
    print("payload 保存正文和出处；这些信息不能靠向量本身还原出来。")

    print("\n2. 为什么需要它")
    print("Python 列表随进程结束而消失；存到磁盘，下次启动就能复用已有资料。")
    print("同一个编号再次写入时，旧记录会被新内容覆盖，不能用编号重复来表示两条来源。")

    print("\n3. 场景")
    print("把设备借用说明存成一条记录，再更新该说明，关闭程序后按编号核对新正文。")
    print("本例把 source 当普通字符串保存；数据库 id 另用整数 1。")

    print("\n4. 代码与实际结果")
    print(
        "导入：QdrantClient 来自 qdrant_client；三个记录/配置类型来自 qdrant_client.models。"
    )
    # resolve() 得到绝对路径；以脚本位置定位，运行时不依赖终端当前目录。
    store_path = Path(__file__).resolve().parent / "outputs" / "store_demo"
    collection_name = "demo_notes"
    print(f"本例磁盘路径：{store_path}")
    print("QdrantClient(path=绝对路径字符串)：打开或新建本地库，返回客户端对象。")
    print('QdrantClient(":memory:") 则只存在内存，关闭后数据消失；不要同时传 path。')
    print("本地模式无需服务器地址或 API 密钥；本例不是远程数据库服务。")
    # QdrantClient(path=字符串)：打开本地磁盘库；返回的客户端用于后续操作。
    client = QdrantClient(path=str(store_path))
    try:
        print("\n4.1 建立集合")
        # collection_exists(collection_name=集合名) -> bool：检查是否已经存在。
        exists = client.collection_exists(collection_name=collection_name)
        print(f"集合已存在：{exists}；存在就复用，不删除已有记录。")
        if not exists:
            # VectorParams(size=维度, distance=比较方式)：本例约定二维和余弦。
            vector_config = VectorParams(size=2, distance=Distance.COSINE)
            # create_collection：传集合名与向量配置，创建成功返回 True。
            created = client.create_collection(
                collection_name=collection_name, vectors_config=vector_config
            )
            print(f"创建结果：{created}")
        print("size=2 限定每条向量含两个数字；Distance.COSINE 指定余弦比较方式。")

        print("\n4.2 写入一条记录")
        # PointStruct(id=编号, vector=数值列表, payload=附带数据)：描述待写记录。
        original_point = PointStruct(
            id=1,
            vector=[1.0, 0.0],
            payload={"source": "设备借用说明.md", "text": "借用设备需登记姓名。"},
        )
        print("PointStruct 的 id、vector 必填；payload 可选，本例用它保留原文和出处。")
        print("id 可用整数或 UUID；不能直接把任意相对路径当作 Qdrant 的字符串编号。")
        # upsert(collection_name, points, wait=True)：新增或覆盖，等待写入完成。
        first_result = client.upsert(
            collection_name=collection_name, points=[original_point], wait=True
        )
        print(f"写入返回 UpdateResult；status={first_result.status.value}")
        # count(..., exact=True) 返回 CountResult，.count 才是记录总数 int。
        before_update = client.count(collection_name=collection_name, exact=True).count
        print(f"写入后集合记录数：{before_update}")

        print("\n4.3 同一个 ID 再写一次")
        updated_point = PointStruct(
            id=1,
            vector=[0.8, 0.2],
            payload={
                "source": "设备借用说明.md",
                "text": "借用设备需登记姓名，并填写归还时间。",
            },
        )
        client.upsert(
            collection_name=collection_name, points=[updated_point], wait=True
        )
        after_update = client.count(collection_name=collection_name, exact=True).count
        print(f"再写 ID=1 后记录数：{after_update}；期望仍是 {before_update}")
        print("upsert 的 points 是列表；wait 可选且默认 True，这里显式写出等待行为。")
    finally:
        # close()：释放客户端和磁盘锁；同一路径重开前必须先关闭。
        client.close()
        print("第一个客户端已关闭。")

    print("\n4.4 用新客户端重开相同路径")
    reopened_client = QdrantClient(path=str(store_path))
    try:
        # retrieve：按 ids 取记录；with_payload/with_vectors 是可选的返回内容开关。
        records = reopened_client.retrieve(
            collection_name=collection_name,
            ids=[1],
            with_payload=True,
            with_vectors=False,
        )
        print("retrieve 必填集合名和 ids；返回 list[Record]，不是正文字符串。")
        print("with_payload=True 带回附加数据；with_vectors=False 不把向量带回。")
        print(f"取回条数：{len(records)}；期望：1")
        for record in records:
            payload = record.payload or {}
            print(f"id={record.id}；source={payload.get('source')}")
            print(f"正文：{payload.get('text')}；期望包含新加的归还时间要求。")
            print(f"vector 字段：{record.vector}；期望：None（本次未请求返回向量）")
    finally:
        reopened_client.close()

    print("\n5. 注意什么")
    print("同一路径不能由两个本地客户端同时占用；用 try/finally 保证及时 close。")
    print("集合已有的维度与比较方式不会因重开而改变，不要向二维集合塞 512 维向量。")
    print("本例只覆盖专用集合的 ID=1；重复运行不会多存一条，也不会删除其他编号。")
    print("retrieve 是按 ID 精确取回；向量相似度查询由另一份独立演示讲解。")
    print("磁盘库只是存储，不会重新训练模型，也不会自动检查正文是否能回答问题。")


if __name__ == "__main__":
    main()

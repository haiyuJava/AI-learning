import math


def cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    return dot / (norm_a * norm_b)


class SimpleEmbeddingModel:
    """
    模拟一个极简 embedding 模型。
    真实 embedding 是大模型生成的，这里为了方便理解，用关键词规则模拟。
    向量维度含义：
    [请假, 工资, 审批, 车辆, 密码]
    """

    def encode(self, text):
        vector = [0.0, 0.0, 0.0, 0.0, 0.0]

        if any(word in text for word in ["年假", "请假", "休假", "假期"]):
            vector[0] += 1.0

        if any(word in text for word in ["工资", "薪水", "薪资", "发薪"]):
            vector[1] += 1.0

        if any(word in text for word in ["审批", "流程", "提交", "申请"]):
            vector[2] += 1.0

        if any(word in text for word in ["车", "车辆", "车机", "汽车"]):
            vector[3] += 1.0

        if any(word in text for word in ["密码", "登录", "重置", "忘记"]):
            vector[4] += 1.0

        # 避免全 0 向量
        if sum(vector) == 0:
            vector = [0.01, 0.01, 0.01, 0.01, 0.01]

        return vector


class BruteForceVectorDB:
    """
    暴力搜索：每次查询都和所有 chunk 算相似度。
    """

    def __init__(self):
        self.items = []

    def add(self, item_id, text, vector):
        self.items.append({
            "id": item_id,
            "text": text,
            "vector": vector
        })

    def search(self, query_vector, top_k=3):
        results = []

        compared_count = 0

        for item in self.items:
            compared_count += 1
            score = cosine_similarity(query_vector, item["vector"])
            results.append({
                "id": item["id"],
                "text": item["text"],
                "score": score
            })

        results.sort(key=lambda x: x["score"], reverse=True)

        return results[:top_k], compared_count


class MiniIVFIndex:
    """
    一个极简 IVF 向量索引。

    IVF = Inverted File Index

    核心思想：
    1. 先准备几个中心点 centroid
    2. 每个向量插入时，分配到最近的 centroid 桶里
    3. 查询时，不扫描全部数据，只扫描最接近 query 的几个桶

    真实 Milvus / Faiss 的 IVF 更复杂，但核心思想类似。
    """

    def __init__(self, centroids):
        self.centroids = centroids
        self.buckets = {i: [] for i in range(len(centroids))}

    def _nearest_centroid_ids(self, vector, nprobe):
        scores = []

        for idx, centroid in enumerate(self.centroids):
            score = cosine_similarity(vector, centroid)
            scores.append((idx, score))

        scores.sort(key=lambda x: x[1], reverse=True)

        return [idx for idx, _ in scores[:nprobe]]

    def add(self, item_id, text, vector):
        nearest_bucket_id = self._nearest_centroid_ids(vector, nprobe=1)[0]

        self.buckets[nearest_bucket_id].append({
            "id": item_id,
            "text": text,
            "vector": vector
        })

    def search(self, query_vector, top_k=3, nprobe=1):
        """
        nprobe 表示查询几个桶。

        nprobe 越小：
        - 查询越快
        - 但可能漏掉正确结果

        nprobe 越大：
        - 查询越慢
        - 但召回率更高
        """

        bucket_ids = self._nearest_centroid_ids(query_vector, nprobe=nprobe)

        candidates = []
        compared_count = 0

        for bucket_id in bucket_ids:
            for item in self.buckets[bucket_id]:
                compared_count += 1
                score = cosine_similarity(query_vector, item["vector"])
                candidates.append({
                    "id": item["id"],
                    "text": item["text"],
                    "score": score,
                    "bucket": bucket_id
                })

        candidates.sort(key=lambda x: x["score"], reverse=True)

        return candidates[:top_k], compared_count, bucket_ids

    def print_buckets(self):
        print("\n========== IVF 索引桶结构 ==========")

        for bucket_id, items in self.buckets.items():
            print(f"\nBucket {bucket_id}:")
            for item in items:
                print(f"  {item['id']} - {item['text']} - vector={item['vector']}")


def main():
    embedding_model = SimpleEmbeddingModel()

    docs = [
        ("chunk_001", "年假申请需要在 OA 系统提交审批"),
        ("chunk_002", "请假流程需要直属领导审批"),
        ("chunk_003", "休假申请需要提前三天提交"),
        ("chunk_004", "工资发放时间是每月月底"),
        ("chunk_005", "薪资调整需要 HR 审批"),
        ("chunk_006", "车机密码忘记后可以重置"),
        ("chunk_007", "车辆登录失败可能是密码错误"),
        ("chunk_008", "汽车金融贷款需要提交资料"),
    ]

    brute_db = BruteForceVectorDB()

    # 这里人为定义几个中心点，用来模拟 IVF 的聚类中心
    # [请假, 工资, 审批, 车辆, 密码]
    centroids = [
        [1.0, 0.0, 0.5, 0.0, 0.0],  # 请假/审批类
        [0.0, 1.0, 0.3, 0.0, 0.0],  # 工资类
        [0.0, 0.0, 0.0, 1.0, 0.8],  # 车辆/密码类
    ]

    ivf_index = MiniIVFIndex(centroids)

    for item_id, text in docs:
        vector = embedding_model.encode(text)

        brute_db.add(item_id, text, vector)
        ivf_index.add(item_id, text, vector)

    ivf_index.print_buckets()

    query = "怎么申请年假？"
    query_vector = embedding_model.encode(query)

    print("\n========== 查询 ==========")
    print("query:", query)
    print("query_vector:", query_vector)

    print("\n========== 暴力搜索结果 ==========")
    brute_results, brute_compared_count = brute_db.search(query_vector, top_k=3)

    for r in brute_results:
        print(r)

    print("暴力搜索比较次数:", brute_compared_count)

    print("\n========== IVF 索引搜索结果：nprobe=1 ==========")
    ivf_results, ivf_compared_count, bucket_ids = ivf_index.search(
        query_vector,
        top_k=3,
        nprobe=1
    )

    print("搜索的 bucket:", bucket_ids)

    for r in ivf_results:
        print(r)

    print("IVF 比较次数:", ivf_compared_count)

    print("\n========== IVF 索引搜索结果：nprobe=2 ==========")
    ivf_results, ivf_compared_count, bucket_ids = ivf_index.search(
        query_vector,
        top_k=3,
        nprobe=2
    )

    print("搜索的 bucket:", bucket_ids)

    for r in ivf_results:
        print(r)

    print("IVF 比较次数:", ivf_compared_count)


if __name__ == "__main__":
    main()

    """
    centroids = [
    [1.0, 0.0, 0.5, 0.0, 0.0],
    [0.0, 1.0, 0.3, 0.0, 0.0],
    [0.0, 0.0, 0.0, 1.0, 0.8],]
    不是每次都扫描全部向量 而是先把向量分桶 查询时只查最可能相关的桶 query_vector 和所有 chunk_vector 
    都算一遍 IVF 搜索是query_vector 先找到最近的 bucket 只在这个 bucket 里查
    
    面试的时候说
    向量索引的核心作用是减少候选向量数量。暴力检索需要对所有向量计算相似度，而 IVF、HNSW 等索引会先把向量空间组织起来，
    查询时只访问最可能相关的一部分候选，从而提升搜索性能。代价是它通常是近似搜索，可能牺牲少量召回率。

    
    """
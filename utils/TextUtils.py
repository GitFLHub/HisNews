# TextUtils.py

import numpy as np
from Levenshtein import distance as levenshtein_distance
from sentence_transformers import SentenceTransformer, util
import torch
from tqdm import tqdm
from network.ProxySwitcher import ProxySwitcher
from utils.TorchUtils import TorchUtils
import re

class TextUtils:

    model = SentenceTransformer('all-MiniLM-L6-v2')

    @staticmethod
    def calculate_levenshtein_similarity(str1: str, str2: str) -> float:
        """
        计算基于Levenshtein距离的文本相似度。
        """
        len_str1 = len(str1)
        len_str2 = len(str2)
        max_len = max(len_str1, len_str2)
        if max_len == 0:
            return 1.0  # 避免除以0
        distance = levenshtein_distance(str1, str2)
        similarity = (max_len - distance) / max_len
        return similarity

    @staticmethod
    def calculate_jaccard_similarity(str1: str, str2: str) -> float:
        """
        计算基于Jaccard相似度的文本相似度。
        """
        set_str1 = set(str1.split())
        set_str2 = set(str2.split())
        intersection = set_str1.intersection(set_str2)
        union = set_str1.union(set_str2)
        if len(union) == 0:
            return 1.0  # 避免除以0
        similarity = len(intersection) / len(union)
        return similarity
    
    @staticmethod
    def calculate_cosine_similarity(str1: str, str2: str) -> float:
        """
        计算基于余弦相似度的文本相似度。
        """
        embeddings = TextUtils.model.encode([str1, str2], convert_to_tensor=True)
        cosine_scores = util.pytorch_cos_sim(embeddings[0], embeddings[1])
        return cosine_scores.item()
    
    @staticmethod
    def embedding_text_by_sentence_transformer(text: str) -> torch.Tensor:
        """
        使用SentenceTransformer模型对文本进行编码。
        """
        return TextUtils.model.encode(text, convert_to_tensor=True)
    
    @staticmethod
    def batch_embedding_text_by_sentence_transformer(texts: list, batch_size = 16) -> torch.Tensor:
        """
        使用SentenceTransformer模型对文本列表进行批量编码。
        """
        if len(texts) <= 16:
            return TextUtils.model.encode(texts, convert_to_tensor=True, show_progress_bar=False)

        # 批处理
        embeddings = []
        for i in tqdm(range(0, len(texts), batch_size), desc="Processing"):
            embeddings.extend(TextUtils.batch_embedding_text_by_sentence_transformer(texts[i:min(i + batch_size, len(texts))]))
        return torch.stack(embeddings)


    
    @staticmethod # 批量计算一个文本嵌入与多个文本嵌入之间的余弦相似度
    def calculate_cosine_similarity_batch(embedding: torch.Tensor, embeddings: torch.Tensor, device='cuda') -> np.ndarray:
        """
        批量计算一个文本嵌入与多个文本嵌入之间的余弦相似度。
        """
        if isinstance(embeddings, list):
            embeddings = torch.stack(embeddings)

        if isinstance(embedding, np.ndarray):
            embedding = torch.tensor(embedding)

        # 将嵌入向量转移到指定的设备
        embedding, embeddings = TorchUtils.move_to_device(embedding, embeddings, device=device)
        return util.pytorch_cos_sim(embedding, embeddings).cpu().numpy().flatten()
    
    @staticmethod # 对相似度进行排序，并返回排序后的索引
    def sort_similarity_index(similarity: np.ndarray) -> np.ndarray:
        """
        对相似度进行排序，并返回排序后的索引。
        """
        return np.argsort(similarity)[::-1]
    
    @staticmethod # 清理文本
    def clean_text(text: str) -> str:
        # 确保text是字符串 
        text = str(text) if text is not None else ''

        # 替换转义序列和多个空白字符为一个空格
        text = re.sub(r'\\[nt]', ' ', text)
        text = re.sub(r'\s+', ' ', text)

        # 除去字符串中的链接
        text = re.sub(r'http\S+', '', text)
        # 替换 英文逗号 为 中文逗号
        text = text.replace(',', '，')
        # 移除字符串首尾的空白字符
        return text.strip()




# # 计算批量文本的嵌入
# texts = ['I love machine learning', 'I love coding', 'I love data science']
# embeddings = TextUtils.batch_embedding_text_by_sentence_transformer(texts)

# input_text = 'I love machine learning'
# input_embedding = TextUtils.embedding_text_by_sentence_transformer(input_text)

# # 计算余弦相似度
# cosine_similarity = TextUtils.calculate_cosine_similarity_batch(input_embedding, embeddings)

# # 对相似度进行排序
# sorted_index = TextUtils.sort_similarity_index(cosine_similarity)

# # 输出排序后的文本
# for idx in sorted_index:
#     print(f'相似度: {cosine_similarity[idx]:.4f}, 文本: {texts[idx]}')

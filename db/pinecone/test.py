import openai
import pinecone

openai.api_key = "sk-******"
pinecone.init(api_key="4b7aee63-1125-4aad-9237-5d383cd7e7bd", environment="gcp-starter")

def createIndex():
  # 初始化索引
  index = pinecone.Index('embedding')

  # 获取私有数据
  file = open('./data.txt', 'r', encoding='utf-8')
  content = file.read()
  file.close()

  # 将私有数据转换为向量数据
  data_embedding_res = openai.Embedding.create(
    model="text-embedding-ada-002",
    input=content
  )

  # 写入并覆盖指定向量数据库已有内容
  index.upsert([
    ("亚运会首日中国比赛数据", data_embedding_res['data'][0]['embedding'], {"data": content})
  ])
  


if __name__ == '__main__':
  createIndex()
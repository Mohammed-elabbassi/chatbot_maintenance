from pymilvus import MilvusClient
c = MilvusClient(uri='http://localhost:19530')
print('Milvus version:', c.get_server_version())
print('Collections:', c.list_collections())
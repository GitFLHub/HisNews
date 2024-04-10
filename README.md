```
## 安装步骤
1. conda 安装
2. conda 新建虚拟环境 hisnews 

```bash
conda create --name hisnews python=3.7.13
```

clash 配置文件  allow-lan: true

```yaml
mixed-port: 7890
allow-lan: true
external-controller: 127.0.0.1:51392
secret: ''
```

```pip3
pip3 install torch==1.13.1 numpy==1.21.6 requests==2.28.2 PyYAML==6.0.1 lxml==4.9.3 tqdm==4.65.0 Levenshtein==0.23.0 sentence_transformers==2.2.2 fake_useragent==1.5.1
```

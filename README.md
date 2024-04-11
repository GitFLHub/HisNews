### 项目描述

新浪历史新闻爬取

### 爬取思路

访问站点 https://web.archive.org/ 查询 https://news.sina.com.cn/china/ 所有可用的时间戳

获取时间戳下的 https://news.sina.com.cn/china/ 的主页

获取所有的新闻 a 标签

爬取指定的内容，（标题，日期，内容，图片链接等）

### 特点

* 借助 clash restful api 实现代理切换（需要开启 TUN 模式）
* 支持动态更新时间戳，自动获取最新的时间戳
* 支持中继接力爬取数据

### 安装步骤

1. 使用conda进行安装：

```bash
conda create --name hisnews python=3.7.13
```

2. 执行以下命令安装所需依赖：
   注：requirement.txt 中的深度学习相关的依赖非必需，可删除 \utils\TextUtils 下相关的代码

```bash
pip3 install -r requirements.txt
```

3. 修改 clash 配置文件 config.yaml，使其具有如下特性：
   clash 路径 在 clash 界面 Home Directory 下

```yaml
mixed-port: 7890
allow-lan: true
external-controller: 127.0.0.1:XXXX
secret: ''
```

# 设定基础镜像
[cite_start]FROM python:3.10-slim [cite: 1]

# 设置工作目录
[cite_start]WORKDIR /app [cite: 1]

# 复制依赖文件
[cite_start]COPY requirements.txt . [cite: 1]
# 安装依赖
[cite_start]RUN pip install --no-cache-dir -r requirements.txt [cite: 1]

# 复制所有项目文件到工作目录
COPY . [cite_start]. [cite: 1]

# 创建静态文件目录 (如果需要)
[cite_start]RUN mkdir -p static [cite: 2]

# 声明容器对外暴露的端口
[cite_start]EXPOSE 5050 [cite: 2]

# 定义容器启动时运行的命令
[cite_start]CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5050"] [cite: 2]

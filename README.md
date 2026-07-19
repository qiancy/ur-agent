# 运行说明

## 后端运行

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 初始化数据库
```bash
python scripts/init_db.py
```

### 3. 启动后端服务
```bash
uvicorn src.app:app --host 0.0.0.0 --port 8000
```

## 前端运行

### 1. 安装依赖
```bash
pip install gradio
```

### 2. 启动前端
```bash
python frontend.py
```

## Docker运行

### 1. 构建Docker镜像
```bash
docker build -t uni-resource-agent .
```

### 2. 启动容器
```bash
docker-compose up -d
```

## 环境配置

设置环境变量：
```bash
export DB_HOST=localhost
export DB_NAME=uni_resource_agent
export DB_USER=postgres
export DB_PASSWORD=postgres
export DB_PORT=5432
export LLM_BASE_URL=http://localhost:8000/v1
export LLM_API_KEY=fake-key
```

## API接口

- `GET /` - 根路径
- `GET /health` - 健康检查
- `POST /query` - 处理用户查询
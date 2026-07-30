# 4个空间的模拟数据

> **Context说明**: `context` 是运行时概念，由 `ouid` (组织ID) 和 `puid` (人员ID) 组成，表示 "person@organization" 上下文

## 公司空间 (ouid: 1, puid: 101)

{
  "name": "公司",
  "type": "company",
  "assets": [
    {
      "name": "笔记本电脑",
      "type": "电子设备",
      "quantity": 5,
      "status": "active"
    },
    {
      "name": "办公桌",
      "type": "家具",
      "quantity": 10,
      "status": "active"
    }
  ],
  "personnel": [
    {
      "name": "张三",
      "role": "员工",
      "health_reminders": {
        "task": "年度体检",
        "due_date": "2026-12-31"
      }
    }
  ],
  "transactions": [
    {
      "amount": 5000.00,
      "category": "办公用品",
      "description": "采购办公用品"
    }
  ]
}

## 家庭空间 (ouid: 2, puid: 102)
{
  "name": "家庭",
  "type": "home",
  "assets": [
    {
      "name": "沙发",
      "type": "家具",
      "quantity": 1,
      "status": "active"
    },
    {
      "name": "电视",
      "type": "电子设备",
      "quantity": 1,
      "status": "active"
    }
  ],
  "personnel": [
    {
      "name": "李四",
      "role": "家庭成员",
      "health_reminders": {
        "task": "家庭健康检查",
        "due_date": "2026-11-15"
      }
    }
  ],
  "transactions": [
    {
      "amount": 2000.00,
      "category": "家庭支出",
      "description": "家庭日常开销"
    }
  ]
}

## 家庭空间2 (ouid: 3, puid: 103)
{
  "name": "家庭2",
  "type": "family",
  "assets": [
    {
      "name": "儿童玩具",
      "type": "玩具",
      "quantity": 3,
      "status": "active"
    }
  ],
  "personnel": [
    {
      "name": "小明",
      "role": "孩子",
      "health_reminders": {
        "task": "疫苗接种",
        "due_date": "2026-08-20"
      }
    }
  ],
  "transactions": [
    {
      "amount": 500.00,
      "category": "儿童用品",
      "description": "购买儿童用品"
    }
  ]
}

## 学校空间 (ouid: 4, puid: 104)
{
  "name": "学校",
  "type": "school",
  "assets": [
    {
      "name": "教科书",
      "type": "学习资料",
      "quantity": 20,
      "status": "active"
    }
  ],
  "personnel": [
    {
      "name": "王老师",
      "role": "教师",
      "health_reminders": {
        "task": "教学培训",
        "due_date": "2026-09-30"
      }
    }
  ],
  "transactions": [
    {
      "amount": 1000.00,
      "category": "教学用品",
      "description": "购买教学用品"
    }
  ]
}
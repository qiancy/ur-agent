"""
TDD HTTP API Tests (v5.1: person + membership + resource + warehouse)
"""
import pytest
from fastapi.testclient import TestClient
from src.app import app
from typing import Optional

client = TestClient(app)


# ============================================================================
# 数据管理工具
# ============================================================================

def create_test_data():
    """创建测试所需的基础数据"""
    # 创建组织
    org_resp = client.post("/organizations", json={
        "name": "测试组织",
        "org_type": "company",
        "description": "测试用途"
    })
    assert org_resp.status_code in (200, 201)
    return org_resp.json()


def delete_test_data(org_id: int):
    """清理测试数据"""
    # 清理逻辑根据实际需求实现
    pass


class TestHealth:
    def test_health(self):
        """测试健康检查"""
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_health_response_format(self):
        """测试健康检查响应格式"""
        resp = client.get("/health")
        data = resp.json()
        assert "status" in data
        assert isinstance(data["status"], str)


class TestOrganizationAPI:
    def test_list(self):
        """测试查询组织列表"""
        resp = client.get("/organizations")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 5
        
        # 验证数据结构
        if len(data) > 0:
            org = data[0]
            assert "id" in org
            assert "name" in org
            assert "type" in org
            assert "description" in org

    def test_list_with_filters(self):
        """测试带过滤条件的组织查询"""
        resp = client.get("/organizations", params={"org_type": "company"})
        assert resp.status_code == 200
        data = resp.json()
        for org in data:
            assert org["type"] == "company"

    def test_create(self):
        """测试创建组织"""
        resp = client.post("/organizations", json={
            "name": "测试公司",
            "org_type": "company",
            "description": "测试描述"
        })
        assert resp.status_code in (200, 201)
        data = resp.json()
        assert "id" in data
        assert data["name"] == "测试公司"

    def test_create_validation(self):
        """测试创建组织时的参数验证"""
        # 缺少必要字段
        resp = client.post("/organizations", json={"name": "T"})
        assert resp.status_code in (400, 422)  # FastAPI返回422

    def test_members(self):
        """测试查询组织成员"""
        resp = client.get("/organizations/1/members")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # 验证成员数据结构
        member = data[0]
        assert "id" in member
        assert "pid" in member
        assert "role" in member
        # oid可能不在成员对象中，通过组织ID查询本身已隐含


class TestPersonAPI:
    def test_list(self):
        """测试查询人员列表"""
        resp = client.get("/person", params={"oid": 1})
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # 验证数据结构
        person = data[0]
        assert "id" in person
        assert "name" in person
        assert "membership_role" in person

    def test_list_with_name_filter(self):
        """测试按名称过滤人员"""
        resp = client.get("/person", params={"oid": 1, "name": "刘"})
        assert resp.status_code == 200
        data = resp.json()
        for p in data:
            assert "刘" in p["name"]

    def test_create(self):
        """测试创建人员"""
        resp = client.post("/person", json={
            "name": "测试人",
            "birth_date": "1990-01-01"
        })
        assert resp.status_code in (200, 201)
        data = resp.json()
        assert "id" in data
        assert data["name"] == "测试人"

    def test_create_with_birth_date(self):
        """测试创建人员时包含生日"""
        resp = client.post("/person", json={
            "name": "测试人2",
            "birth_date": "1985-05-15"
        })
        assert resp.status_code in (200, 201)
        data = resp.json()
        assert data["birth_date"] == "1985-05-15"

    def test_person_not_found(self):
        """测试查询不存在的组织人员"""
        resp = client.get("/person", params={"oid": 99999})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 0


class TestResourceAPI:
    def test_list(self):
        """测试查询资源列表"""
        resp = client.get("/resource", params={"oid": 1})
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # 验证数据结构
        resource = data[0]
        assert "id" in resource
        assert "name" in resource
        assert "type" in resource
        assert "status" in resource

    def test_list_by_type(self):
        """测试按类型查询资源"""
        resp = client.get("/resource", params={"oid": 1, "resource_type": "physical"})
        assert resp.status_code == 200
        data = resp.json()
        for r in data:
            assert r["type"] == "physical"

    def test_create_physical(self):
        """测试创建物理资源"""
        resp = client.post("/resource", json={
            "oid": 1,
            "name": "测试物资",
            "resource_type": "physical",
            "unit": "个"
        })
        assert resp.status_code in (200, 201)
        data = resp.json()
        assert data["type"] == "physical"
        assert data["unit"] == "个"

    def test_create_financial(self):
        """测试创建财务资源"""
        resp = client.post("/resource", json={
            "oid": 1,
            "name": "测试资金",
            "resource_type": "financial",
            "amount": 50000,
            "currency": "CNY"
        })
        assert resp.status_code in (200, 201)
        data = resp.json()
        assert data["type"] == "financial"
        assert data["amount"] == 50000

    def test_create_human(self):
        """测试创建人力资源"""
        resp = client.post("/resource", json={
            "oid": 1,
            "name": "测试人力",
            "resource_type": "human",
            "pid": 1
        })
        assert resp.status_code in (200, 201)
        data = resp.json()
        assert data["type"] == "human"

    def test_create_knowledge(self):
        """测试创建知识资源"""
        resp = client.post("/resource", json={
            "oid": 1,
            "name": "测试知识",
            "resource_type": "knowledge",
            "content": "这是一份测试文档"
        })
        assert resp.status_code in (200, 201)
        data = resp.json()
        assert data["type"] == "knowledge"

    def test_filter_by_type(self):
        """测试按类型过滤资源"""
        resp = client.get("/resource", params={"oid": 1, "resource_type": "financial"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) > 0
        for r in data:
            assert r["type"] == "financial"


class TestWarehouseAPI:
    def test_list(self):
        """测试查询仓库列表"""
        resp = client.get("/warehouse", params={"oid": 1})
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # 验证数据结构
        warehouse = data[0]
        assert "id" in warehouse
        assert "name" in warehouse
        assert "code" in warehouse
        assert "location" in warehouse

    def test_list_with_name_filter(self):
        """测试按名称过滤仓库"""
        resp = client.get("/warehouse", params={"oid": 1, "name": "武库"})
        assert resp.status_code == 200
        data = resp.json()
        for w in data:
            assert "武库" in w["name"]

    def test_create(self):
        """测试创建仓库"""
        resp = client.post("/warehouse", json={
            "oid": 1,
            "name": "测试仓库",
            "code": "Z002",
            "location": "测试地点",
            "description": "测试描述"
        })
        assert resp.status_code in (200, 201)
        data = resp.json()
        assert data["name"] == "测试仓库"
        assert data["code"] == "Z002"


class TestResourceWarehouseAPI:
    def test_list(self):
        """测试查询资源-仓库明细"""
        resp = client.get("/resource-warehouse", params={"resource_id": 1})
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        
        if len(data) > 0:
            rw = data[0]
            assert "id" in rw
            assert "resource_id" in rw
            assert "location_path" in rw
            assert "quantity" in rw

    def test_list_by_location(self):
        """测试按库位路径过滤"""
        resp = client.get("/resource-warehouse", params={
            "resource_id": 1,
            "location_path": "A"
        })
        assert resp.status_code == 200
        data = resp.json()
        for rw in data:
            assert rw["location_path"].startswith("A")

    def test_create(self):
        """测试创建资源-仓库明细"""
        resp = client.post("/resource-warehouse", json={
            "resource_id": 1,
            "location_path": "A-1-001",
            "quantity": 100,
            "unit": "个"
        })
        assert resp.status_code in (200, 201)
        data = resp.json()
        assert data["location_path"] == "A-1-001"
        assert data["quantity"] == 100

    def test_create_total(self):
        """测试创建total库位记录"""
        resp = client.post("/resource-warehouse", json={
            "resource_id": 1,
            "location_path": "total",
            "quantity": 200,
            "unit": "个"
        })
        assert resp.status_code in (200, 201)

    def test_get_total(self):
        """测试获取资源总数"""
        resp = client.get("/resource-warehouse/total", params={"resource_id": 1})
        assert resp.status_code == 200
        data = resp.json()
        assert "total_qty" in data
        assert isinstance(data["total_qty"], (int, float))


class TestTransactionAPI:
    def test_list(self):
        """测试查询交易记录"""
        resp = client.get("/transaction", params={"oid": 1})
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        
        if len(data) > 0:
            txn = data[0]
            assert "id" in txn
            assert "amount" in txn
            assert "category" in txn
            assert "parties" in txn

    def test_list_with_limit(self):
        """测试限制返回数量"""
        resp = client.get("/transaction", params={"oid": 1, "limit": 5})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) <= 5

    def test_create(self):
        """测试创建交易"""
        resp = client.post("/transaction", json={
            "amount": 100.0,
            "category": "test",
            "description": "测试交易"
        })
        assert resp.status_code in (200, 201)
        data = resp.json()
        assert data["amount"] == 100.0
        assert data["category"] == "test"

    def test_create_with_party(self):
        """测试创建带参与方的交易"""
        # 先创建交易
        txn_resp = client.post("/transaction", json={
            "amount": 200.0,
            "category": "test",
            "description": "测试交易"
        })
        assert txn_resp.status_code in (200, 201)
        
        # 再创建参与方
        party_resp = client.post("/party", json={
            "pid": 1,
            "oid": 1,
            "transaction_id": txn_resp.json()["id"],
            "role": "payer",
            "description": "测试付款方"
        })
        assert party_resp.status_code in (200, 201)
        
        # 创建交易
        resp = client.post("/transaction", json={
            "amount": 500.0,
            "category": "test",
            "description": "带参与方的交易"
        })
        assert resp.status_code in (200, 201)

    def test_transaction_not_found(self):
        """测试查询不存在的组织交易"""
        resp = client.get("/transaction", params={"oid": 99999})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 0


class TestPartyAPI:
    def test_list(self):
        """测试查询参与方列表"""
        resp = client.get("/party", params={"oid": 1})
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        party = data[0]
        assert "id" in party
        assert "pid" in party
        assert "oid" in party
        assert "role" in party

    def test_list_with_pid_filter(self):
        """测试按人员ID过滤参与方"""
        resp = client.get("/party", params={"oid": 1, "pid": 1})
        assert resp.status_code == 200
        data = resp.json()
        for p in data:
            assert p["pid"] == 1

    def test_create(self):
        """测试创建参与方"""
        # 先创建交易
        txn_resp = client.post("/transaction", json={
            "amount": 100.0,
            "category": "test",
            "description": "测试交易"
        })
        assert txn_resp.status_code in (200, 201)
        txn_id = txn_resp.json()["id"]
        
        # 创建参与方
        resp = client.post("/party", json={
            "pid": 1,
            "oid": 1,
            "transaction_id": txn_id,
            "role": "payer",
            "description": "付款方"
        })
        assert resp.status_code in (200, 201)
        data = resp.json()
        assert data["role"] == "payer"

    def test_get_transaction_parties(self):
        """测试查询交易的所有参与方"""
        resp = client.get("/party/transaction/1")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)


class TestSummaryAPI:
    def test_summary(self):
        """测试获取财务汇总"""
        resp = client.get("/summary", params={"oid": 1})
        assert resp.status_code == 200
        data = resp.json()
        assert "oid" in data
        assert data["oid"] == 1
        
        # 验证汇总字段
        assert "total_outflow" in data
        assert "transaction_count" in data
        assert isinstance(data["total_outflow"], (int, float))
        assert isinstance(data["transaction_count"], int)

    def test_summary_empty(self):
        """测试获取空组织的汇总"""
        resp = client.get("/summary", params={"oid": 99999})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_outflow"] == 0.0
        assert data["transaction_count"] == 0


class TestChatAPI:
    def test_endpoint(self):
        """测试AI对话接口"""
        resp = client.post("/chat", json={"message": "hi", "oid": 1})
        assert resp.status_code in (200, 500, 503)
        if resp.status_code == 200:
            data = resp.json()
            assert "response" in data
            assert "oid" in data

    def test_chat_with_context(self):
        """测试带上下文的AI对话"""
        resp = client.post("/chat", json={
            "message": "蜀国有多少资源？",
            "oid": 1,
            "context": "resource_query"
        })
        assert resp.status_code in (200, 500, 503)
        if resp.status_code == 200:
            data = resp.json()
            assert "response" in data

    def test_chat_invalid_context(self):
        """测试无效上下文ID"""
        resp = client.post("/chat", json={
            "message": "测试",
            "oid": 99999
        })
        assert resp.status_code in (200, 400, 500)


# ============================================================================
# 集成测试类
# ============================================================================

class TestIntegration:
    """集成测试：完整业务流程"""
    
    def test_full_workflow(self):
        """测试完整业务流程：创建组织 -> 添加人员 -> 创建资源 -> 记录交易"""
        # 1. 创建组织
        org_resp = client.post("/organizations", json={
            "name": "集成测试组织",
            "org_type": "company",
            "description": "集成测试"
        })
        assert org_resp.status_code in (200, 201)
        org = org_resp.json()
        org_id = org["id"]
        
        # 2. 添加人员
        person_resp = client.post("/person", json={
            "name": "集成测试人",
            "birth_date": "2000-01-01"
        })
        assert person_resp.status_code in (200, 201)
        person = person_resp.json()
        person_id = person["id"]
        
        # 3. 添加组织成员
        member_resp = client.post("/organizations/members", json={
            "pid": person_id,
            "oid": org_id,
            "role": "测试角色"
        })
        assert member_resp.status_code in (200, 201)
        
        # 4. 创建资源
        resource_resp = client.post("/resource", json={
            "oid": org_id,
            "name": "集成测试资源",
            "resource_type": "physical",
            "unit": "个"
        })
        assert resource_resp.status_code in (200, 201)
        
        # 5. 创建仓库
        warehouse_resp = client.post("/warehouse", json={
            "oid": org_id,
            "name": "集成测试仓库",
            "code": "IT",
            "location": "测试地点"
        })
        assert warehouse_resp.status_code in (200, 201)
        
        # 6. 创建资源-仓库明细
        rw_resp = client.post("/resource-warehouse", json={
            "resource_id": 1,  # 使用第一个资源
            "location_path": "total",
            "quantity": 50,
            "unit": "个"
        })
        assert rw_resp.status_code in (200, 201)
        
        # 7. 创建交易
        txn_resp = client.post("/transaction", json={
            "amount": 1000.0,
            "category": "测试",
            "description": "集成测试交易"
        })
        assert txn_resp.status_code in (200, 201)
        
        # 8. 创建参与方
        party_resp = client.post("/party", json={
            "pid": person_id,
            "oid": org_id,
            "transaction_id": txn_resp.json()["id"],
            "role": "payer",
            "description": "付款方"
        })
        assert party_resp.status_code in (200, 201)
        
        # 9. 验证数据
        assert client.get("/organizations").json()[org_id - 1]["id"] == org_id
        assert len(client.get("/person", params={"oid": org_id}).json()) > 0
        assert len(client.get("/resource", params={"oid": org_id}).json()) > 0
        assert len(client.get("/transaction", params={"oid": org_id}).json()) > 0
        
        # 10. 清理
        delete_test_data(org_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

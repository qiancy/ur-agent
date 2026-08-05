"""
TDD Unit Tests (v5.1: person + membership + resource + warehouse)
"""
import unittest
from src.db.database import init_database, _fetch


class TestDatabaseSchema(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_database(drop_all=True)

    def test_tables_exist(self):
        tables = _fetch(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' ORDER BY table_name"
        )
        names = {r["table_name"] for r in tables}
        expected = {"organization", "person", "membership", "resource",
                    "warehouse", "resource_warehouse", "party", "transaction"}
        self.assertTrue(expected.issubset(names), f"Missing: {expected - names}")

    def test_no_old_tables(self):
        for table in ["assets", "physical_assets", "virtual_assets", "personnel"]:
            t = _fetch("SELECT table_name FROM information_schema.tables WHERE table_name = %s", (table,))
            self.assertEqual(len(t), 0, f"Old table {table} should not exist")

    def test_resource_has_new_fields(self):
        cols = _fetch("SELECT column_name FROM information_schema.columns WHERE table_name = 'resource'")
        names = {c["column_name"] for c in cols}
        self.assertIn("amount", names)
        self.assertIn("currency", names)
        self.assertIn("person_id", names)
        self.assertIn("unit", names)

    def test_warehouse_table(self):
        cols = _fetch("SELECT column_name FROM information_schema.columns WHERE table_name = 'warehouse'")
        names = {c["column_name"] for c in cols}
        self.assertIn("organization_id", names)
        self.assertIn("name", names)
        self.assertIn("code", names)

    def test_resource_warehouse_table(self):
        cols = _fetch("SELECT column_name FROM information_schema.columns WHERE table_name = 'resource_warehouse'")
        names = {c["column_name"] for c in cols}
        self.assertIn("resource_id", names)
        self.assertIn("location_path", names)
        self.assertIn("quantity", names)
        self.assertIn("unit", names)


class TestResourceCRUD(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_database(drop_all=True)

    def test_create_physical_resource(self):
        from src.db.database import create_resource, create_organization

        org = create_organization("测试", "company", None)
        r = create_resource(org["id"], "宝剑", "physical", unit="把")
        self.assertEqual(r["type"], "physical")
        self.assertEqual(r["unit"], "把")

    def test_create_financial_resource(self):
        from src.db.database import create_resource, create_organization

        org = create_organization("测试", "company", None)
        r = create_resource(org["id"], "金库", "financial", amount=10000, currency="黄金")
        self.assertEqual(r["amount"], 10000)
        self.assertEqual(r["currency"], "黄金")

    def test_create_human_resource(self):
        from src.db.database import create_resource, create_organization, create_person

        org = create_organization("测试", "company", None)
        p = create_person("张三")
        r = create_resource(org["id"], "兵力", "human", person_id=p["id"])
        self.assertEqual(r["person_id"], p["id"])

    def test_create_knowledge_resource(self):
        from src.db.database import create_resource, create_organization

        org = create_organization("测试", "company", None)
        r = create_resource(org["id"], "兵法", "knowledge", content="孙子兵法")
        self.assertEqual(r["content"], "孙子兵法")


class TestWarehouseCRUD(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_database(drop_all=True)

    def test_create_warehouse(self):
        from src.db.database import create_warehouse, create_organization

        org = create_organization("测试", "company", None)
        w = create_warehouse(org["id"], "测试仓库", "A", "北京")
        self.assertEqual(w["code"], "A")
        self.assertEqual(w["location"], "北京")


class TestResourceWarehouseCRUD(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_database(drop_all=True)

    def test_create_and_query(self):
        from src.db.database import (create_resource, create_resource_warehouse,
                                     query_resource_warehouse, get_resource_total,
                                     create_organization, create_warehouse)

        org = create_organization("测试", "company", None)
        wh = create_warehouse(org["id"], "测试仓库", "T1", "北京")
        r = create_resource(org["id"], "宝剑", "physical", unit="把")
        create_resource_warehouse(r["id"], wh["id"], "total", 100, "把")
        create_resource_warehouse(r["id"], wh["id"], "A", 60, "把")
        create_resource_warehouse(r["id"], wh["id"], "A-1-001", 30, "把")
        create_resource_warehouse(r["id"], wh["id"], "A-1-002", 30, "把")

        results = query_resource_warehouse(r["id"])
        self.assertEqual(len(results), 4)
        self.assertEqual({row["warehouse_id"] for row in results}, {wh["id"]})

        total = get_resource_total(r["id"])
        self.assertEqual(total["total_qty"], 100)


class TestThreeKingdomsDemo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        from scripts.init_db import main
        main()

    @classmethod
    def tearDownClass(cls):
        """drop_all 清掉了 demo/recording 数据，自动恢复"""
        import subprocess, sys, os
        from pathlib import Path
        repo_root = Path(__file__).resolve().parents[2]
        env = {**os.environ, "PYTHONPATH": str(repo_root)}
        if os.getenv("DEMO_ZHANSAN_PASSWORD"):
            subprocess.run(
                [sys.executable, "scripts/seed_demo_data.py"],
                cwd=repo_root, env=env, capture_output=True
            )
        if os.getenv("DEMO_LIUMING_PASSWORD"):
            subprocess.run(
                [sys.executable, "scripts/seed_recording_data.py"],
                cwd=repo_root, env=env, capture_output=True
            )

    def test_shu_resource_types(self):
        from src.db.database import query_resource, resolve_organization_id
        res = query_resource(resolve_organization_id("shu"))
        types = {r["type"] for r in res}
        self.assertIn("physical", types)
        self.assertIn("financial", types)
        self.assertIn("human", types)
        self.assertIn("knowledge", types)

    def test_shu_has_warehouse(self):
        from src.db.database import query_warehouse, resolve_organization_id
        wh = query_warehouse(resolve_organization_id("shu"))
        self.assertTrue(len(wh) > 0)

    def test_resource_warehouse_data(self):
        from src.db.database import (
            query_resource, query_resource_warehouse, get_resource_total,
            resolve_organization_id,
        )
        res = query_resource(resolve_organization_id("shu"), name="连弩")
        self.assertTrue(len(res) > 0)
        rw = query_resource_warehouse(res[0]["id"])
        self.assertTrue(len(rw) > 0)
        total = get_resource_total(res[0]["id"])
        self.assertEqual(total["total_qty"], 50)


if __name__ == "__main__":
    unittest.main()

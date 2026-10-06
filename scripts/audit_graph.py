"""Export reproducible Cypher evidence after bench_kg.py --judge."""
from pathlib import Path
import json
import os
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from src.graph import Neo4jGraph


QUERIES = {
    "labels": "MATCH (n) RETURN labels(n)[0] AS label, count(*) AS n ORDER BY n DESC",
    "relationships": "MATCH ()-[r]->() RETURN type(r) AS rel,count(*) AS n ORDER BY n DESC",
    "E1_unlinked": "MATCH (k:Case) WHERE NOT (k)-[:CHARGED_WITH]->() RETURN k.name AS name,k.doc_id AS doc_id",
    "E2_hoang_nato": "MATCH (p:Person)-[:INVOLVED_IN]->(k:Case)-[:CHARGED_WITH]->(:Crime)<-[:DEFINES]-(a:Article)-[:HAS_CLAUSE]->(cl:Clause) WHERE p.name CONTAINS 'Dương Minh Tuấn' RETURN DISTINCT k.name AS name,a.id AS article,cl.number AS clause,cl.penalty AS penalty,EXISTS {(k)-[:INVOLVES]->(:Substance)<-[:MENTIONS]-(cl)} AS substance_match ORDER BY name,clause",
    "E3_huy_duplicates": "MATCH (p:Person {name:'Cái Quang Huy'})-[:INVOLVED_IN]->(k:Case) RETURN k.name AS name,k.doc_id AS doc_id,k.date AS date ORDER BY doc_id",
    "Q6_mdma": "MATCH (k:Case)-[r:INVOLVES]->(:Substance {name:'MDMA'}) OPTIONAL MATCH (p:Person)-[:INVOLVED_IN]->(k) RETURN k.name AS name,k.doc_id AS doc_id,r.amount AS amount,collect(p.name) AS people ORDER BY doc_id,name",
    "E6_missing_charge": "MATCH (p:Person)-[r:INVOLVED_IN]->(k:Case) WHERE coalesce(r.charge,'')='' RETURN p.name AS person,r.role AS role,k.name AS case,k.doc_id AS doc_id",
}


def main():
    load_dotenv()
    graph = Neo4jGraph(os.getenv("NEO4J_URI", "bolt://localhost:7687"),
                       os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "password123"))
    try:
        evidence = {name: {"cypher": query, "rows": graph.run(query)} for name, query in QUERIES.items()}
        evidence["stats"] = graph.stats()
        evidence["context_hoang_nato"] = graph.context(
            "Giang hồ 'Hoàng Nato' bị bắt về hành vi gì, và hành vi đó có thể bị phạt tù tối đa bao nhiêu theo Bộ luật Hình sự?", [])
    finally:
        graph.close()
    Path("report/graph_audit.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

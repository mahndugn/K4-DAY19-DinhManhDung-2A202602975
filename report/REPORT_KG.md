# Báo cáo Day 19 — Flat RAG vs GraphRAG

**Họ tên:** Đinh Mạnh Dũng — **MSSV:** 2A202602975 — **Ngày:** 06/10/2026

Benchmark thực trên 18 Điều luật, 20 bài báo, 176 chunk, top_k=3, chunk_size=800. Cả hai pipeline dùng Gemini 3.5 Flash-Lite và Gemini Embedding 001. Graph có **198 node / 379 cạnh**. Dùng ontology gợi ý, không đăng ký bonus. Nguồn số liệu: [ket_qua_benchmark_kg.txt](../ket_qua_benchmark_kg.txt); bằng chứng Cypher: [graph_audit.json](graph_audit.json).

## 1. Chi phí

Hai bảng dưới được chép từ output do bench_kg.py sinh, không sửa file benchmark:

```text
== Indexing (one-off)
pipeline  calls    in_tok  out_tok       USD  seconds
flat        176         0        0   0.00000    115.4
graph       196     34619     5513   0.02417    206.1

== Querying (mean per question)
pipeline  recall  judge   in_tok  out_tok       USD  seconds
flat        0.51   1.50      696       76   0.00040     1.41
graph       0.94   1.83     5282      129   0.00191     2.00
```

| Chỉ số | Flat | Graph | Graph / Flat |
| --- | --- | --- | --- |
| Indexing USD được meter | 0,00000 | 0,02417 | Không xác định vì mẫu số 0, thiếu usage embedding |
| Indexing giây | 115,4 | 206,1 | 1,79× |
| Mỗi câu: USD được meter | 0,00040 | 0,00191 | 4,78× |
| Mỗi câu: giây | 1,41 | 2,00 | 1,42× |
| Mỗi câu: input token được meter | 696 | 5282 | 7,59× |

**Cách hiểu USD và token:** key được dùng theo free tier người dùng cung cấp. USD trong bảng là **ước tính tương đương trả phí cho phần token có usage**, không phải hóa đơn thực tế. Chat tính theo 0,30 USD input / 2,50 USD output mỗi triệu token, đối chiếu [bảng giá Google](https://ai.google.dev/gemini-api/docs/pricing) ngày 06/10/2026. Giá công bố cho embedding-001 là 0,15 USD/triệu input token theo [Google Developers Blog](https://developers.googleblog.com/en/gemini-embedding-available-gemini-api/). Endpoint OpenAI-compatible embedding trả `usage=None`, nên code không đo được token/cost embedding: số 0 ở Flat indexing thể hiện **thiếu phép đo**, không khẳng định embedding miễn phí ở paid tier. Không tự điền token phỏng đoán. Chi phí free tier thực tế kỳ vọng 0 trong hạn mức, nhưng repo không truy cập hóa đơn để xác minh.

Graph dựng thêm 20 lần chat để trích tin, tương ứng 34619 input và 5513 output token, khoảng 90,7 giây và 0,02417 USD tương đương trả phí. Luật trích regex không gọi LLM. Query Graph thêm nguyên văn khoản và các cạnh nên input tăng 7,59 lần; judge được benchmark gọi riêng và không cộng vào cost pipeline. Thời gian gồm truy xuất, pacing embedding và chờ retry, không chỉ latency model. Có một lần chờ rate limit 53,7 giây trong lần chạy thành công; vì vậy không xem 206,1 giây là tốc độ cơ sở khi không bị quota.

**Điểm hòa vốn:** Graph không tiết kiệm tiền mỗi câu trong phép đo này, nên không có số câu hỏi hữu hạn làm tổng chi phí Graph thấp hơn Flat. Phần tăng thêm tương đương trả phí đo được là khoảng `0,02417 + N × 0,00151 USD`, chưa kể embedding thiếu usage và chi phí Neo4j. Nếu chỉ xét công dựng graph 90,7 giây được chia cho nhiều câu, ở 100 câu là 0,907 giây/câu, ở 1000 câu là 0,091 giây/câu. Lợi ích ở đây là tăng chất lượng câu xuyên KB, không phải giảm USD.

## 2. Từng câu hỏi

| Câu | Loại | Flat recall / judge | Graph recall / judge | Thắng | Vì sao |
| --- | --- | --- | --- | --- | --- |
| Q1 | single-hop-law | 1,00 / 2 | 1,00 / 2 | Hòa chất lượng, Flat rẻ hơn | Định nghĩa tiền chất nằm trong chunk; graph thêm số Điều nhưng không tăng điểm. |
| Q2 | single-hop-news | 1,00 / 2 | 1,00 / 2 | Hòa chất lượng, Flat rẻ hơn | Hai người nhận tử hình đều có trong một bài. |
| Q3 | cross-kb | 0,33 / 1 | 1,00 / 2 | Graph | Crime nối vụ Lê Minh Thành với Điều 251 khoản 1. |
| Q4 | cross-kb | 0,33 / 1 | 0,67 / 1 | Graph thêm Điều; cả hai chưa đủ | Graph lấy khung cơ bản 7 năm rồi gọi đó là tối đa, bỏ khoản 4. |
| Q5 | cross-kb-multi-hop | 0,40 / 1 | 1,00 / 2 | Graph | MDMA dẫn tới khoản 4 Điều 250, đủ ngưỡng và khung hình phạt. |
| Q6 | aggregation | 0,00 / 2 | 1,00 / 2 | Graph theo recall; judge không phân biệt | Graph có đủ tên ba vụ chuẩn, nhưng liệt kê trùng; Flat không nêu đủ tên và thiếu vụ Viện Pháp y. |

Trên Q3–Q5, recall trung bình tính từ điểm từng câu là khoảng **0,36 → 0,89**; judge **1,00 → 1,67**. Q1–Q2 đều đạt recall 1,00 và judge 2 ở cả hai pipeline. Đây là một lần đo trên 6 câu, chưa đủ để khái quát cho mọi corpus. Recall dùng khớp substring, judge dùng cùng model chat, không phải người chấm độc lập.

## 3. Phân tích lỗi

### E2 — Thiếu ngữ cảnh luật: mức phạt tối đa bị biến thành khung cơ bản

- **Hiện tượng:** Q4 Graph trả “tức mức phạt tù tối đa là **07 năm**”, trong khi corpus và gold có khung cao nhất 20 năm hoặc tù chung thân.
- **Bằng chứng:** câu trả lời nguyên văn ở Q4 trong file benchmark. Truy vấn kiểm tra trên graph hiện tại:

```cypher
MATCH (p:Person {name:'Dương Minh Tuấn'})-[:INVOLVED_IN]->(k:Case)
      -[:CHARGED_WITH]->(:Crime)<-[:DEFINES]-(a:Article {id:'Điều 255 BLHS'})
      -[:HAS_CLAUSE]->(cl:Clause)
RETURN DISTINCT cl.number AS clause, cl.penalty AS penalty,
  EXISTS { (k)-[:INVOLVES]->(:Substance)<-[:MENTIONS]-(cl) } AS substance_match
ORDER BY clause;
```

Kết quả tương ứng trong graph_audit.json/E2_hoang_nato, lấy riêng Điều 255:

```text
1 | phạt tù từ 02 năm đến 07 năm                  | false
2 | phạt tù từ 07 năm đến 15 năm                  | false
3 | phạt tù từ 15 năm đến 20 năm                  | false
4 | phạt tù 20 năm hoặc tù chung thân             | false
5 | phạt tiền ... phạt quản chế, cấm cư trú ...   | false
```

- **Nguyên nhân:** context trong src/graph.py chọn khoản 1 hoặc khoản nhắc chất của vụ. Điều 255 nêu điều kiện tổ chức sử dụng, không dựa tên chất; do đó clause 4 tồn tại trong graph nhưng không vào prompt. Đó là lỗi retrieval, sau đó model suy rộng khung cơ bản thành tối đa.
- **Đề xuất sửa:** khi câu hỏi có “tối đa/cao nhất”, lấy các khoản hình phạt của Điều đúng tội người đó, không lọc theo substance; sửa context và GRAPH_PROMPT để phân biệt khung cơ bản/khung cao nhất. Prompt sẽ dài hơn, có thể tăng token, nhưng Điều 255 chỉ có 5 khoản. Chưa áp dụng thay đổi này trong benchmark đã nộp; giữ nguyên cấu hình để người chấm tái hiện lỗi.

### E3 — Cùng vụ Cái Quang Huy thành hai Case

- **Hiện tượng:** Q6 Graph liệt kê hai vụ vận chuyển của Cái Quang Huy dù chúng cùng mô tả lô MDMA hơn 9,6kg qua Nội Bài.
- **Bằng chứng:** truy vấn và hai dòng từ graph_audit.json/E3_huy_duplicates:

```cypher
MATCH (:Person {name:'Cái Quang Huy'})-[:INVOLVED_IN]->(k:Case)
RETURN k.name AS name,k.doc_id AS doc_id,k.date AS date ORDER BY doc_id;
```

```text
Vụ vận chuyển hơn 10kg ma túy từ Đức về Việt Nam qua sân bay Nội Bài
  doc_id=news-100260917203001265, date=2025-09-29
Vụ vận chuyển ma túy qua sân bay Nội Bài liên quan đến Cái Quang Huy
  doc_id=news-100260918080821054, date=""
```

Bài thứ hai là bài Lê Minh Thành, có một đoạn giới thiệu bài liên quan Cái Quang Huy ở cuối. Cả hai Case đều có MDMA amount “hơn 9,6kg” trong Q6_mdma. Q6 Graph đưa chúng vào mục 1 và 2; gold chỉ coi đây là một vụ. Người và Substance đã dùng node chung nhưng Case vẫn tách.

- **Nguyên nhân:** dữ liệu crawl giữ đoạn teaser bài liên quan; LLM coi đoạn ấy là vụ riêng; MERGE Case theo tên do LLM tạo không nhận biết hai tên mô tả cùng sự kiện. Đây là lỗi phối hợp crawl, extraction và khóa ontology, không phải MERGE thiếu constraint.
- **Đề xuất sửa:** loại teaser/navigation trong scripts/crawl_drug_corpus.py và lưu source span khi extract_news_cases; dùng id ổn định theo hồ sơ nếu có, hoặc bước đối chiếu người/địa điểm/khối lượng và lưu danh sách nguồn sau khi xác nhận. Đánh đổi là bước giải quyết thực thể tốn thêm công/LLM và có nguy cơ gộp nhầm hai vụ cùng người. Chưa tự động gộp chỉ vì chung tên người.

### E4 — Recall và judge không phản ánh đầy đủ chất lượng tổng hợp

- **Hiện tượng:** Q6 Flat recall=0,00 nhưng judge=2. Q6 Graph recall=1,00 và judge=2 dù lặp vụ.
- **Bằng chứng:** Q6 Flat trong benchmark liệt kê “Vụ việc [1]” với 4,3kg MDMA, “Vụ việc [2]” với Thành và 5 viên, “Vụ việc [3]” với 5,3kg MDMA. Không nêu đủ tên Cái Quang Huy/Lê Minh Thành/Pháp y tâm thần theo must_include. Hai lô 4,3kg và 5,3kg là cùng vụ vận chuyển, còn vụ Viện Pháp y bị thiếu. Q6_mdma trả **5 Case** trên graph, chứa đủ ba nhóm sự kiện gold nhưng có tách trùng. Graph liệt kê cả 5, vẫn được điểm đầy đủ.
- **Nguyên nhân:** keyword_recall chỉ kiểm tra tên có xuất hiện, không xét tính đúng, thiếu hay trùng sự kiện. Judge model chấm quá rộng, không đối chiếu từng sự kiện và không có rubric phạt trùng. Đây là lỗi phép đo, không thể xem judge=2 là bằng chứng mọi chi tiết đúng.
- **Đề xuất sửa:** thêm đánh giá entity/event precision–recall sau chuẩn hóa và đối chiếu nguồn; rubric judge yêu cầu liệt kê vụ còn thiếu/trùng, người chấm kiểm tra Q6. Phải thay phiên bản benchmark trong thí nghiệm riêng, không sửa bench_kg.py/test hiện tại để nâng điểm. Chi phí judge và kiểm tra thủ công sẽ tăng.

## 4. Kết luận

Flat RAG đủ khi câu trả lời nằm gọn trong một đoạn như Q1–Q2: cả hai đạt điểm tối đa, Flat dùng ít token hơn. Graph hữu ích khi cần nối người/vụ trong tin với Điều/khoản trong luật hoặc tổng hợp theo chất: Q3 và Q5 tăng từ recall 0,33/0,40 lên 1,00; trung bình 6 câu tăng 0,51 → 0,94.

Đổi lại Graph có công dựng thêm 90,7 giây, 20 lần LLM; input mỗi câu tăng 7,59× và độ trễ trung bình tăng 1,42× trong lần đo này. Khi corpus ít thay đổi, nhiều câu xuyên KB dùng lại graph sẽ giúp phân bổ chi phí dựng. Tuy vậy Q4 sai tối đa và Q6 trùng chứng minh cần kiểm tra truy xuất và giải quyết thực thể trước khi dùng kết quả quan trọng. Không suy ra lợi ích tài chính từ embedding cost=0, vì thiếu usage. Corpus luật theo phiên bản lab, không phải kiểm tra pháp luật hiện hành.

## 5. Tự kiểm

```text
$ .venv\Scripts\python.exe -m pytest tests/ -q
................................................                         [100%]
48 passed in 0.07s

$ .venv\Scripts\python.exe bench_kg.py --check
[OK] Dữ liệu: 18 điều luật, 20 bài báo
[OK] KG-1 link_entity
[OK] Neo4j kết nối được
[provider] chat = gemini:gemini-3.5-flash-lite | embedding = gemini:gemini-embedding-001
[OK] KG-2 build_graph: 148 node / 293 cạnh, đường xuyên 2 KB dài 2 cạnh
[OK] KG-3 context: 18 dữ kiện, có Điều 251
[OK] KG-4 GraphRAGAgent.answer
[OK] Chi phí check: 1 lần gọi LLM, $0.00243. Graph nhỏ (luật + 1 bài) vẫn còn trong Neo4j để bạn xem; chạy --judge để dựng graph đầy đủ.
```

Check chạy trước benchmark; graph đầy đủ trong ảnh/audit là kết quả benchmark 198 node / 379 cạnh. Không chạy lại check sau ảnh vì check xóa graph và chỉ dựng một bài. Đã kiểm tra thêm retry 429 tôn trọng delay, retry hữu hạn, lỗi hết credit dừng ngay, và giá chat 0,30/2,50 bằng mock offline. Không sửa tests có sẵn hoặc bench_kg.py.

Ảnh thực của Neo4j Browser, sinh bằng scripts/capture_neo4j.py sau :clear, không vẽ lại hay chỉnh sửa:

- [Đếm node](img/kg_count.png): đủ 7 label; Clause 99, Person 40, Article 18, Case 13, Crime 13, Substance 10, Location 5.
- [Cầu nối xuyên KB](img/kg_cross_kb.png): Graph và Results overview có Person, Case, Crime, Article; INVOLVED_IN, CHARGED_WITH, DEFINES.
- [Vụ tự chọn](img/kg_my_case.png): **Cái Quang Huy**, có Điều 250, MDMA, Ketamine và Hà Nội; ảnh cũng thể hiện 2 Case bị tách trùng.

**Hạn chế quy cách ảnh:** ảnh là toàn bộ viewport 1600×1000 của Neo4j Browser qua Edge headless, thấy ô truy vấn và kết quả/Results overview. Không có thanh địa chỉ hay viền cửa sổ hệ điều hành. Công cụ chụp cửa sổ native không kết nối được, nên chưa đáp ứng nguyên văn yêu cầu “cả cửa sổ trình duyệt”. Nếu cần đúng quy cách đó, mở localhost:7474 và chụp lại 3 truy vấn trong scripts/capture_neo4j.py; dữ liệu graph đã lưu trong container.

## Vấn đề gặp phải

1. OpenAI probe trả 429 credit_balance_exhausted. Không dùng provider này trong benchmark.
2. Gemini 2.5 Flash-Lite mặc định trả 404, đề nghị đổi gemini-3.5-flash-lite. Đã đặt GEMINI_CHAT_MODEL và provider trong .env, giữ nguyên API key; không commit .env.
3. Lần benchmark đầu bị 429 embedding free tier 100 request/phút, retry sau khoảng 52,8 giây. Đã thêm pacing 0,65 giây và retry có giới hạn trong src/llm.py rồi chạy lại từ đầu. File benchmark nộp là lần hoàn thành, không lấy số liệu của lần thất bại.
4. Công cụ native báo “Computer Use native pipe is unavailable ... The system cannot find the file specified. (os error 2)”; Chrome/IAB qua CUA không khả dụng. Đã chụp web viewport thực bằng Playwright thay thế, nêu hạn chế ở trên.
5. Chưa đo được token embedding, chưa có số liệu nhiều lần chạy hay hóa đơn xác thực. Chưa sửa các lỗi E2/E3 trong lần thí nghiệm này; các đề xuất là hướng cải tiến, không nhận là đã chứng minh sửa thành công.
# Chạy lại bài đã hoàn thành

Python 3.11, Docker Desktop, API key Gemini. `.env` đã có key trên máy này và bị Git bỏ qua.

```powershell
$env:PYTHONIOENCODING="utf-8"
.venv\Scripts\python.exe -m pip install -r requirements.txt
docker start neo4j-drug-kg
.venv\Scripts\python.exe -m pytest tests/ -q
.venv\Scripts\python.exe bench_kg.py --check
.venv\Scripts\python.exe bench_kg.py --judge
.venv\Scripts\python.exe scripts\audit_graph.py
```

Trong `.env`, đặt `LLM_PROVIDER=gemini`, `EMBEDDING_PROVIDER=gemini`, `GEMINI_CHAT_MODEL=gemini-3.5-flash-lite`. Không tự chuyển provider giữa một lần benchmark. Nếu dựng trên máy mới, dùng lệnh Docker trong LAB_GUIDE.md; trên máy này chỉ cần `docker start`.

`--check` **xóa và dựng lại graph nhỏ**. Luôn chạy check trước benchmark. Số liệu và extraction có thể thay đổi giữa các lần gọi model; báo cáo hiện tại tương ứng file benchmark đã nộp. Sau khi chạy lại cần cập nhật bảng, audit và ảnh theo lần mới.

Ảnh viewport có thể tái tạo bằng các lệnh tùy chọn:

```powershell
.venv\Scripts\python.exe -m pip install playwright==1.63.0
.venv\Scripts\python.exe scripts\capture_neo4j.py
```

Script dùng Microsoft Edge đã cài trên máy; không sửa hay vẽ ảnh kết quả. Để đáp ứng đúng yêu cầu chụp **toàn cửa sổ có thanh địa chỉ**, mở http://localhost:7474, đăng nhập bằng cấu hình Neo4j của lab, chạy `:clear` trước từng truy vấn trong script rồi chụp cửa sổ bằng công cụ của hệ điều hành. Người tự chọn là Cái Quang Huy.

Kết thúc khi không cần xem graph: `docker stop neo4j-drug-kg`. Container giữ dữ liệu để mở lại bằng `docker start`.

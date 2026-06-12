# Section 2 — Docker: Đóng Gói Agent Thành Container

## Mục tiêu học
- Hiểu container là gì và tại sao cần nó
- Viết Dockerfile đúng cách (single vs multi-stage)
- Dùng Docker Compose để chạy multi-service stack
- Tối ưu image size xuống dưới 500 MB

---

## Ví dụ Basic — Dockerfile Đơn Giản

```
develop/
├── app.py
├── Dockerfile          # Single-stage, dễ hiểu
├── .dockerignore
└── requirements.txt
```

### Chạy thử
```bash
# IMPORTANT: Build from project root!
cd ../..  # Go to project root

# Build image
docker build -f 02-docker/develop/Dockerfile -t agent-develop .

# Xem size
docker images agent-develop

# Chạy container
docker run -p 8000:8000 agent-develop

# Test
curl http://localhost:8000/health
```

---

## Ví dụ Advanced — Multi-Stage + Docker Compose

```
production/
├── app.py
├── Dockerfile              # Multi-stage build → image nhỏ hơn nhiều
├── docker-compose.yml      # Full stack: agent + vector store + redis
├── nginx/
│   └── nginx.conf          # Reverse proxy
├── .dockerignore
└── requirements.txt
```

### Chạy thử
```bash
# From project root
cd ../..  # if not already there

# Khởi động toàn bộ stack (1 lệnh!)
docker compose -f 02-docker/production/docker-compose.yml up

# Xem các service đang chạy
docker compose -f 02-docker/production/docker-compose.yml ps

# Test agent qua Nginx
curl http://localhost/health

# Dừng toàn bộ
docker compose -f 02-docker/production/docker-compose.yml down
```

### So sánh image size:

```bash
# Basic vs Advanced
docker images | grep agent
# agent-basic    ~  800 MB  ← python:3.11 base
# agent-advanced ~  160 MB  ← python:3.11-slim + multi-stage
```
**Kết quả chạy thực tế của bạn cho thấy sự khác biệt rất rõ rệt giữa hai môi trường:**

* Về Image Size: Trong file README.md, dung lượng dự kiến của bản basic là khoảng 800 MB. Tuy nhiên, trên máy, image agent-develop thực tế phình to lên tới 1.66GB. Điều này càng chứng minh rõ ràng sự cần thiết của Multi-stage build để tối ưu dung lượng xuống mức nhẹ nhất có thể (chỉ giữ lại runtime).

* Về Health Check Endpoint:

* Bản Basic: Chạy trực tiếp trên port 8000 và trả về JSON đơn giản: {"status":"ok","uptime_seconds":103.2,"container":true}.

* Bản Advanced: Chạy qua Nginx Reverse Proxy ở port 80 (bạn chỉ cần gọi localhost/health mà không cần port). Kết quả trả về chuyên nghiệp hơn với các header bảo mật của Nginx (X-Frame-Options, X-XSS-Protection) và payload chi tiết hơn: {"status":"ok","uptime_seconds":15.6,"version":"2.0.0","timestamp":"2026-06-12T08:37:21.167467"}.**
---

## Lý thuyết: Tại Sao Multi-Stage?

```dockerfile
# Stage 1: Builder — có đầy đủ tools để compile deps
FROM python:3.11 AS builder   # 1 GB
RUN pip install ...            # thêm deps vào layer này

# Stage 2: Runtime — chỉ copy những gì cần chạy
FROM python:3.11-slim          # 150 MB ← bắt đầu từ image sạch
COPY --from=builder ...        # copy chỉ /site-packages
```

**Kết quả:** Final image chỉ có runtime, không có pip, không có build tools → nhỏ và an toàn hơn.

---

## Câu hỏi thảo luận

1. Tại sao `COPY requirements.txt .` rồi `RUN pip install` TRƯỚC khi `COPY . .`?
* Docker build image theo cơ chế phân lớp (Layer Caching). Mỗi dòng lệnh trong Dockerfile tạo ra một layer mới.

* Source code của bạn (copy bằng COPY . .) sẽ thay đổi liên tục mỗi khi bạn sửa code, nhưng các thư viện trong requirements.txt thì rất ít khi thay đổi.

* Nếu copy requirements.txt và cài đặt trước, Docker sẽ lưu lại (cache) layer này. Những lần build sau, nếu requirements.txt không đổi, Docker bỏ qua bước tải thư viện tốn thời gian và chỉ build lại phần source code mới. Nếu làm ngược lại, mỗi lần sửa một dòng code, sẽ phải ngồi chờ pip install lại toàn bộ từ đầu.
2. `.dockerignore` nên chứa những gì? Tại sao `venv/` và `.env` quan trọng?
* File .dockerignore có chức năng tương tự .gitignore, dùng để ngăn không cho Docker copy các file/thư mục rác hoặc nhạy cảm từ máy tính vào "build context" (ngữ cảnh đóng gói).

* Tại sao venv/ quan trọng: Thư mục này chứa các thư viện Python được biên dịch riêng cho hệ điều hành hiện tại của bạn (Windows/macOS). Nếu copy chúng vào container (thường chạy Linux), ứng dụng sẽ bị lỗi vì sai hệ điều hành. Ngoài ra, nó làm dung lượng build context tăng lên hàng trăm MB một cách vô ích.

* Tại sao .env quan trọng: File .env chứa các bí mật (secrets) như API Key, Database Password. Nếu không ignore, file này sẽ bị "đóng băng" (baked) thẳng vào trong Docker image. Bất kỳ ai có được file image này (ví dụ bạn push lên Docker Hub) đều có thể trích xuất và đánh cắp thông tin bảo mật.
3. Nếu agent cần đọc file từ disk, làm sao mount volume vào container?
* Vì container là một môi trường bị cô lập, dữ liệu bên trong sẽ bị mất khi container bị xóa. Để đọc/ghi file lâu dài xuống ổ cứng thật của máy chủ (host), cần dùng kỹ thuật Volume Mounting.


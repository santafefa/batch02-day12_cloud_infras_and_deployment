# Solution Day 12

## Part 1-5: Exercises

### Part 1: Localhost vs Production

**Exercise 1.3: So sánh với advanced version**

| Feature      | Basic      | Advanced         | Tại sao quan trọng?                                       |
|--------------|------------|------------------|-----------------------------------------------------------|
| Config       | Hardcode   | Env vars         | Dễ dàng thay đổi cấu hình giữa các môi trường (dev, prod) mà không cần sửa code. Giúp giữ bí mật (secrets) an toàn, không bị commit vào Git. |
| Health check | ❌ Không có | ✅ Có (`/health`) | Giúp các nền tảng Cloud (như Railway, Kubernetes) biết được ứng dụng có còn "sống" hay không để tự động khởi động lại khi cần, tăng độ tin cậy. |
| Logging      | `print()`  | Structured (JSON)| Log có cấu trúc dễ dàng được thu thập, tìm kiếm, và phân tích bởi các hệ thống quản lý log tập trung (như Datadog, ELK), giúp gỡ lỗi nhanh hơn. |
| Shutdown     | Đột ngột   | Graceful         | Đảm bảo các request đang xử lý được hoàn thành trước khi tắt, tránh mất dữ liệu và mang lại trải nghiệm tốt hơn cho người dùng. |

---

### Part 2: Docker Containerization

**Exercise 2.1: Dockerfile cơ bản**

1.  **Base image là gì?**
    *   Là `python:3.11-slim`, một phiên bản gọn nhẹ của Python 3.11 trên nền tảng Debian, cung cấp môi trường runtime cần thiết cho ứng dụng.
2.  **Working directory là gì?**
    *   Là `/app`, đây là thư mục mặc định bên trong container nơi các lệnh tiếp theo (như `COPY`, `CMD`) sẽ được thực thi.
3.  **Tại sao `COPY requirements.txt` trước?**
    *   Để tận dụng cơ chế caching của Docker. Các thư viện trong `requirements.txt` ít khi thay đổi. Bằng cách cài đặt chúng ở một layer riêng biệt, những lần build sau nếu file này không đổi, Docker sẽ tái sử dụng layer đã cache, giúp tăng tốc độ build đáng kể.
4.  **`CMD` vs `ENTRYPOINT` khác nhau thế nào?**
    *   `ENTRYPOINT` xác định câu lệnh thực thi chính của container và khó bị ghi đè. `CMD` cung cấp các tham số mặc định cho `ENTRYPOINT` và có thể dễ dàng bị ghi đè khi chạy container (`docker run <image> <new_command>`).

**Exercise 2.4: Docker Compose stack architecture diagram**

Sơ đồ kiến trúc của stack `production` trong `02-docker`:
```
Client (Browser/curl)
       │
       ▼
  Nginx (Reverse Proxy & Load Balancer trên port 80)
       │
       ├─────────► Agent Instance 1 (port 8000) ───► Redis
       ├─────────► Agent Instance 2 (port 8000) ───► Redis
       └─────────► Agent Instance 3 (port 8000) ───► Redis
```
*   Client gửi request đến Nginx.
*   Nginx phân phối (load balance) request đến một trong các instance của Agent.
*   Tất cả các instance của Agent đều kết nối và chia sẻ chung một instance Redis để lưu trữ trạng thái (ví dụ: conversation history).

---

### Part 3: Cloud Deployment

**Exercise 3.2: So sánh `render.yaml` với `railway.toml`**

| Tiêu chí | `railway.toml` | `render.yaml` |
|---|---|---|
| **Định dạng** | TOML | YAML |
| **Cấu trúc** | Đơn giản, tập trung vào `build` và `deploy` (lệnh chạy, health check). | Chi tiết hơn, định nghĩa toàn bộ hạ tầng (services, databases, disks, env vars) trong một file. |
| **Quản lý Services** | Thường mỗi service có file `railway.toml` riêng hoặc quản lý qua UI/CLI. | Có thể định nghĩa nhiều services (web, worker, redis) và mối quan hệ giữa chúng trong cùng một file "Blueprint". |
| **Triết lý** | "Convention over Configuration" - Tự động hóa nhiều, cấu hình tối thiểu. | "Infrastructure as Code" - Khai báo tường minh mọi thứ, cho phép quản lý phiên bản hạ tầng qua Git. |

**Câu hỏi thảo luận (Deployment Options):**
1. **Tại sao serverless (Lambda) không phải lúc nào cũng tốt cho AI agent?**
   AI Agent thường có thời gian thực thi dài (chờ LLM API, suy luận nhiều bước), dễ bị dính timeout của Lambda (tối đa 15 phút, API Gateway 30s). Kích thước thư viện AI thường lớn vượt quá giới hạn của Lambda.
2. **"Cold start" là gì? Ảnh hưởng thế nào đến UX?**
   Là độ trễ khi hệ thống scale từ 0 lên 1 instance (phải khởi động container, load thư viện/model). Điều này gây delay vài giây đến chục giây cho request đầu tiên, làm giảm trải nghiệm người dùng (UX).
3. **Khi nào nên upgrade từ Railway lên Cloud Run?**
   Khi cần kiểm soát chi tiết về Concurrency, Auto-scaling phức tạp (max instances), tích hợp CI/CD tự động toàn diện qua Cloud Build, và cần bảo mật cấp doanh nghiệp (VD: Google Secret Manager).

---

### Part 4: API Security

**Exercise 4.1: API Key authentication**
*   **API key được check ở đâu?** Trong file `app/auth.py` qua hàm `verify_api_key` và được gọi thông qua cơ chế `Depends` của FastAPI trong router.
*   **Điều gì xảy ra nếu sai key?** Hệ thống sẽ reject request và ném ra lỗi `HTTPException` với status code `401 Unauthorized`.
*   **Làm sao rotate key (đổi key)?** Thay đổi giá trị biến môi trường `AGENT_API_KEY` trên Cloud Platform (Railway/Render) để server nhận key mới mà không cần sửa code. Phía client cũng cần được cấp key mới tương ứng.

**Exercise 4.3: Rate limiting**
*   **Algorithm nào được dùng?** Thuật toán Sliding window (Cửa sổ trượt) thông qua Redis Sorted Sets (`zremrangebyscore`, `zcard`, `zadd`).
*   **Limit là bao nhiêu requests/minute?** Mặc định là 10 requests / 1 phút (lấy từ biến môi trường `RATE_LIMIT_PER_MINUTE`).
*   **Làm sao bypass limit cho admin?** Thêm logic vào hàm `check_rate_limit`: Nếu `user_id` khớp với admin key, sẽ `return` luôn mà không ghi nhận log vào Redis.

**Câu hỏi thảo luận (API Gateway & Security):**
1. **Khi nào nên dùng API Key vs JWT vs OAuth2?**
   - **API Key:** Dùng cho giao tiếp Service-to-Service (server gọi server), script tự động hoặc internal API. Nhanh, dễ cấu hình, nhưng khó phân quyền chi tiết.
   - **JWT (JSON Web Token):** Dùng cho giao tiếp Client-to-Server (Mobile app, Web SPA). Chứa sẵn thông tin user (stateless) giúp giảm tải truy vấn Database khi check phiên đăng nhập.
   - **OAuth2:** Dùng khi muốn cho phép ứng dụng bên thứ 3 truy cập tài nguyên của user mà không lộ mật khẩu (vd: "Đăng nhập bằng Google/Facebook").
2. **Rate limit nên đặt bao nhiêu request/phút cho một AI agent?**
   - Các tác vụ AI thường tốn kém (gọi API trả phí của LLM) và mất thời gian xử lý. Do đó, nên đặt thấp hơn các API thông thường, khoảng **10 - 20 requests/phút** cho người dùng cơ bản để tránh bị spam làm cạn kiệt ngân sách nhanh chóng.
3. **Nếu API key bị lộ, bạn phát hiện và xử lý như thế nào?**
   - **Phát hiện:** Thông qua hệ thống cảnh báo chi phí (Billing Alert) khi budget tăng đột biến, log giám sát thấy traffic tăng bất thường từ IP lạ, hoặc các công cụ dò quét mã nguồn bị public (như GitHub Secret Scanning).
   - **Xử lý:** Vô hiệu hóa (Revoke) key cũ ngay lập tức. Đổi biến môi trường trên server để sinh key mới (Rotate) cấp cho các client hợp lệ. Kiểm tra audit log xem hacker đã dùng key cũ để làm gì (có lấy cắp dữ liệu hay chỉ spam).

---

### Part 5: Scaling & Reliability

**Câu hỏi thảo luận (Stateless & Scale):**
*   **Tại sao stateless quan trọng khi scale?** 
    Khi scale out thành nhiều instance, load balancer sẽ điều phối request ngẫu nhiên đến các instance khác nhau. Nếu lưu trữ trạng thái (như lịch sử trò chuyện) trong RAM của từng instance (Stateful), dữ liệu sẽ bị gián đoạn và mất đồng bộ. Việc thiết kế Stateless (đẩy toàn bộ state ra Redis) giúp bất kỳ instance nào cũng có thể đọc và ghi đồng nhất, xử lý mượt mà mọi request tiếp theo từ user.

---

## Part 6: Final Project

Dự án AI Agent đã được "production-ready" hóa bằng cách áp dụng các nguyên tắc từ Part 1 đến 5 và triển khai thành công lên nền tảng Railway.

*   **Project:** Production-ready AI Agent
*   **API URL Link:** `https://ai-agent-lab-prod-production.up.railway.app`
*   **API Key dùng để test:** `secret-agent-key` (Hoặc giá trị đã được thiết lập trên Railway)

### Hướng dẫn test API:

Sử dụng PowerShell với lệnh `Invoke-RestMethod`:
```powershell
Invoke-RestMethod -Uri "https://ai-agent-lab-prod-production.up.railway.app/ask" -Method POST -Headers @{ "X-API-Key" = "secret-agent-key"; "Content-Type" = "application/json" } -Body '{"question": "What is Docker?"}'
```

**Kết quả mong đợi:**
```json
{
  "answer": "Docker is a platform for developing, shipping, and running applications in containers.",
  "conversation_history": [
    {
      "role": "user",
      "content": "What is Docker?"
    },
    {
      "role": "assistant",
      "content": "Docker is a platform for developing, shipping, and running applications in containers."
    }
  ]
}
```
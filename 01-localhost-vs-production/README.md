# Section 1 — Từ Localhost Đến Production

## Mục tiêu học
- Hiểu tại sao "it works on my machine" là vấn đề
- Nhận ra sự khác biệt giữa dev và production environment
- Áp dụng 4 nguyên tắc 12-factor cơ bản

---

## Ví dụ Basic — Agent "Kiểu Localhost"

```
develop/
├── app.py          # ❌ Anti-patterns: hardcode secrets, no config, no health check
├── .env.example
└── requirements.txt
```

### Chạy thử
```bash
cd basic
pip install -r requirements.txt
python app.py
# Truy cập: http://localhost:8000
```

### Những vấn đề trong code này:
1. API key hardcode trong code
2. Không có health check endpoint
3. Debug mode bật cứng
4. Không xử lý SIGTERM gracefully
5. Config không đến từ environment

---

## Ví dụ Advanced — 12-Factor Compliant Agent

```
production/
├── app.py          # ✅ Clean: config from env, health check, graceful shutdown
├── config.py       # ✅ Centralized config management
├── .env.example    # ✅ Template — không commit .env thật
└── requirements.txt
```

### Chạy thử
```bash
cd advanced
pip install -r requirements.txt
cp .env.example .env
# Sửa .env nếu cần
python app.py
```

### So sánh với Basic:

| | Basic (❌) | Advanced (✅) |
|--|-----------|--------------|
| Config | Hardcode trong code | Đọc từ env vars |
| Secrets | `api_key = "sk-abc123"` | `os.getenv("OPENAI_API_KEY")` |
| Port | Cố định `8000` | Từ `PORT` env var |
| Health check | Không có | `GET /health` |
| Shutdown | Tắt đột ngột | Graceful — hoàn thành request hiện tại |
| Logging | `print()` | Structured JSON logging |

---

## Câu hỏi thảo luận

1. Điều gì xảy ra nếu bạn push code với API key hardcode lên GitHub public?
2. Tại sao stateless quan trọng khi scale?
3. 12-factor nói "dev/prod parity" — nghĩa là gì trong thực tế?

---

## Câu hỏi thảo luận

1.  **Điều gì xảy ra nếu bạn push code với API key hardcode lên GitHub public?**
    Nếu bạn push code chứa API key hardcode lên GitHub public, API key đó sẽ bị lộ ngay lập tức. Điều này dẫn đến các rủi ro bảo mật nghiêm trọng như: truy cập trái phép vào các dịch vụ mà key đó bảo vệ, lạm dụng dịch vụ (ví dụ: gọi API OpenAI đến khi hết tiền), và có thể dẫn đến việc tài khoản của bạn bị khóa hoặc bị đánh cắp.

2.  **Tại sao stateless quan trọng khi scale?**
    Thiết kế stateless là cực kỳ quan trọng khi scale ứng dụng vì nó đảm bảo rằng không có trạng thái nào của người dùng hoặc phiên làm việc được lưu trữ trong bộ nhớ của từng instance ứng dụng. Khi ứng dụng được scale lên nhiều instance, nếu trạng thái được lưu cục bộ, mỗi instance sẽ có trạng thái riêng biệt. Điều này có nghĩa là nếu một yêu cầu từ người dùng được chuyển đến một instance khác với instance đã xử lý yêu cầu trước đó, trạng thái sẽ bị mất, dẫn đến trải nghiệm người dùng không nhất quán hoặc lỗi. Với thiết kế stateless, tất cả trạng thái cần thiết được lưu trữ ở một dịch vụ bên ngoài (ví dụ: Redis, cơ sở dữ liệu) mà tất cả các instance đều có thể truy cập, cho phép ứng dụng mở rộng quy mô liền mạch và chịu lỗi tốt hơn.

3.  **12-factor nói "dev/prod parity" — nghĩa là gì trong thực tế?**
    "Dev/prod parity" (ngang bằng giữa môi trường phát triển và sản xuất) là một nguyên tắc trong 12-Factor App, có nghĩa là giữ cho môi trường phát triển, thử nghiệm và sản xuất càng giống nhau càng tốt. Trong thực tế, điều này bao gồm việc sử dụng cùng một hệ điều hành, cùng phiên bản ngôn ngữ lập trình (ví dụ: Python 3.11), cùng các thư viện và dependencies, và cùng các dịch vụ hỗ trợ (backing services) như cơ sở dữ liệu (ví dụ: PostgreSQL), hệ thống hàng đợi (ví dụ: Redis) trên tất cả các môi trường. Mục tiêu là để giảm thiểu sự khác biệt giữa các môi trường, từ đó giảm thiểu các lỗi "nó chạy trên máy của tôi" và đảm bảo rằng những gì hoạt động trong môi trường phát triển cũng sẽ hoạt động trong môi trường sản xuất, giúp quá trình triển khai mượt mà hơn và đáng tin cậy hơn.

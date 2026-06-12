# Section 3 — Cloud Deployment Options

## 3 Tier: Chọn Platform Theo Nhu Cầu

| Tier | Platform | Khi nào dùng | Thời gian deploy |
|------|----------|-------------|-----------------|
| 1 | Railway, Render | MVP, demo, học | < 10 phút |
| 2 | AWS ECS, Cloud Run | Production | 15–30 phút |
| 3 | Kubernetes | Enterprise, large-scale | Vài giờ setup |

---

## railway/ — Deploy < 5 Phút

Không cần server config. Kết nối GitHub → Auto deploy.

```
railway/
├── railway.toml        # Railway config
├── Procfile            # Define start command
├── app.py              # Agent (Railway-ready)
└── requirements.txt
```

### Các bước deploy Railway:
1. `railway login` (hoặc qua browser)
2. `railway init`
3. `railway up`
4. Nhận URL dạng `https://your-app.up.railway.app`

---

## render/ — render.yaml (Infrastructure as Code)

Định nghĩa toàn bộ infrastructure trong 1 YAML file.

```
render/
├── render.yaml         # Khai báo service, env vars, disk
└── app.py
```

---

## production-cloud-run/ — GCP Cloud Run + CI/CD

Production-grade. Tự động build và deploy khi push code.

```
production-cloud-run/
├── cloudbuild.yaml     # CI/CD pipeline
├── service.yaml        # Cloud Run service definition
└── README.md           # Hướng dẫn chi tiết
```

---

## Câu hỏi thảo luận

1. Tại sao serverless (Lambda) không phải lúc nào cũng tốt cho AI agent?
Mặc dù kiến trúc serverless truyền thống như AWS Lambda cực kỳ tối ưu cho các tác vụ sự kiện (event-driven) ngắn hạn, chúng lại bộc lộ nhiều điểm yếu khi chạy các AI agent:

Thời gian thực thi bị giới hạn (Timeouts): Các AI agent thường phải thực hiện nhiều bước suy luận (reasoning loops), gọi API đến các LLM, hoặc cào dữ liệu từ web. AWS Lambda giới hạn thời gian chạy tối đa là 15 phút (và API Gateway thường timeout sau 30 giây). Nếu agent mất nhiều thời gian xử lý, tiến trình sẽ bị ngắt giữa chừng.

Kích thước package lớn: Các ứng dụng AI thường đi kèm với các thư viện xử lý dữ liệu lớn (như Pandas) hoặc các framework Deep Learning phức tạp. Lambda có giới hạn nghiêm ngặt về dung lượng mã nguồn và bộ nhớ.

Khởi tạo tài nguyên nặng: Việc load các mô hình Transformer lớn, hoặc thiết lập pipeline cho các tác vụ như xử lý Vision-Language Models (VLM) tốn rất nhiều RAM và thời gian khởi tạo ban đầu, khiến bản chất "chạy xong rồi tắt" của Lambda trở nên kém hiệu quả về mặt hiệu năng.
2. "Cold start" là gì? Ảnh hưởng thế nào đến UX?
Định nghĩa:"Cold start" (Khởi động lạnh) xảy ra khi một dịch vụ serverless (hoặc container) tự động scale từ mức $0$ lên $1$ instance để xử lý một request mới đến. Hệ thống sẽ cần một khoảng thời gian trễ nhất định để cấp phát tài nguyên máy chủ, kéo (pull) container image, khởi động môi trường runtime và chạy mã nguồn của ứng dụng.Ảnh hưởng đến Trải nghiệm người dùng (UX):Với các ứng dụng AI, cold start là một vấn đề lớn. Việc khởi động một ứng dụng chứa các thư viện nặng hoặc nạp mô hình vào bộ nhớ có thể đẩy thời gian delay của request đầu tiên lên từ vài giây đến cả chục giây. Điều này khiến người dùng cảm thấy hệ thống bị treo, phản hồi chậm chạp và làm giảm độ mượt mà của ứng dụng.
3. Khi nào nên upgrade từ Railway lên Cloud Run?
Cần kiểm soát chi tiết về Concurrency và Auto-scaling: Khi hệ thống có lượng traffic lớn hoặc biến động mạnh, Cloud Run cho phép bạn tinh chỉnh chính xác cách ứng dụng chịu tải. Ví dụ, service.yaml giới hạn mỗi instance xử lý tối đa 80 requests đồng thời (containerConcurrency: 80) và scale tối đa lên 10 instances (maxScale: "10").

Tích hợp CI/CD tự động và Test: Khi dự án lớn lên, bạn cần một quy trình làm việc tự động và an toàn hơn. File cloudbuild.yaml cho thấy một pipeline hoàn chỉnh: từ việc chạy test (với pytest), build Docker image có sử dụng layer cache, push lên registry, cho đến deploy.

Yêu cầu bảo mật cấp doanh nghiệp (Enterprise Security): Thay vì khai báo environment variables trực tiếp trên Dashboard như Railway/Render, Cloud Run cho phép kết nối an toàn với Google Secret Manager. Như trong cấu hình của bạn, các khóa nhạy cảm như OPENAI_API_KEY được kéo trực tiếp từ Secret Manager thay vì hardcode

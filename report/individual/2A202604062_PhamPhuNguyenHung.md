# Báo cáo thực hành Day 3 — Segmentation

- Mã học viên theo lớp: 2A202604062
- Ngày / CVAT local: 11/11/2026, CVAT v2.74.1 chạy bằng Docker trên máy cá nhân (localhost:8080)
- Công cụ đã dùng:
  - **CVAT**: Brush, Polygon và chỉnh mask trực tiếp.
  - **Claude Code (AI)**: chạy script trong `cvat-seg-copilot/scripts/` để tạo nháp mask sơ bộ cho job 5–11 (hard và 6 checkpoint). Nháp gồm YOLO26l-seg cho vật đếm được (người, xe, đèn giao thông) và SegFormer-B2 Cityscapes cho vùng stuff (road, sidewalk, building, vegetation, sky, pole, traffic sign). Mask của vật được trừ khỏi stuff để hai bên không chồng nhau. Sau đó mình mở từng job trong CVAT để xem lại; phần lớn mask là mình tự sửa lại, xóa hoặc vẽ bổ sung chứ không giữ nguyên nháp của máy.
  - Claude Code cũng viết script tạo task, gán thứ tự lớp (z_order), xuất ZIP và kiểm cấu trúc.
  - Không dùng SAM 3 vì tài khoản chưa được duyệt quyền tải. Job 3 và 4 (easy, medium) mình cũng dùng gợi ý tự động trước, sau đó sửa tay trong CVAT.

Phần nháp do máy tạo ra, mình ghi rõ ở đây để coach đối chiếu với quy định về gợi ý tự động.

## 1. Bài đã nộp

| Task | File ZIP đúng tên | Hoàn thành mấy ảnh | Điểm tối đa (coach chấm sau) |
| --- | --- | ---: | ---: |
| easy_semantic | submissions/easy_semantic.zip | 3 / 3 | 20 |
| medium_instance | submissions/medium_instance.zip | 3 / 3 | 32 |
| hard_panoptic | submissions/hard_panoptic.zip | 2 / 2 | 30 |
| cp1_holes | submissions/cp1_holes.zip | 1 / 1 | 3 |
| cp2_slice | submissions/cp2_slice.zip | 1 / 1 | 3 |
| cp5_occlusion | submissions/cp5_occlusion.zip | 1 / 1 | 3 |
| cp3_thin | submissions/cp3_thin.zip | 1 / 1 | 3 |
| cp4_curb | submissions/cp4_curb.zip | 1 / 1 | 3 |
| cp6_coverage | submissions/cp6_coverage.zip | 1 / 1 | 3 |
| **Tổng tối đa** | | | **100** |

Semantic xuất Segmentation mask 1.1, instance và panoptic xuất COCO 1.0. Mình chạy `scripts/inspect_submissions.py` thì cả 9 file đều OK về cấu trúc. Đây mới là kiểm tra file hợp lệ, chưa phải độ chính xác; mình chưa có điểm tự đánh giá vì chưa có reference.

## 2. Một quyết định trước khi dùng gợi ý

Ở `medium_instance` mình dùng gợi ý tự động trước, rồi mở CVAT chỉnh sửa và xóa những mask không phù hợp. Object mình tự vẽ tay là `person 8` ở frame 0. Mình vẽ nó sau khi job đã có gợi ý, nên không phải object vẽ trước khi xem gợi ý.

- Ảnh, vị trí và object Medium tự vẽ: `medium_instance`, frame 0 (ảnh `000000181542.jpg`), object `person 8` (nguồn Manual trong danh sách Objects của CVAT). Đó là người phụ nữ mặc áo dài đỏ đang đi qua vạch kẻ đường, đứng giữa ảnh, xung quanh là các xe máy.
- Class và quy tắc tôi dùng để chọn biên: class `person`; chỉ vẽ phần người nhìn thấy, đi theo viền áo dài và tóc, không lấy phần xe máy ở sau hoặc bên cạnh.
- Sau khi có gợi ý: với các mask còn lại, mình duyệt từng cái, xóa mask sai class hoặc thừa và chỉnh biên bằng Brush/Polygon.

Nếu quy định bắt buộc tự vẽ object đầu tiên ở đúng task Medium thì mình xin coach cho biết cách xử lý bài này.

## 3. Một lỗi tôi tìm thấy và sửa

- Task/ảnh/vùng: cp1_holes, ảnh xe moto Honda, vật phía sau xe là cái caravan (rơ-moóc cắm trại).
- Lỗi thuộc loại: sai lớp.
- Bằng chứng tôi nhìn thấy: nháp gán caravan là `truck`. Nhìn ảnh thì đó là rơ-moóc cắm trại có cửa sổ, logo, không phải xe tải. Mask của nó cũng là một khối vuông, không bám theo đường viền thật.
- Quy tắc và hành động sửa: class phải theo vật thật, không theo hình dạng chung. Mask `truck` này không hợp lý vì AI hiển thị sai, nên mình xóa nó trong job 6; giờ job không còn mask `truck` nào.
- Sau sửa đã Save và export lại chưa? Rồi, `cp1_holes.zip` được export sau khi sửa.

Mình chưa xem điểm tự đánh giá trên GitHub Actions nên không có số liệu trước/sau.

## 4. Ba ca chưa chắc hoặc đã cân nhắc

| Ảnh/vị trí | Hai cách hiểu có thể | Quy tắc/chứng cứ | Quyết định hoặc câu hỏi cho coach |
| --- | --- | --- | --- |
| cp6_coverage, khe sáng nhỏ phía trên giữa các toà nhà (khoảng 50×80 px) | Là một mảng `sky` nhỏ, hoặc chỉ là mặt kính phản sáng | Màu trắng gần giống mặt toà nhà; phiếu quy tắc nói không ép đoán cho đủ coverage | Mình không vẽ `sky`. Hỏi coach: vùng trời rất nhỏ có ngưỡng diện tích tối thiểu không? |
| cp6_coverage, xe buýt số 2555 và xe tải CAPITAL | Gán cả hai là `car`, hoặc để trống | Class của task chỉ có `car` và `person`, không có `bus`/`truck` | Hai xe này không có nhãn tương ứng trong danh sách class của cp6 nên mình không gán, để trống. Chỉ gán `car` cho xe con. |
| cp4_curb, mảng tối ở giữa bên phải ảnh | Là vỉa hè tối màu, hoặc là đoạn hạ bó vỉa ở lối vào nhà (thuộc `road`) | Phiếu ghi ranh road–sidewalk xác định theo chức năng và bó vỉa, không theo màu | Mình chỉnh tay mảng này trong CVAT và gán là `sidewalk`. Hỏi coach: đoạn hạ bó vỉa ở lối vào nhà thì tính là `road` hay `sidewalk`? |

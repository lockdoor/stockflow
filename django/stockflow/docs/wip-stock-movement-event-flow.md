# WIPStockMovement Event Flow

```mermaid
flowchart TD
    WI[IN: รับวัสดุเข้า WIP] --> WO[OUT: ใช้วัสดุใน process]
    WO --> WR[RETURN: คืนวัสดุจาก WIP]
    WO --> WL[LOSS: สูญเสียวัสดุใน WIP]
    WI -.-> WA[ADJUST: ปรับยอด WIP]

    classDef in fill:#e8eaf6,stroke:#3949ab,stroke-width:2px;
    classDef out fill:#f3e5f5,stroke:#8e24aa,stroke-width:2px;
    classDef return fill:#e0f2f1,stroke:#00897b,stroke-width:2px;
    classDef loss fill:#ffebee,stroke:#b71c1c,stroke-width:2px,stroke-dasharray: 3 2;
    classDef adjust fill:#fffde7,stroke:#fbc02d,stroke-width:2px;

    WI:::in
    WO:::out
    WR:::return
    WL:::loss
    WA:::adjust
```

---
**WIPStockMovement Event Flow:**
- **IN**: รับวัสดุเข้า WIP (จาก stock จริง)
- **OUT**: ใช้วัสดุใน process (ตัดออกจาก WIP)
- **RETURN**: คืนวัสดุจาก WIP กลับคลังจริง
- **LOSS**: สูญเสียวัสดุใน WIP
- **ADJUST**: ปรับยอด WIP (เช่น audit, correction)

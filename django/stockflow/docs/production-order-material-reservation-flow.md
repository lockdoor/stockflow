# Production Order Material Reservation Flow


```mermaid
flowchart TD
    A[Draft] -->|Submit| B[Created]
    B -->|Start Production| C[In Progress]
    C -->|Pause| D[Paused]
    D -->|Resume| C
    C -->|Complete| E[Completed]
    B -->|Cancel| F[Cancelled]
    C -->|Cancel| F
    D -->|Cancel| F

    %% Reservation/Consumption logic
    B -.->|Reserve material by BOM| R[Material Reservation]
    C -.->|Consume material within reservation| S[Stock Movement]
    C -.->|Consume more than reserved| S2[Stock Movement Over Reservation]
    E -.->|Release unused reservation| X[Release Reservation]
    F -.->|Release all reservation| X

    %% WIP/Warehouse movement logic
    S -.->|Transfer material to WIP warehouse| W[WIP Stock Movement]
    W -.->|Consume from WIP in process| P[Production Process Consumption]
    P -.->|Return unused material from WIP| RW[Return to Warehouse]
    P -.->|Loss in process| L[Production Loss]
    P -.->|Output finished goods| FG[Finished Goods Stock In]

    %% Notes
    B:::reserve
    C:::consume
    S2:::overconsume
    E:::release
    F:::release
    W:::wip
    P:::process
    RW:::return
    L:::loss
    FG:::fgin

    classDef reserve fill:#e0f7fa,stroke:#00796b,stroke-width:2px;
    classDef consume fill:#fff3e0,stroke:#f57c00,stroke-width:2px;
    classDef overconsume fill:#ffebee,stroke:#d32f2f,stroke-width:2px,stroke-dasharray: 5 2;
    classDef release fill:#fce4ec,stroke:#c2185b,stroke-width:2px;
    classDef wip fill:#e8eaf6,stroke:#3949ab,stroke-width:2px;
    classDef process fill:#f3e5f5,stroke:#8e24aa,stroke-width:2px;
    classDef return fill:#e0f2f1,stroke:#00897b,stroke-width:2px;
    classDef loss fill:#ffebee,stroke:#b71c1c,stroke-width:2px,stroke-dasharray: 3 2;
    classDef fgin fill:#f1f8e9,stroke:#558b2f,stroke-width:2px;
```

> หมายเหตุ:
> - Created: จองวัสดุตาม BOM
> - In Progress: เบิกวัสดุจริง (เบิกเท่าไหร่ก็ได้)
> - หากเบิกเกินที่จอง จะลด stock จริงโดยตรง (Stock Movement (Over Reservation))
> - Completed/Cancelled: คืนวัสดุที่จองไว้ (ถ้ามี)

---
**WIP/Production Process Flow เพิ่มเติม:**
- In Progress: วัสดุที่เบิกจะถูกโอนเข้า WIP warehouse เฉพาะของ production order/process
- ในแต่ละ production process จะตัด stock ออกจาก WIP warehouse ตามการใช้จริง
- หากมีวัสดุเหลือใน WIP เมื่อ production เสร็จหรือยกเลิก สามารถคืนเข้าคลังจริงได้
- ผลผลิตที่ได้จะถูกโอนเข้าคลังปลายทาง (Finished Goods)
- กรณีสูญเสียวัสดุใน process ให้บันทึกเป็น Production Loss

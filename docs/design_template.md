# Design Template

## Problem

Hệ thống cần xử lý research query bằng cách tìm kiếm thông tin, phân tích và viết câu trả lời cuối cùng. Yêu cầu so sánh single-agent vs multi-agent workflow.

## Why multi-agent?

Single-agent chưa đủ vì:
1. **Separation of concerns**: một agent làm tất cả (search + analyze + write) dẫn đến prompt quá dài và quality không đồng đều
2. **Routing flexibility**: multi-agent cho phép supervisor quyết định flow dựa trên state hiện tại
3. **Debugging**: trace từng agent riêng biệt dễ debug hơn
4. **Parallelism tiềm năng**: researcher và analyst có thể chạy song song nếu cần

## Agent roles

| Agent | Responsibility | Input | Output | Failure mode |
|---|---|---|---|---|
| Supervisor | Điều phối flow, quyết định agent tiếp theo | ResearchState (kiểm tra các field đã có chưa) | Cập nhật route_history | Fallback về done nếu max_iterations |
| Researcher | Tìm kiếm sources, viết research notes | request.query | sources + research_notes | Dùng fallback search source |
| Analyst | Phân tích sâu, extract key claims | research_notes + sources | analysis_notes | Ghi nhận lỗi, tiếp tục |
| Writer | Viết final answer từ research + analysis | research_notes + analysis_notes + sources | final_answer | Trả lời ngắn gọn nếu thiếu input |
| Critic (optional) | Fact-check và critique | final_answer + research_notes + sources | Critique in agent_results | Ghi nhận lỗi |

## Shared state

| Field | Type | Lý do cần |
|---|---|---|
| request | ResearchQuery | Query gốc từ user |
| iteration | int | Đếm số bước để enforce max_iterations |
| route_history | list[str] | Debug và trace flow |
| sources | list[SourceDocument] | Lưu search results |
| research_notes | str | Output của Researcher |
| analysis_notes | str | Output của Analyst |
| final_answer | str | Output của Writer |
| agent_results | list[AgentResult] | Chi tiết từng agent call |
| trace | list[dict] | Trace events cho debugging |
| errors | list[str] | Lưu các lỗi gặp phải |

## Routing policy

```
                    ┌──────────────────────┐
                    │       START         │
                    │   (supervisor)      │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  has research_notes?│
                    └──────────┬──────────┘
                       No     │     Yes
              ┌───────────────▼───────────────┐
              │      researcher              │
              └───────────────┬───────────────┘
                              │
              ┌───────────────▼───────────────┐
              │  has analysis_notes?         │
              └───────────────┬───────────────┘
                 No           │     Yes
        ┌───────────────▼───────────────┐
        │        analyst               │
        └───────────────┬───────────────┘
                        │
              ┌─────────▼─────────┐
              │ has final_answer? │
              └─────────┬─────────┘
                 No     │     Yes
        ┌────────▼────────┐
        │     writer      │
        └────────┬────────┘
                 │
           ┌─────▼─────┐
           │    END     │
           └───────────┘
```

Supervisor quyết định route dựa trên state:
- `research_notes == None` → researcher
- `research_notes` tồn tại nhưng `analysis_notes == None` → analyst
- `analysis_notes` tồn tại nhưng `final_answer == None` → writer
- `final_answer` đã có → done

## Guardrails

- **Max iterations**: 6 (config: `MAX_ITERATIONS`)
- **Timeout**: 60s cho mỗi LLM call
- **Retry**: 3 retries với exponential backoff (2s → 4s → 8s)
- **Fallback**:
  - Tavily API fail → DuckDuckGo HTML scrape
  - Search fail → Placeholder source
- **Validation**: ResearchState Pydantic model validation

## Benchmark plan

| Query | Metric | Expected outcome |
|---|---|---|
| "What is GraphRAG" | Latency | Multi-agent < 15s |
| "What is GraphRAG" | Quality | Multi-agent > Baseline |
| "What is GraphRAG" | Cost | Baseline < Multi-agent |
| "What is GraphRAG" | Citation coverage | Multi-agent ≥ 0.5 |

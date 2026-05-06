# Lab Guide: Multi-Agent Research System

## Scenario

Bạn cần xây dựng một research assistant có thể nhận câu hỏi dài, tìm thông tin, phân tích và viết câu trả lời cuối cùng. Lab yêu cầu so sánh hai cách làm:

1. **Single-agent baseline**: một agent làm toàn bộ.
2. **Multi-agent workflow**: Supervisor điều phối Researcher, Analyst, Writer.

## Quy tắc quan trọng

- Không thêm agent nếu không có lý do rõ ràng.
- Mỗi agent phải có responsibility riêng.
- Shared state phải đủ rõ để debug.
- Phải có trace hoặc log cho từng bước.
- Phải benchmark, không chỉ nhìn output bằng cảm tính.

## Milestone 1: Baseline

File gợi ý:
- `src/multi_agent_research_lab/cli.py`
- `src/multi_agent_research_lab/services/llm_client.py`

Đã implement LLMClient với OpenAI API, retry và token logging.

## Milestone 2: Supervisor

File gợi ý:
- `src/multi_agent_research_lab/agents/supervisor.py`
- `src/multi_agent_research_lab/graph/workflow.py`

Đã implement routing policy với các câu hỏi thiết kế đã trả lời:

- **Khi nào gọi Researcher?** Khi `research_notes == None`
- **Khi nào gọi Analyst?** Khi có `research_notes` nhưng chưa có `analysis_notes`
- **Khi nào gọi Writer?** Khi có `analysis_notes` nhưng chưa có `final_answer`
- **Khi nào stop?** Khi `final_answer` đã có hoặc `iteration >= max_iterations`
- **Nếu agent fail thì retry hay fallback?** Retry 3 lần với exponential backoff, fallback sang search source khác

## Milestone 3: Worker agents

File gợi ý:
- `agents/researcher.py`
- `agents/analyst.py`
- `agents/writer.py`

Đã implement đầy đủ:
- **Researcher**: search + research notes
- **Analyst**: extract key claims, compare viewpoints, flag weak evidence
- **Writer**: synthesize response với citations

## Milestone 4: Trace và benchmark

File gợi ý:
- `observability/tracing.py`
- `evaluation/benchmark.py`
- `evaluation/report.py`

Benchmark tối thiểu đã implement:

| Metric | Cách đo |
|---|---|
| Latency | wall-clock time |
| Cost | token usage từ OpenAI API |
| Quality | rubric 0-10 (content completeness) |
| Citation coverage | số claims có source / tổng claims chính |
| Failure rate | số query fail / tổng query |

## Exit ticket

Mỗi nhóm trả lời 2 câu:

1. **Case nào nên dùng multi-agent? Vì sao?**
   - Khi cần separation of concerns rõ ràng
   - Khi cần routing linh hoạt theo state
   - Khi cần debug từng bước riêng biệt
   - Khi muốn scale từng agent độc lập

2. **Case nào không nên dùng multi-agent? Vì sao?**
   - Khi task đơn giản, một agent làm đủ
   - Khi latency quan trọng hơn quality (multi-agent có overhead)
   - Khi chi phí API quan trọng hơn (multi-agent dùng nhiều LLM calls hơn)

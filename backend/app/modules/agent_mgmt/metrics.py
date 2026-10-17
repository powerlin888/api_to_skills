from sqlalchemy.ext.asyncio import AsyncSession
from app.shared.dao.dao import AgentDAO


class MetricsCollector:
    def __init__(self, db: AsyncSession):
        self.dao = AgentDAO(db)

    async def collect(self, agent_id: str, run_response, session_id: str | None = None) -> dict | None:
        if not run_response or not hasattr(run_response, 'metrics') or not run_response.metrics:
            return None
        m = run_response.metrics
        data = {
            "model_calls": getattr(m, 'model_calls', 0) or 0,
            "input_tokens": getattr(m, 'input_tokens', 0) or 0,
            "output_tokens": getattr(m, 'output_tokens', 0) or 0,
            "tool_calls": getattr(m, 'tool_calls', 0) or 0,
            "latency_ms": int(getattr(m, 'latency_ms', 0) or 0),
            "cost": float(getattr(m, 'cost', 0) or 0.0),
        }
        metric = await self.dao.add_metric(agent_id=agent_id, session_id=session_id, **data)
        return {"id": metric.id, **data}

    async def get_session_metrics(self, agent_id: str, session_id: str) -> list[dict]:
        from sqlalchemy import select
        from app.shared.dao.models import AgentMetric
        result = await self.dao.db.execute(
            select(AgentMetric).where(
                AgentMetric.agent_id == agent_id,
                AgentMetric.session_id == session_id
            )
        )
        metrics = list(result.scalars().all())
        return [{"model_calls": m.model_calls, "input_tokens": m.input_tokens,
                 "output_tokens": m.output_tokens, "tool_calls": m.tool_calls,
                 "latency_ms": m.latency_ms, "cost": m.cost} for m in metrics]

"""loadtest.py：50 并发提交 SD1.5 快工作流，采集 p50/p95（规格书 §8）。

采集三项分布：提交ACK / enqueued→started（队列等待）/ started→finished（生成耗时）。

用法：python scripts/loadtest.py [并发数] [工作流id]
"""

import concurrent.futures
import json
import statistics
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime

BASE = "http://127.0.0.1:8000"


def req(method: str, path: str, token: str | None = None, body: dict | None = None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(f"{BASE}{path}", data=data, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(r, timeout=30)
        return resp.status, json.loads(resp.read()) if resp.status != 204 else None
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def _parse(ts: str | None) -> float | None:
    if not ts:
        return None
    return datetime.fromisoformat(ts).timestamp()


def _p50(xs: list[float]) -> float:
    return statistics.median(xs)


def _p95(xs: list[float]) -> float:
    return sorted(xs)[int(len(xs) * 0.95) - 1]


def main() -> None:
    concurrency = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    wf_id = int(sys.argv[2]) if len(sys.argv) > 2 else 3

    # 1. 登录
    _, login = req("POST", "/api/auth/login", body={"email": "canliu", "password": "gch17728501545"})
    token = login["access_token"]
    print(f"登录成功，准备并发 {concurrency} 提交工作流 {wf_id}")

    # 2. 并发提交，记录 ACK 耗时 + task_id
    ack_times: list[float] = []
    task_ids: list[int] = []

    def _submit(i: int):
        t0 = time.time()
        code, resp = req(
            "POST", "/api/tasks", token=token,
            body={"workflow_id": wf_id, "params": {"prompt": f"loadtest image {i}"}},
        )
        dt = time.time() - t0
        return code, dt, resp

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as pool:
        results = list(pool.map(_submit, range(concurrency)))

    for code, dt, resp in results:
        ack_times.append(dt)
        if code == 202:
            task_ids.append(resp["id"])
    print(f"提交完成：{len(task_ids)}/{concurrency} 成功")

    # 3. 轮询直到全部终态
    tasks = {}
    deadline = time.time() + 600
    while time.time() < deadline:
        _, lst = req("GET", "/api/tasks?limit=100", token=token)
        for t in lst:
            if t["id"] in task_ids:
                tasks[t["id"]] = t
        if len(tasks) >= len(task_ids) and all(
            t["status"] in ("success", "failed", "cancelled") for t in tasks.values()
        ):
            break
        time.sleep(2)

    # 4. 采集 enqueued→started / started→finished
    queue_waits, gen_times = [], []
    for tid in task_ids:
        t = tasks.get(tid, {})
        enq, st, fin = _parse(t.get("enqueued_at")), _parse(t.get("started_at")), _parse(t.get("finished_at"))
        if enq and st:
            queue_waits.append(st - enq)
        if st and fin:
            gen_times.append(fin - st)

    # 5. 输出
    print("\n| 指标 | p50 | p95 | 均值 |")
    print("|---|---|---|---|")
    for name, xs in [("提交ACK (s)", ack_times), ("队列等待 enqueued→started (s)", queue_waits), ("生成耗时 started→finished (s)", gen_times)]:
        if xs:
            print(f"| {name} | {_p50(xs):.2f} | {_p95(xs):.2f} | {statistics.mean(xs):.2f} |")


if __name__ == "__main__":
    main()

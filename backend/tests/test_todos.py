from datetime import datetime, timedelta, timezone

import pytest

TODAY = datetime.now(timezone.utc).date()  # same clock as the API
YESTERDAY = (TODAY - timedelta(days=1)).isoformat()
NEXT_WEEK = (TODAY + timedelta(days=7)).isoformat()


def test_todo_crud_lifecycle(client):
    # Create
    create = client.post(
        "/api/todos",
        json={
            "title": "Set up CI pipeline",
            "description": "GitHub Actions with pytest and Trivy",
            "priority": "HIGH",
            "category": "DevOps",
            "due_date": NEXT_WEEK,
        },
    )
    assert create.status_code == 201
    todo = create.json()
    assert todo["title"] == "Set up CI pipeline"
    assert todo["completed"] is False
    assert todo["completed_at"] is None
    assert todo["priority"] == "HIGH"
    assert todo["due_date"] == NEXT_WEEK

    # Read
    read = client.get(f"/api/todos/{todo['id']}")
    assert read.status_code == 200
    assert read.json()["id"] == todo["id"]

    # Update
    update = client.put(f"/api/todos/{todo['id']}", json={"title": "Set up CD pipeline"})
    assert update.status_code == 200
    assert update.json()["title"] == "Set up CD pipeline"
    assert update.json()["category"] == "DevOps"  # untouched fields are kept

    # Delete
    assert client.delete(f"/api/todos/{todo['id']}").status_code == 204
    assert client.get(f"/api/todos/{todo['id']}").status_code == 404


def test_create_uses_defaults(make_todo):
    todo = make_todo(title="Buy milk")
    assert todo["priority"] == "MEDIUM"
    assert todo["category"] == "General"
    assert todo["description"] is None
    assert todo["due_date"] is None


def test_create_strips_whitespace(make_todo):
    todo = make_todo(title="  Plan sprint  ", category="  Work ")
    assert todo["title"] == "Plan sprint"
    assert todo["category"] == "Work"


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"title": ""},
        {"title": "   "},
        {"title": "x" * 201},
        {"title": "ok", "priority": "URGENT"},
        {"title": "ok", "due_date": "not-a-date"},
    ],
)
def test_create_rejects_invalid_payloads(client, payload):
    assert client.post("/api/todos", json=payload).status_code == 422


def test_missing_todo_returns_404(client):
    assert client.get("/api/todos/99999").status_code == 404
    assert client.put("/api/todos/99999", json={"title": "x"}).status_code == 404
    assert client.patch("/api/todos/99999/toggle").status_code == 404
    assert client.delete("/api/todos/99999").status_code == 404


def test_toggle_sets_and_clears_completed_at(client, make_todo):
    todo = make_todo()

    done = client.patch(f"/api/todos/{todo['id']}/toggle").json()
    assert done["completed"] is True
    assert done["completed_at"] is not None

    undone = client.patch(f"/api/todos/{todo['id']}/toggle").json()
    assert undone["completed"] is False
    assert undone["completed_at"] is None


def test_update_completed_flag(client, make_todo):
    todo = make_todo()
    response = client.put(f"/api/todos/{todo['id']}", json={"completed": True})
    assert response.json()["completed"] is True
    assert response.json()["completed_at"] is not None


def test_update_can_clear_optional_fields(client, make_todo):
    todo = make_todo(description="temp", due_date=NEXT_WEEK)
    response = client.put(
        f"/api/todos/{todo['id']}", json={"description": None, "due_date": None}
    )
    assert response.status_code == 200
    assert response.json()["description"] is None
    assert response.json()["due_date"] is None


def test_update_rejects_null_required_fields(client, make_todo):
    todo = make_todo()
    assert client.put(f"/api/todos/{todo['id']}", json={"title": None}).status_code == 422
    assert client.put(f"/api/todos/{todo['id']}", json={"completed": None}).status_code == 422


def test_list_filters_by_status(client, make_todo):
    active = make_todo(title="Active task")
    done = make_todo(title="Done task")
    client.patch(f"/api/todos/{done['id']}/toggle")

    def ids(query):
        return {t["id"] for t in client.get(f"/api/todos?{query}").json()}

    assert ids("status=all") == {active["id"], done["id"]}
    assert ids("status=active") == {active["id"]}
    assert ids("status=completed") == {done["id"]}


def test_list_filters_overdue_and_today(client, make_todo):
    overdue = make_todo(title="Late", due_date=YESTERDAY)
    today = make_todo(title="Today", due_date=TODAY.isoformat())
    make_todo(title="Later", due_date=NEXT_WEEK)
    late_but_done = make_todo(title="Late but done", due_date=YESTERDAY)
    client.patch(f"/api/todos/{late_but_done['id']}/toggle")

    overdue_ids = {t["id"] for t in client.get("/api/todos?status=overdue").json()}
    assert overdue_ids == {overdue["id"]}
    today_ids = {t["id"] for t in client.get("/api/todos?status=today").json()}
    assert today_ids == {today["id"]}


def test_list_filters_by_priority_category_and_search(client, make_todo):
    target = make_todo(title="Deploy with Helm", priority="HIGH", category="DevOps")
    make_todo(title="Deploy docs", priority="LOW", category="Docs")
    make_todo(title="Groceries", description="helm of lettuce", category="Home")

    assert [t["id"] for t in client.get("/api/todos?priority=HIGH").json()] == [target["id"]]
    assert [t["id"] for t in client.get("/api/todos?category=DevOps").json()] == [target["id"]]

    search = {t["title"] for t in client.get("/api/todos?search=HELM").json()}
    assert search == {"Deploy with Helm", "Groceries"}  # case-insensitive, title + description


def test_list_sorting(client, make_todo):
    make_todo(title="b-low", priority="LOW", due_date=NEXT_WEEK)
    make_todo(title="a-high", priority="HIGH")
    make_todo(title="c-medium", priority="MEDIUM", due_date=YESTERDAY)

    def titles(sort):
        return [t["title"] for t in client.get(f"/api/todos?sort={sort}").json()]

    assert titles("created") == ["c-medium", "a-high", "b-low"]
    assert titles("priority") == ["a-high", "c-medium", "b-low"]
    assert titles("title") == ["a-high", "b-low", "c-medium"]
    assert titles("due_date") == ["c-medium", "b-low", "a-high"]


def test_list_rejects_unknown_filter_values(client):
    assert client.get("/api/todos?status=archived").status_code == 422
    assert client.get("/api/todos?sort=random").status_code == 422


def test_stats(client, make_todo):
    make_todo(title="one", priority="HIGH", category="Work", due_date=YESTERDAY)
    make_todo(title="two", priority="HIGH", category="Work", due_date=TODAY.isoformat())
    three = make_todo(title="three", priority="LOW", category="Home")
    make_todo(title="four", priority="MEDIUM", category="Home")
    client.patch(f"/api/todos/{three['id']}/toggle")

    stats = client.get("/api/todos/stats").json()
    assert stats["total"] == 4
    assert stats["completed"] == 1
    assert stats["active"] == 3
    assert stats["overdue"] == 1
    assert stats["due_today"] == 1
    assert stats["completion_rate"] == 25.0
    assert stats["by_priority"] == {"LOW": 0, "MEDIUM": 1, "HIGH": 2}  # active todos only
    assert stats["by_category"] == {"Home": 2, "Work": 2}


def test_stats_when_empty(client):
    stats = client.get("/api/todos/stats").json()
    assert stats["total"] == 0
    assert stats["completion_rate"] == 0.0


def test_clear_completed(client, make_todo):
    keep = make_todo(title="keep")
    for title in ("done 1", "done 2"):
        todo = make_todo(title=title)
        client.patch(f"/api/todos/{todo['id']}/toggle")

    response = client.delete("/api/todos/completed")
    assert response.status_code == 200
    assert response.json() == {"deleted": 2}
    assert [t["id"] for t in client.get("/api/todos").json()] == [keep["id"]]

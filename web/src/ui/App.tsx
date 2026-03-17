import { useEffect, useMemo, useState } from "react";
import { api, BetWithMatch, Match, MatchStatus, Me } from "../lib/api";
import { tgReady } from "../lib/telegram";

type Tab = "matches" | "mybets" | "me";

export function App() {
  const [tab, setTab] = useState<Tab>("matches");
  const [me, setMe] = useState<Me | null>(null);
  const [matches, setMatches] = useState<Match[] | null>(null);
  const [myBets, setMyBets] = useState<BetWithMatch[] | null>(null);
  const [statusFilter, setStatusFilter] = useState<MatchStatus | "all">("live");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const filteredMatches = useMemo(() => {
    if (!matches) return null;
    if (statusFilter === "all") return matches;
    return matches.filter((m) => m.status === statusFilter);
  }, [matches, statusFilter]);

  async function loadAll() {
    setLoading(true);
    setError(null);
    try {
      tgReady();
      const [meRes, matchesRes] = await Promise.all([api.me(), api.matches()]);
      setMe(meRes);
      setMatches(matchesRes);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function loadMyBets() {
    setLoading(true);
    setError(null);
    try {
      const res = await api.myBets();
      setMyBets(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  async function placeQuickBet(match: Match, team: string) {
    const amountStr = prompt("Сумма ставки");
    if (!amountStr) return;
    const amount = Number(amountStr);
    if (!Number.isFinite(amount) || amount <= 0) {
      alert("Неверная сумма");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await api.placeBet({ match_id: match.id, team, amount });
      await loadAll();
      alert("Ставка принята");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="container">
      <header className="header">
        <div className="title">PPL Bets</div>
        <div className="subtitle">
          {me ? (
            <>
              Баланс: <b>{me.balance.toFixed(2)}</b>
            </>
          ) : (
            "..."
          )}
        </div>
      </header>

      <nav className="tabs">
        <button className={tab === "matches" ? "tab active" : "tab"} onClick={() => setTab("matches")}>
          Матчи
        </button>
        <button
          className={tab === "mybets" ? "tab active" : "tab"}
          onClick={() => {
            setTab("mybets");
            void loadMyBets();
          }}
        >
          Мои ставки
        </button>
        <button className={tab === "me" ? "tab active" : "tab"} onClick={() => setTab("me")}>
          Профиль
        </button>
      </nav>

      {error ? <div className="error">{error}</div> : null}
      {loading ? <div className="loading">Загрузка...</div> : null}

      {tab === "matches" ? (
        <section className="card">
          <div className="row">
            <div className="label">Фильтр</div>
            <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value as any)}>
              <option value="all">Все</option>
              <option value="scheduled">Scheduled</option>
              <option value="live">Live</option>
              <option value="finished">Finished</option>
            </select>
            <button className="btn" onClick={() => void loadAll()}>
              Обновить
            </button>
          </div>

          {filteredMatches?.length ? (
            <div className="list">
              {filteredMatches.map((m) => (
                <div key={m.id} className="match">
                  <div className="matchTop">
                    <div className="matchTeams">
                      <b>
                        #{m.id} {m.team1} vs {m.team2}
                      </b>
                      <div className="muted">
                        {new Date(m.start_time).toLocaleString()} · статус: {m.status}
                      </div>
                    </div>
                  </div>
                  <div className="betRow">
                    <button className="betBtn" disabled={m.status !== "live"} onClick={() => void placeQuickBet(m, m.team1)}>
                      {m.team1} · {m.coef_team1.toFixed(2)}
                    </button>
                    <button className="betBtn" disabled={m.status !== "live"} onClick={() => void placeQuickBet(m, m.team2)}>
                      {m.team2} · {m.coef_team2.toFixed(2)}
                    </button>
                  </div>
                  {m.winner ? <div className="winner">Победитель: {m.winner}</div> : null}
                </div>
              ))}
            </div>
          ) : (
            <div className="muted">Матчей нет.</div>
          )}
        </section>
      ) : null}

      {tab === "mybets" ? (
        <section className="card">
          {myBets?.length ? (
            <div className="list">
              {myBets.map((b) => (
                <div key={b.id} className="bet">
                  <div>
                    <b>
                      #{b.match_id} {b.match_team1} vs {b.match_team2}
                    </b>
                    <div className="muted">{new Date(b.match_start_time).toLocaleString()}</div>
                  </div>
                  <div className="betMeta">
                    <div>
                      Ставка: <b>{b.team}</b>
                    </div>
                    <div>
                      Сумма: <b>{b.amount}</b> · Коэф: <b>{b.coef.toFixed(2)}</b>
                    </div>
                    <div className="muted">
                      Статус: {b.match_status}
                      {b.match_winner ? ` · победитель: ${b.match_winner}` : ""}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="muted">Ставок нет.</div>
          )}
        </section>
      ) : null}

      {tab === "me" ? (
        <section className="card">
          <div className="row">
            <div className="label">ID</div>
            <div>{me?.id ?? "..."}</div>
          </div>
          <div className="row">
            <div className="label">Username</div>
            <div>{me?.username ?? "-"}</div>
          </div>
          <div className="row">
            <div className="label">Баланс</div>
            <div>{me ? me.balance.toFixed(2) : "..."}</div>
          </div>
          <button className="btn" onClick={() => void loadAll()}>
            Обновить
          </button>
        </section>
      ) : null}
    </div>
  );
}


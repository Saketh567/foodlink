import { useEffect, useState } from "react";
import api from "../api/axios";

export default function ClientDashboard() {
  const [data, setData] = useState(null);

  useEffect(() => {
    api.get("/client/dashboard").then(res => setData(res.data)).catch(console.error);
  }, []);

  if (!data) return <p>Loading…</p>;

  return (
    <div style={{ padding: 16 }}>
      <h2>Client Dashboard</h2>

      <section>
        <h3>Next Pickup Window</h3>
        <p>{data.pickup_window?.start} – {data.pickup_window?.end}</p>
      </section>

      <section>
        <h3>Your Profile</h3>
        <pre style={{ background:"#f7f7f7", padding:12 }}>
          {JSON.stringify(data.profile, null, 2)}
        </pre>
      </section>

      <section>
        <h3>Distribution History</h3>
        {data.history?.length ? (
          <ul>{data.history.map(h => (
            <li key={h.id}>{h.date_given} — {h.notes || ""}</li>
          ))}</ul>
        ) : <p>No distributions yet.</p>}
      </section>
    </div>
  );
}

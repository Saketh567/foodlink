import { useEffect, useState } from "react";
import api from "../api/axios";
import "../App.css"; 

export default function ClientPhotos() {
  const [photos, setPhotos] = useState([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  const refresh = () =>
    api.get("/client/photos")
      .then(r => setPhotos(Array.isArray(r.data) ? r.data : []))
      .catch(e => setErr(e?.message ?? "Failed to load"))
      .finally(() => setBusy(false));

  useEffect(() => { setBusy(true); refresh(); }, []);

  const onUpload = async (e) => {
    if (!e.target.files?.length) return;
    setBusy(true);
    const form = new FormData();
    [...e.target.files].forEach(f => form.append("photos", f));
    try {
      await api.post("/client/photos", form, { headers: { "Content-Type": "multipart/form-data" } });
      e.target.value = "";
      await refresh();
    } catch (ex) {
      setErr(ex?.message ?? "Upload failed");
      setBusy(false);
    }
  };

  return (
    <>
  
      <div className="container">
        <div className="card">
          <h1 className="h1">Family Photos</h1>

          <form className="profile-form" onSubmit={(e) => e.preventDefault()}>
            <div className="field">
              <label htmlFor="photos">Upload photos (JPG/PNG)</label>

              {/* hidden native input */}
              <input id="photos" className="file-input" type="file"
                     accept=".jpg,.jpeg,.png" multiple onChange={onUpload} />
              {/* styled trigger */}
              <label htmlFor="photos" className="file-btn">Choose Files</label>
              {busy && <span className="file-hint">Uploading / Loading…</span>}
              {err && <span className="file-hint" style={{color:"#b91c1c"}}>{err}</span>}
            </div>
          </form>

          <div className="gallery">
            {photos.length === 0 ? (
              <p className="muted">No photos yet.</p>
            ) : (
              photos.map(p => (
                <figure className="photo-card" key={p.id ?? p.url}>
                  <img src={p.url} alt="" />
                  <figcaption>{new Date(p.uploaded_at).toLocaleString()}</figcaption>
                </figure>
              ))
            )}
          </div>
        </div>
      </div>
    </>
  );
}


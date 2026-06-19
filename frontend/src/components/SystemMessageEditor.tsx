import { useState } from "react";

interface Props {
  systemMessage: string;
  onSave: (msg: string) => void;
}

export function SystemMessageEditor({ systemMessage, onSave }: Props) {
  const [open, setOpen] = useState(false);
  const [value, setValue] = useState(systemMessage);

  const handleSave = () => {
    onSave(value);
    setOpen(false);
  };

  return (
    <>
      <button
        onClick={() => setOpen(!open)}
        style={{ background: "none", border: "1px solid #555", color: "#aaa", borderRadius: 4, padding: "4px 8px", cursor: "pointer", fontSize: 12 }}
      >
        System Prompt
      </button>
      {open && (
        <div style={{
          position: "fixed", top: 0, left: 0, right: 0, bottom: 0,
          background: "rgba(0,0,0,0.6)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 100,
        }}>
          <div style={{ background: "#1a1a1a", padding: 20, borderRadius: 12, width: 500, maxWidth: "90vw" }}>
            <h3 style={{ color: "#eee", margin: "0 0 12px" }}>System Message</h3>
            <textarea
              value={value}
              onChange={(e) => setValue(e.target.value)}
              rows={6}
              style={{ width: "100%", padding: 8, borderRadius: 6, border: "1px solid #555", background: "#2d2d2d", color: "#eee", resize: "vertical" }}
            />
            <div style={{ display: "flex", gap: 8, justifyContent: "flex-end", marginTop: 12 }}>
              <button onClick={() => setOpen(false)} style={{ padding: "6px 12px", background: "#333", color: "#eee", border: "none", borderRadius: 6, cursor: "pointer" }}>Cancel</button>
              <button onClick={handleSave} style={{ padding: "6px 12px", background: "#2b5278", color: "#fff", border: "none", borderRadius: 6, cursor: "pointer" }}>Save</button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

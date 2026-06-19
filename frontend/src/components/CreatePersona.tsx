import { useState } from "react";

interface Props {
  onSave: (data: { name: string; avatar: string; title: string; system_message: string }) => void;
  onClose: () => void;
}

const s = {
  overlay: {
    position: "fixed" as const, top: 0, left: 0, right: 0, bottom: 0,
    background: "rgba(0,0,0,0.5)", display: "flex", alignItems: "flex-end" as const,
    justifyContent: "center", zIndex: 100,
  },
  sheet: {
    background: "#1c1c1e", borderRadius: "14px 14px 0 0",
    width: "100%", maxWidth: 420, padding: "8px 20px 32px",
  },
  grabber: {
    width: 36, height: 5, borderRadius: 3, background: "#3a3a3c",
    margin: "0 auto 12px",
  },
  header: {
    display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16,
  },
  cancelBtn: { background: "none", border: "none", color: "#8e8e93", fontSize: 16, cursor: "pointer" },
  doneBtn: (valid: boolean) => ({
    background: "none", border: "none", color: valid ? "#0a84ff" : "#3a3a3c",
    fontSize: 16, fontWeight: 600, cursor: valid ? "pointer" : "default",
  } as React.CSSProperties),
  title: { color: "#fff", fontSize: 16, fontWeight: 600 },
  label: { color: "#8e8e93", fontSize: 12, marginBottom: 6, marginTop: 12 },
  input: {
    width: "100%", padding: 10, borderRadius: 10, border: "1px solid #3a3a3c",
    background: "#2c2c2e", color: "#fff", fontSize: 14, fontFamily: "inherit",
    outline: "none", boxSizing: "border-box" as const,
  },
  textarea: {
    width: "100%", padding: 10, borderRadius: 10, border: "1px solid #3a3a3c",
    background: "#2c2c2e", color: "#fff", fontSize: 14, fontFamily: "inherit",
    outline: "none", boxSizing: "border-box" as const, resize: "vertical" as const, minHeight: 80,
  },
};

const EMOJIS = ["😀", "😎", "🤖", "🧠", "🎨", "🎵", "📚", "🌙", "⭐", "🌈", "🌸", "🔥", "💡", "🎯", "🧙‍♂️", "👩‍🦰", "👨‍🔬", "👩‍🎤", "🧑‍🍳", "🦊"];

export function CreatePersona({ onSave, onClose }: Props) {
  const [name, setName] = useState("");
  const [avatar, setAvatar] = useState("🤖");
  const [title, setTitle] = useState("");
  const [systemMessage, setSystemMessage] = useState("");

  const valid = name.trim().length > 0;

  const handleSave = () => {
    if (!valid) return;
    onSave({ name: name.trim(), avatar, title: title.trim(), system_message: systemMessage.trim() });
  };

  return (
    <div style={s.overlay} onClick={onClose}>
      <div style={s.sheet} onClick={(e) => e.stopPropagation()}>
        <div style={s.grabber} />
        <div style={s.header}>
          <button onClick={onClose} style={s.cancelBtn}>Cancel</button>
          <span style={s.title}>New Persona</span>
          <button onClick={handleSave} style={s.doneBtn(valid)}>Save</button>
        </div>

        <div style={s.label}>AVATAR</div>
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 8 }}>
          {EMOJIS.map((e) => (
            <button
              key={e}
              onClick={() => setAvatar(e)}
              style={{
                width: 36, height: 36, borderRadius: 18, border: avatar === e ? "2px solid #0a84ff" : "2px solid transparent",
                background: "#2c2c2e", cursor: "pointer", fontSize: 18,
                display: "flex", alignItems: "center", justifyContent: "center",
              }}
            >
              {e}
            </button>
          ))}
        </div>

        <div style={s.label}>NAME</div>
        <input style={s.input} value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Alex" />

        <div style={s.label}>TITLE</div>
        <input style={s.input} value={title} onChange={(e) => setTitle(e.target.value)} placeholder="e.g. Creative Writer" />

        <div style={s.label}>SYSTEM PROMPT</div>
        <textarea style={s.textarea} value={systemMessage} onChange={(e) => setSystemMessage(e.target.value)} rows={4} placeholder="Describe how this persona should behave..." />
      </div>
    </div>
  );
}

import { useState } from "react";

interface Props {
  systemMessage: string;
  onSave: (msg: string) => void;
}

const s = {
  trigger: {
    background: "none",
    border: "none",
    color: "#0a84ff",
    borderRadius: 6,
    padding: "4px 8px",
    cursor: "pointer",
    fontSize: 12,
    fontWeight: 500,
  } as React.CSSProperties,
  overlay: {
    position: "fixed" as const,
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: "rgba(0,0,0,0.5)",
    display: "flex",
    alignItems: "flex-end",
    justifyContent: "center",
    zIndex: 100,
  } as React.CSSProperties,
  sheet: {
    background: "#1c1c1e",
    borderRadius: "14px 14px 0 0",
    width: "100%",
    maxWidth: 420,
    padding: "8px 20px 32px",
  } as React.CSSProperties,
  grabber: {
    width: 36,
    height: 5,
    borderRadius: 3,
    background: "#3a3a3c",
    margin: "0 auto 12px",
  } as React.CSSProperties,
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 16,
  } as React.CSSProperties,
  doneBtn: {
    background: "none",
    border: "none",
    color: "#0a84ff",
    fontSize: 16,
    fontWeight: 600,
    cursor: "pointer",
  } as React.CSSProperties,
  cancelBtn: {
    background: "none",
    border: "none",
    color: "#8e8e93",
    fontSize: 16,
    cursor: "pointer",
  } as React.CSSProperties,
  title: {
    color: "#fff",
    fontSize: 16,
    fontWeight: 600,
  } as React.CSSProperties,
  textarea: {
    width: "100%",
    padding: 12,
    borderRadius: 10,
    border: "1px solid #3a3a3c",
    background: "#2c2c2e",
    color: "#fff",
    fontSize: 14,
    fontFamily: "inherit",
    resize: "vertical" as const,
    outline: "none",
    boxSizing: "border-box" as const,
    minHeight: 120,
  } as React.CSSProperties,
};

export function SystemMessageEditor({ systemMessage, onSave }: Props) {
  const [open, setOpen] = useState(false);
  const [value, setValue] = useState(systemMessage);

  const handleSave = () => {
    onSave(value);
    setOpen(false);
  };

  const handleOpen = () => {
    setValue(systemMessage);
    setOpen(true);
  };

  return (
    <>
      <button onClick={handleOpen} style={s.trigger}>
        Edit Prompt
      </button>
      {open && (
        <div style={s.overlay} onClick={() => setOpen(false)}>
          <div style={s.sheet} onClick={(e) => e.stopPropagation()}>
            <div style={s.grabber} />
            <div style={s.header}>
              <button onClick={() => setOpen(false)} style={s.cancelBtn}>Cancel</button>
              <span style={s.title}>System Prompt</span>
              <button onClick={handleSave} style={s.doneBtn}>Done</button>
            </div>
            <textarea
              value={value}
              onChange={(e) => setValue(e.target.value)}
              rows={6}
              style={s.textarea}
            />
          </div>
        </div>
      )}
    </>
  );
}

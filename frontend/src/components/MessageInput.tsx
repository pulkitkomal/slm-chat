import { useState, type FormEvent } from "react";

interface Props {
  onSend: (content: string) => void;
  disabled: boolean;
  isMobile: boolean;
}

export function MessageInput({ onSend, disabled, isMobile }: Props) {
  const [input, setInput] = useState("");

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!input.trim() || disabled) return;
    onSend(input.trim());
    setInput("");
  };

  const hasText = input.trim().length > 0;

  return (
    <form onSubmit={handleSubmit} style={{
      padding: isMobile ? "6px 12px calc(12px + var(--sab))" : "6px 12px 12px",
      display: "flex", gap: 6, alignItems: "flex-end",
    }}>
      <div style={{
        flex: 1, display: "flex", alignItems: "flex-end",
        background: "#1c1c1e", borderRadius: 18,
        padding: "3px 3px 3px 12px", border: "1px solid #2c2c2e",
      }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Message..."
          disabled={disabled}
          style={{
            flex: 1, padding: "7px 0", border: "none", background: "transparent",
            color: "#fff", outline: "none", fontSize: 15, fontFamily: "inherit",
            lineHeight: 1.4,
          }}
        />
        <button
          type="submit"
          disabled={disabled || !hasText}
          style={{
            width: 28, height: 28, borderRadius: 14, border: "none",
            background: hasText ? "#0a84ff" : "#2c2c2e", color: "#fff", fontSize: 12,
            cursor: hasText && !disabled ? "pointer" : "default",
            display: "flex", alignItems: "center", justifyContent: "center",
            flexShrink: 0, transition: "background 0.15s", opacity: disabled ? 0.5 : 1,
          }}
        >
          ↑
        </button>
      </div>
    </form>
  );
}

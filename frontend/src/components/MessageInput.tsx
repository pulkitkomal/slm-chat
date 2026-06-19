import { useState, type FormEvent } from "react";

interface Props {
  onSend: (content: string) => void;
  disabled: boolean;
}

export function MessageInput({ onSend, disabled }: Props) {
  const [input, setInput] = useState("");

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!input.trim() || disabled) return;
    onSend(input.trim());
    setInput("");
  };

  return (
    <form onSubmit={handleSubmit} style={{ padding: "12px", borderTop: "1px solid #333", display: "flex", gap: 8 }}>
      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Type a message..."
        disabled={disabled}
        style={{
          flex: 1,
          padding: "10px",
          borderRadius: 8,
          border: "1px solid #555",
          background: "#2d2d2d",
          color: "#eee",
          outline: "none",
        }}
      />
      <button
        type="submit"
        disabled={disabled || !input.trim()}
        style={{
          padding: "10px 20px",
          borderRadius: 8,
          border: "none",
          background: disabled ? "#444" : "#2b5278",
          color: "#fff",
          cursor: disabled ? "not-allowed" : "pointer",
        }}
      >
        Send
      </button>
    </form>
  );
}

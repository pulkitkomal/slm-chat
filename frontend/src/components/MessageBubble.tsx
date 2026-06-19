import type { Agent, Message } from "../api/client";

interface Props {
  message: Message;
  agent: Agent | null;
}

const s = {
  row: (isUser: boolean) =>
    ({
      display: "flex",
      justifyContent: isUser ? "flex-end" : "flex-start",
      marginBottom: 3,
      alignItems: "flex-end",
      gap: 6,
    } as React.CSSProperties),
  avatar: {
    width: 28,
    height: 28,
    borderRadius: 14,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: 13,
    background: "#1c1c1e",
    flexShrink: 0,
  } as React.CSSProperties,
  bubble: (isUser: boolean) =>
    ({
      maxWidth: "75%",
      padding: "9px 14px",
      borderRadius: 18,
      borderBottomRightRadius: isUser ? 4 : 18,
      borderBottomLeftRadius: isUser ? 18 : 4,
      background: isUser ? "#0a84ff" : "#1c1c1e",
      color: "#fff",
      whiteSpace: "pre-wrap" as const,
      wordBreak: "break-word" as const,
      fontSize: 15,
      lineHeight: 1.45,
    } as React.CSSProperties),
};

export function MessageBubble({ message, agent }: Props) {
  const isUser = message.role === "user";
  return (
    <div style={s.row(isUser)}>
      {!isUser && agent && <div style={s.avatar}>{agent.avatar}</div>}
      <div style={s.bubble(isUser)}>{message.content}</div>
    </div>
  );
}

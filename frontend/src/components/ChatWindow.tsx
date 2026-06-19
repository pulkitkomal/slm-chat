import type { Agent, Chat, Message } from "../api/client";
import { MessageBubble } from "./MessageBubble";
import { MessageInput } from "./MessageInput";
import { SystemMessageEditor } from "./SystemMessageEditor";

interface Props {
  chat: Chat;
  agent: Agent | null;
  messages: Message[];
  streamingContent: string;
  loading: boolean;
  error: string | null;
  isMobile: boolean;
  onBack: () => void;
  onSend: (content: string) => void;
  onUpdateChat: (id: string, data: Partial<Chat>) => void;
  onReset: (id: string) => void;
}

export function ChatWindow({ chat, agent, messages, streamingContent, loading, error, isMobile, onBack, onSend, onUpdateChat, onReset }: Props) {
  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", height: "100vh", background: "#000", minWidth: 0 }}>
      <div style={{
        padding: isMobile ? "52px 12px 8px" : "12px 12px 8px",
        display: "flex", alignItems: "center", gap: 8,
        borderBottom: "1px solid #1c1c1e",
      }}>
        {isMobile && (
          <button onClick={onBack} style={{
            background: "none", border: "none", color: "#0a84ff", fontSize: 24,
            cursor: "pointer", padding: "0 4px", lineHeight: 1,
          }}>
            ‹
          </button>
        )}
        {agent && (
          <div style={{
            width: 28, height: 28, borderRadius: 14, display: "flex", alignItems: "center",
            justifyContent: "center", fontSize: 14, background: "#1c1c1e", flexShrink: 0,
          }}>
            {agent.avatar}
          </div>
        )}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ color: "#fff", fontWeight: 600, fontSize: 15, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {chat.title}
          </div>
          {agent && <div style={{ color: "#8e8e93", fontSize: 11 }}>{agent.title}</div>}
        </div>
        <div style={{ display: "flex", gap: 4, flexShrink: 0 }}>
          <SystemMessageEditor
            systemMessage={chat.system_message}
            onSave={(msg) => onUpdateChat(chat.id, { system_message: msg })}
          />
          <button onClick={() => onReset(chat.id)} style={{
            background: "none", border: "none", color: "#8e8e93",
            cursor: "pointer", fontSize: 11, padding: "4px 6px", fontWeight: 500,
          }}>
            Reset
          </button>
        </div>
      </div>
      <div style={{ flex: 1, overflowY: "auto", padding: "8px 12px 4px", display: "flex", flexDirection: "column" }}>
        {messages.length === 0 && (
          <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", color: "#555", fontSize: 13 }}>
            Send a message to start chatting with {agent?.name || chat.title}
          </div>
        )}
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} agent={agent} />
        ))}
        {streamingContent && (
          <div style={{ display: "flex", alignItems: "flex-end", gap: 6, marginBottom: 4 }}>
            {agent && (
              <div style={{ width: 26, height: 26, borderRadius: 13, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 12, background: "#1c1c1e", flexShrink: 0 }}>
                {agent.avatar}
              </div>
            )}
            <div style={{
              maxWidth: "75%", padding: "9px 14px", borderRadius: 18, borderBottomLeftRadius: 4,
              background: "#1c1c1e", color: "#ebebf5", whiteSpace: "pre-wrap", fontSize: 15, lineHeight: 1.45,
            }}>
              {streamingContent}
              <span style={{ display: "inline-block", width: 6, height: 14, background: "#0a84ff", marginLeft: 1, animation: "blink 1s step-end infinite" }} />
            </div>
          </div>
        )}
      </div>
      {error && (
        <div style={{ padding: "6px 12px", background: "#3a1010", color: "#ff6961", fontSize: 12, textAlign: "center", borderTop: "1px solid #5c1a1a" }}>
          {error}
        </div>
      )}
      <MessageInput onSend={onSend} disabled={loading} isMobile={isMobile} />
    </div>
  );
}
